"""Regression checks against Release output, including GitHub Pages 404 routing."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import unittest

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
PUBLISH = ROOT / 'artifacts/publish/wwwroot'
CATALOG = [
    {'id': 'alpha', 'name': 'Alpha', 'url': 'https://example.com/alpha',
     'summary': 'First benefit', 'tags': ['travel'], 'categories': ['education']},
    {'id': 'beta', 'name': 'Beta', 'url': 'https://example.com/beta',
     'summary': 'Second benefit', 'tags': ['fitness'], 'categories': ['education']},
    {'id': 'gamma', 'name': 'Gamma', 'url': 'https://example.com/gamma',
     'summary': 'Third benefit', 'tags': ['travel'], 'categories': ['discounts']},
]


class PagesHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            data = (PUBLISH / '404.html').read_bytes()
            self.send_response(404)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            super().send_error(code, message, explain)


class HomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (PUBLISH / '404.html').is_file():
            raise RuntimeError('Publish the app to artifacts/publish before running browser tests.')
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(PagesHandler, directory=str(PUBLISH)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            executable_path=os.environ.get('CHROME_EXECUTABLE_PATH'))

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.page = self.browser.new_page()
        self.page.set_default_timeout(20000)
        self.errors = []
        self.console_errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('console', lambda message:
                     self.console_errors.append(message.text) if message.type == 'error' else None)

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors, [])

    def mock_catalog(self, catalog=CATALOG):
        self.page.route('**/data/benefits.json', lambda route: route.fulfill(json=catalog))

    def test_category_search_combines_with_tags_and_can_be_cleared(self):
        self.mock_catalog()
        self.page.goto(self.base)
        items = self.page.locator('.benefit-item')
        expect(items).to_have_count(3)
        search = self.page.get_by_role('searchbox', name='Search benefits')
        search.fill(' EDUCATION ')
        expect(items).to_have_count(2)
        travel = self.page.get_by_role('button', name='travel', exact=True)
        travel.click()
        expect(travel).to_have_attribute('aria-pressed', 'true')
        expect(items).to_have_count(1)
        expect(items.first).to_contain_text('Alpha')
        search.fill('no-match')
        expect(self.page.get_by_text('No benefits found for the selected filter.')).to_be_visible()
        search.fill('')
        expect(items).to_have_count(2)
        self.page.get_by_role('button', name='All', exact=True).click()
        expect(items).to_have_count(3)
        expect(travel).to_have_attribute('aria-pressed', 'false')

    def test_http_failure_can_be_retried(self):
        attempts = []
        def respond(route):
            attempts.append(1)
            if len(attempts) == 1:
                route.fulfill(status=503, body='Unavailable')
            else:
                route.fulfill(json=CATALOG)
        self.page.route('**/data/benefits.json', respond)
        self.page.goto(self.base)
        expect(self.page.get_by_role('alert')).to_contain_text("couldn't load")
        self.page.get_by_role('button', name='Try again').click()
        expect(self.page.locator('.benefit-item')).to_have_count(3)
        expect(self.page.get_by_role('alert')).to_have_count(0)
        self.assertEqual(len(attempts), 2)

    def test_invalid_catalogs_show_actionable_error(self):
        # Build the handler in a factory rather than binding `body` as a default
        # argument: Playwright passes the Request as a second positional argument
        # whenever the handler declares two parameters, which would overwrite the
        # payload and leave the route unfulfilled.
        def serve(body):
            return lambda route: route.fulfill(content_type='application/json', body=body)

        for payload in ['not json', 'null', '[null]', '[{"tags":null}]']:
            with self.subTest(payload=payload):
                self.page.route('**/data/benefits.json', serve(payload))
                self.page.goto(self.base)
                expect(self.page.get_by_role('button', name='Try again')).to_be_visible()
                self.page.unroute('**/data/benefits.json')

    def test_direct_about_route_and_refresh_use_pages_fallback(self):
        response = self.page.goto(self.base + '/about')
        self.assertEqual(response.status, 404)
        expect(self.page.get_by_role('heading', name='About SoldierSave.com')).to_be_visible()
        self.page.reload()
        expect(self.page.get_by_role('heading', name='About SoldierSave.com')).to_be_visible()
        self.page.get_by_role('link', name='Home', exact=True).click()
        expect(self.page.locator('.benefit-item')).to_have_count(len(json.loads((ROOT / 'data/benefits.json').read_text(encoding='utf-8'))))

    def test_mobile_layout_and_loading_circle_styles(self):
        self.mock_catalog()
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.page.goto(self.base)
        expect(self.page.locator('.benefit-item')).to_have_count(3)
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))
        styles = self.page.evaluate('''() => {
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.classList.add('loading-progress');
            const circle = document.createElementNS(svg.namespaceURI, 'circle');
            svg.append(circle); document.body.append(svg);
            const style = getComputedStyle(circle);
            const result = {width: style.strokeWidth, transform: style.transform};
            svg.remove(); return result;
        }''')
        self.assertEqual(styles['width'], '9.6px')
        self.assertNotEqual(styles['transform'], 'none')

    def test_content_security_policy_does_not_block_the_app(self):
        """The CSP is delivered as a meta tag because Pages cannot send headers.
        A policy that is too strict breaks the WebAssembly runtime silently, so
        assert the app still boots and the browser reported no violations."""
        self.mock_catalog()
        self.page.goto(self.base)
        expect(self.page.locator('.benefit-item')).to_have_count(3)
        violations = [text for text in self.console_errors
                      if 'Content Security Policy' in text or 'violates' in text]
        self.assertEqual(violations, [])
        policy = self.page.get_attribute('meta[http-equiv="Content-Security-Policy"]', 'content')
        self.assertIn("script-src 'self' 'wasm-unsafe-eval'", ' '.join(policy.split()))

    def test_unsafe_benefit_url_never_becomes_a_live_link(self):
        """CI rejects non-HTTP(S) URLs, but a record edited by hand and merged
        directly would bypass it. The renderer must refuse the href regardless."""
        self.mock_catalog([
            {'id': 'evil', 'name': 'Evil', 'url': 'javascript:alert(1)',
             'summary': 'Unsafe', 'tags': [], 'categories': []},
            {'id': 'good', 'name': 'Good', 'url': 'https://example.com/good',
             'summary': 'Safe', 'tags': [], 'categories': []},
        ])
        self.page.goto(self.base)
        expect(self.page.locator('.benefit-item')).to_have_count(2)
        expect(self.page.get_by_text('Evil', exact=True)).to_be_visible()
        self.assertEqual(self.page.locator('.benefit-item a[href^="javascript:"]').count(), 0)
        expect(self.page.locator('.benefit-item a[href="https://example.com/good"]')).to_have_count(1)


if __name__ == '__main__':
    unittest.main()
