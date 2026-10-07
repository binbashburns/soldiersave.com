const fs = require('node:fs');

function sections(body) {
  const result = new Map();
  let heading;
  for (const line of body.replace(/\r\n/g, '\n').split('\n')) {
    const match = line.match(/^### (.+?)\s*$/);
    if (match) {
      heading = match[1];
      if (result.has(heading)) throw new Error(`Duplicate form section: ${heading}`);
      result.set(heading, []);
    } else if (heading) {
      result.get(heading).push(line);
    }
  }
  return new Map([...result].map(([key, lines]) => {
    const value = lines.join('\n').trim();
    return [key, value === '_No response_' ? '' : value];
  }));
}

function slugify(value) {
  return value.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

function httpUrl(value) {
  let parsed;
  try { parsed = new URL(value); } catch { throw new Error('URLs must be absolute HTTP(S) URLs.'); }
  if (!/^https?:\/\//i.test(value) || !['http:', 'https:'].includes(parsed.protocol) ||
      parsed.username || parsed.password || /\s/.test(value)) {
    throw new Error('URLs must be absolute HTTP(S) URLs without credentials or whitespace.');
  }
  return value;
}

function importBenefit(benefits, issue) {
  const reference = `issue-${issue.number}`;
  if (benefits.some(benefit => benefit.source?.reference === reference)) {
    return null; // A merged contribution must not be imported again on relabel/retry.
  }
  const form = sections(issue.body || '');
  const required = label => {
    const value = form.get(label);
    if (!value) throw new Error(`${label} is required.`);
    return value;
  };
  const slugs = value => [...new Set(value.split(',').map(slugify).filter(Boolean))];
  const name = required('Benefit name');
  const url = httpUrl(required('Primary URL'));
  const summary = required('Short description');
  const categories = slugs(required('Category (pick one that fits best)'));
  if (!categories.length) throw new Error('At least one category is required.');
  const extraUrls = (form.get('Additional URLs (optional)') || '').split('\n')
    .map(line => line.trim()).filter(Boolean).map(httpUrl);
  const eligibility = [...new Set((form.get('Who is eligible? (check all that apply)') || '')
    .split('\n').flatMap(line => {
      const match = line.match(/^\s*[-*]\s+\[x\]\s+(.+)$/i);
      return match ? [slugify(match[1])] : [];
    }).filter(Boolean))];
  const base = slugify(name) || 'benefit';
  const usedIds = new Set(benefits.map(benefit => benefit.id));
  let id = base;
  for (let suffix = 2; usedIds.has(id); suffix++) id = `${base}-${suffix}`;
  return {
    id, name, url, urls: [...new Set([url, ...extraUrls])], summary, categories,
    tags: [...new Set([...slugs(form.get('Tags') || ''), ...categories])],
    eligibility, source: { type: 'community', reference },
    addedBy: `@${issue.user.login}`,
    addedAt: issue.created_at,
  };
}

const REJECTION_MARKER = '<!-- soldiersave-benefit-import -->';

// A failed workflow step is invisible to the person who filed the issue, so tell
// them on the issue itself what to fix. The `edited` trigger re-runs the import,
// so a correction is picked up without any maintainer action.
async function reportRejection({ github, context }, issue, message) {
  const body = `${REJECTION_MARKER}\n\nThanks for the submission. This could not be added to the ` +
    `catalog automatically:\n\n> ${message}\n\nEdit the issue to correct it and the import will run again.`;
  const comments = await github.paginate(github.rest.issues.listComments, {
    ...context.repo, issue_number: issue.number, per_page: 100,
  });
  const prior = comments.filter(comment => comment.body?.startsWith(REJECTION_MARKER)).pop();
  if (prior?.body === body) return; // Don't repeat the same complaint on every edit.
  if (prior) {
    await github.rest.issues.updateComment({ ...context.repo, comment_id: prior.id, body });
  } else {
    await github.rest.issues.createComment({ ...context.repo, issue_number: issue.number, body });
  }
}

async function applyIssue({ github, context, core }) {
  const { data: issue } = await github.rest.issues.get({
    ...context.repo, issue_number: context.payload.issue.number,
  });
  core.setOutput('benefit-id', '');
  if (issue.state !== 'open' || !issue.labels.some(label =>
    (typeof label === 'string' ? label : label.name) === 'type:new-benefit')) return;
  const file = 'data/benefits.json';
  const benefits = JSON.parse(fs.readFileSync(file, 'utf8'));
  let benefit;
  try {
    benefit = importBenefit(benefits, issue);
  } catch (error) {
    await reportRejection({ github, context }, issue, error.message);
    core.setFailed(error.message);
    return;
  }
  if (!benefit) {
    core.info('This issue already has a catalog entry. No change needed.');
    return;
  }
  fs.writeFileSync(file, `${JSON.stringify([...benefits, benefit], null, 2)}\n`);
  core.setOutput('benefit-id', benefit.id);
}

module.exports = { importBenefit, applyIssue };
