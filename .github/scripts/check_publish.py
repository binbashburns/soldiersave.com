"""Check local asset references against published output, not unbuilt source."""

from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        key = {'link': 'href', 'script': 'src', 'img': 'src'}.get(tag)
        if key and attrs.get(key):
            self.assets.append(attrs[key])


def check_publish(root, catalog):
    errors = []
    for name in ('index.html', '404.html'):
        page = root / name
        if not page.is_file():
            errors.append(f'Missing published page: {name}')
            continue
        parser = AssetParser()
        parser.feed(page.read_text(encoding='utf-8'))
        for asset in parser.assets:
            url = urlsplit(asset)
            if url.scheme or url.netloc:
                continue
            path = root / unquote(url.path).lstrip('/')
            if not path.is_file():
                errors.append(f'{name}: missing asset {asset}')
    data = root / 'data/benefits.json'
    if not data.is_file():
        errors.append('Missing published catalog')
    elif json.loads(data.read_text(encoding='utf-8')) != json.loads(catalog.read_text(encoding='utf-8')):
        errors.append('Published catalog differs from canonical data')
    return errors


if __name__ == '__main__':
    errors = check_publish(Path(sys.argv[1]), Path('data/benefits.json'))
    if errors:
        raise SystemExit('\n'.join(errors))
    print('Published pages, asset references, and catalog verified.')
