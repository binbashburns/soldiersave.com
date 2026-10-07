const fs = require('node:fs');

// This reporter owns its own label and marker. It must never adopt an issue
// opened by the central security-pipelines lychee job, which also uses the
// `link-check` label -- two reporters editing one issue would clobber each other.
const LABEL = 'benefit-link-check';
const MARKER = '<!-- soldiersave-benefit-link-check -->';

module.exports = async ({ github, context, core }) => {
  const report = fs.readFileSync('artifacts/link-check/report.md', 'utf8');
  const { results } = JSON.parse(fs.readFileSync('artifacts/link-check/results.json', 'utf8'));
  const issues = await github.paginate(github.rest.issues.listForRepo, {
    ...context.repo, state: 'open', labels: LABEL, per_page: 100,
  });
  const existing = issues.find(issue => !issue.pull_request && issue.body?.includes(MARKER));
  const hasFindings = results.some(result => result.kind !== 'ok');
  if (!existing && !hasFindings) {
    core.info('All catalog links responded successfully. No issue needed.');
    return;
  }
  const runUrl = `${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`;
  const body = `${MARKER}\n\n[Latest workflow report](${runUrl})\n\n${report}`;
  if (!existing) {
    await github.rest.issues.create({
      ...context.repo, title: 'Benefit link check failures', body,
      labels: ['type:bug', 'area:data', LABEL],
    });
    return;
  }
  await github.rest.issues.update({ ...context.repo, issue_number: existing.number, body });
  if (!hasFindings) {
    // Close the tracker rather than leaving a green report open forever.
    await github.rest.issues.update({ ...context.repo, issue_number: existing.number, state: 'closed' });
    core.info(`All catalog links responded successfully. Closed #${existing.number}.`);
  }
};
