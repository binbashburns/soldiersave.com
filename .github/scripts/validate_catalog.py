"""Validate the catalog's item schema and cross-record invariants."""

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]


def validate_catalog(benefits, schema):
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    if not isinstance(benefits, list):
        return ["Catalog must be a JSON array."]
    errors = []
    ids = set()
    for index, benefit in enumerate(benefits):
        prefix = f"Entry {index + 1}"
        item_errors = list(validator.iter_errors(benefit))
        errors.extend(f"{prefix}: {error.json_path}: {error.message}" for error in item_errors)
        if item_errors:
            continue
        identity = benefit['id']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', identity):
            errors.append(f"{prefix}: ID must be a lowercase hyphenated slug.")
        if identity in ids:
            errors.append(f"{prefix}: duplicate ID {identity}.")
        ids.add(identity)
        for field in ('name', 'summary', 'addedBy'):
            if not benefit[field].strip() or benefit[field].strip() == '_No response_':
                errors.append(f"{identity}: {field} must not be blank or a placeholder.")
        for field in ('tags', 'categories', 'eligibility'):
            for value in benefit.get(field, []):
                if not value.strip() or value.strip() == '_No response_':
                    errors.append(f"{identity}: {field} contains a blank or placeholder.")
        for url in [benefit['url'], *benefit.get('urls', [])]:
            try:
                parsed = urlsplit(url)
                valid = (parsed.scheme in ('http', 'https') and parsed.hostname
                         and not parsed.username and not parsed.password
                         and not re.search(r'\s', url))
            except ValueError:
                valid = False
            if not valid:
                errors.append(f"{identity}: expected an HTTP(S) URL without credentials: {url}")
    return errors


if __name__ == '__main__':
    catalog = json.loads((ROOT / 'data/benefits.json').read_text(encoding='utf-8'))
    schema = json.loads((ROOT / 'data/benefits.schema.json').read_text(encoding='utf-8'))
    errors = validate_catalog(catalog, schema)
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Validated {len(catalog)} benefits.')
