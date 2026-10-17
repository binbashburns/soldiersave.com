"""Check catalog URLs; write reports without changing the catalog or GitHub."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import html
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urlsplit
from urllib.request import Request, urlopen


def collect_urls(benefits):
    urls = {}
    for benefit in benefits:
        for url in [benefit['url'], *benefit.get('urls', [])]:
            url = urldefrag(url)[0]
            urls.setdefault(url, set()).add(benefit['name'])
    return {url: sorted(names) for url, names in sorted(urls.items())}


def request_status(url, method, timeout):
    # Identify ourselves honestly, but send the Accept headers a browser would:
    # some providers reject header-less requests outright and show up as 403s
    # that have nothing to do with the link being dead.
    request = Request(url, method=method, headers={
        'User-Agent': 'SoldierSave-LinkCheck/1.0 (+https://github.com/binbashburns/soldiersave.com)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.url, ''
    except HTTPError as error:
        with error:
            return error.code, error.url, ''
    except (URLError, TimeoutError, OSError, ValueError) as error:
        return 0, url, str(error)


def check_url(url, timeout=15, request=request_status):
    if urlsplit(url).scheme not in ('http', 'https'):
        return {'url': url, 'status': 0, 'final_url': url,
                'kind': 'error', 'error': 'Not an HTTP(S) URL'}
    status, final_url, error = request(url, 'HEAD', timeout)
    # Many providers reject HEAD even when their normal pages work.
    if not 200 <= status < 400:
        status, final_url, error = request(url, 'GET', timeout)
    if 200 <= status < 400:
        kind = 'ok'
    elif status in (0, 401, 403, 429):
        kind = 'unverified'
    else:
        kind = 'error'
    return {'url': url, 'status': status, 'final_url': final_url, 'kind': kind, 'error': error}


def cell(value):
    return html.escape(str(value)).replace('|', '&#124;').replace('\n', ' ').replace('\r', ' ')


def render_report(results):
    counts = {kind: sum(result['kind'] == kind for result in results)
              for kind in ('ok', 'error', 'unverified')}
    lines = ['# Benefit link check', '',
             f"Checked {len(results)} unique URLs: {counts['ok']} successful, "
             f"{counts['error']} HTTP errors, {counts['unverified']} unverified.", '',
             'Unverified requests were blocked, rate-limited, or failed to connect. '
             'They do not establish that a benefit is unavailable.', '']
    for kind, title in [('error', 'HTTP errors'), ('unverified', 'Needs manual verification')]:
        rows = [result for result in results if result['kind'] == kind]
        if not rows:
            continue
        lines.extend([f'## {title}', '', '| URL | Status | Benefits | Detail |',
                      '| --- | --- | --- | --- |'])
        for result in rows:
            lines.append('| ' + ' | '.join(map(cell, [result['url'], result['status'] or 'network error',
                         ', '.join(result['benefits']), result['error']])) + ' |')
        lines.append('')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=Path('data/benefits.json'))
    parser.add_argument('--output', type=Path, default=Path('artifacts/link-check'))
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--timeout', type=float, default=15)
    args = parser.parse_args()
    if args.workers < 1 or args.timeout <= 0:
        parser.error('workers and timeout must be positive')
    urls = collect_urls(json.loads(args.catalog.read_text(encoding='utf-8')))
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda url: check_url(url, args.timeout), urls))
    for result in results:
        result['benefits'] = urls[result['url']]
    args.output.mkdir(parents=True, exist_ok=True)
    report = render_report(results)
    (args.output / 'report.md').write_text(report, encoding='utf-8')
    (args.output / 'results.json').write_text(json.dumps({
        'checkedAt': datetime.now(timezone.utc).isoformat(), 'results': results,
    }, indent=2) + '\n', encoding='utf-8')
    print(report.splitlines()[2])
    # Reports contain findings; external provider failures must not block unrelated PRs.
    # Exceptions and malformed input still fail the command and workflow.


if __name__ == '__main__':
    main()
