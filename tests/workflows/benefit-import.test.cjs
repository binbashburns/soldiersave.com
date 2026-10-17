const { test } = require('node:test');
const assert = require('node:assert/strict');
const { importBenefit } = require('../../.github/scripts/benefit-import.cjs');

function issue(overrides = {}) {
  const fields = {
    'Benefit name': 'Example Benefit',
    'Primary URL': 'https://example.com/',
    'Additional URLs (optional)': '_No response_',
    'Category (pick one that fits best)': 'education, travel',
    'Short description': 'First paragraph.\n\nSecond paragraph.',
    Tags: '_No response_',
    'Who is eligible? (check all that apply)': '- [ ] Active-duty\n- [x] Veteran\n- [X] Guard/Reserve',
    ...overrides,
  };
  return {
    number: 42, user: { login: 'contributor' }, created_at: '2026-01-01T00:00:00Z',
    body: Object.entries(fields).map(([heading, value]) => `### ${heading}\n\n${value}`).join('\n\n'),
  };
}

test('preserves multiline content and imports only checked eligibility', () => {
  const record = importBenefit([], issue({
    'Additional URLs (optional)': 'https://example.com/one\nhttps://example.com/two\nhttps://example.com/',
  }));
  assert.deepEqual(record.urls, ['https://example.com/', 'https://example.com/one', 'https://example.com/two']);
  assert.equal(record.summary, 'First paragraph.\n\nSecond paragraph.');
  assert.deepEqual(record.eligibility, ['veteran', 'guard-reserve']);
  assert.deepEqual(record.categories, ['education', 'travel']);
  assert.deepEqual(record.tags, ['education', 'travel']);
  assert.equal(record.addedBy, '@contributor');
});

test('omits optional placeholders and supports CRLF', () => {
  const input = issue();
  input.body = input.body.replaceAll('\n', '\r\n');
  const record = importBenefit([], input);
  assert.deepEqual(record.urls, ['https://example.com/']);
  assert.ok(!JSON.stringify(record).includes('_No response_'));
});

test('normalizes tags and preserves all categories without duplicate tags', () => {
  const record = importBenefit([], issue({ Tags: 'Travel, Military Families, travel' }));
  assert.deepEqual(record.tags, ['travel', 'military-families', 'education']);
});

test('rejects missing required fields and unsafe or malformed URLs', () => {
  for (const heading of ['Benefit name', 'Primary URL', 'Short description', 'Category (pick one that fits best)']) {
    assert.throws(() => importBenefit([], issue({ [heading]: '_No response_' })), /required/);
  }
  for (const value of ['javascript:alert(1)', '/relative', 'https://user:pass@example.com', 'https://example.com/bad path']) {
    assert.throws(() => importBenefit([], issue({ 'Primary URL': value })), /HTTP\(S\)/);
    assert.throws(() => importBenefit([], issue({ 'Additional URLs (optional)': value })), /HTTP\(S\)/);
  }
});

test('retries are stable and a merged issue cannot produce another entry', () => {
  const input = issue();
  const record = importBenefit([], input);
  assert.deepEqual(importBenefit([], input), record);
  assert.equal(importBenefit([record], input), null);
  const other = { ...input, number: 43 };
  assert.equal(importBenefit([record], other).id, 'example-benefit-2');
});

test('rejects duplicate form headings instead of silently replacing a required field', () => {
  const input = issue();
  input.body += '\n\n### Primary URL\n\nhttps://other.example.com';
  assert.throws(() => importBenefit([], input), /Duplicate form section/);
});
