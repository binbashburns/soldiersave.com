import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.github/scripts'))
from check_benefit_links import check_url, collect_urls, render_report
from check_publish import check_publish
from validate_catalog import validate_catalog


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads((ROOT / 'data/benefits.schema.json').read_text())
        self.benefit = {
            'id': 'example', 'name': 'Example', 'url': 'https://example.com',
            'summary': 'An example benefit', 'categories': [], 'tags': [], 'addedBy': '@example',
        }

    def test_valid_record(self):
        self.assertEqual(validate_catalog([self.benefit], self.schema), [])

    def test_rejects_invalid_root_and_duplicate_ids(self):
        self.assertTrue(validate_catalog({}, self.schema))
        self.assertIn('duplicate ID', '\n'.join(validate_catalog([self.benefit] * 2, self.schema)))

    def test_rejects_nulls_placeholders_unknown_fields_and_unsafe_urls(self):
        for changes in [{'tags': None}, {'tags': [None]}, {'tags': ['_No response_']},
                        {'url': 'javascript:alert(1)'}, {'url': 'https://user:pass@example.com'},
                        {'summary': ''}, {'addedAt': 'not-a-date'}, {'extra': 'unexpected'}]:
            with self.subTest(changes=changes):
                record = {**copy.deepcopy(self.benefit), **changes}
                self.assertTrue(validate_catalog([record], self.schema))


class LinkTests(unittest.TestCase):
    def test_collects_every_url_once_with_all_benefit_names(self):
        self.assertEqual(collect_urls([
            {'name': 'One', 'url': 'https://example.com',
             'urls': ['https://example.com#section', 'https://example.com/extra']},
            {'name': 'Two', 'url': 'https://example.com'},
        ]), {'https://example.com': ['One', 'Two'], 'https://example.com/extra': ['One']})

    def test_head_rejection_falls_back_to_get(self):
        methods = []
        def request(url, method, timeout):
            methods.append(method)
            return (405 if method == 'HEAD' else 200), url, ''
        self.assertEqual(check_url('https://example.com', request=request)['kind'], 'ok')
        self.assertEqual(methods, ['HEAD', 'GET'])

    def test_classifies_blocked_and_network_results_separately_from_http_errors(self):
        for status, kind in [(200, 'ok'), (204, 'ok'), (403, 'unverified'),
                             (429, 'unverified'), (0, 'unverified'), (404, 'error'), (500, 'error')]:
            with self.subTest(status=status):
                result = check_url('https://example.com', request=lambda url, method, timeout: (status, url, ''))
                self.assertEqual(result['kind'], kind)

    def test_report_escapes_catalog_text_and_separates_findings(self):
        result = {'url': 'https://example.com/a|b', 'status': 403, 'kind': 'unverified',
                  'error': 'network\nmessage', 'benefits': ['<script>alert(1)</script>']}
        report = render_report([result])
        self.assertIn('Needs manual verification', report)
        self.assertIn('a&#124;b', report)
        self.assertNotIn('<script>', report)
        self.assertNotIn('network\nmessage', report)


class PublishTests(unittest.TestCase):
    def test_checks_generated_assets_after_publish_and_detects_missing_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'data').mkdir()
            (root / 'data/benefits.json').write_text('[]')
            catalog = root / 'catalog.json'
            catalog.write_text('[]')
            page = '<base href="/"><link href="/app.styles.css"><script src="app.js"></script>'
            for name in ['index.html', '404.html']:
                (root / name).write_text(page)
            (root / 'app.styles.css').write_text('')
            (root / 'app.js').write_text('')
            self.assertEqual(check_publish(root, catalog), [])
            (root / 'app.styles.css').unlink()
            self.assertIn('missing asset /app.styles.css', '\n'.join(check_publish(root, catalog)))
            catalog.write_text('[{}]')
            self.assertIn('Published catalog differs', '\n'.join(check_publish(root, catalog)))


if __name__ == '__main__':
    unittest.main()
