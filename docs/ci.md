# CI and security pipelines

Four workflows run in this repository. Three are ours; security scanning is delegated to reusable
workflows in [binbashburns/security-pipelines](https://github.com/binbashburns/security-pipelines).

## `validate.yml` — correctness gate

Runs on every pull request and push to `main`. Installs .NET, Node, and Python, then runs, in order:

1. `node --test tests/workflows/*.test.cjs` — the issue-form importer.
2. `python -m unittest discover -s tests/maintenance` — catalog, link, and publish check scripts.
3. `validate_catalog.py` — schema and cross-record validation of `data/benefits.json`.
4. `dotnet publish` to `artifacts/publish`, then `check_publish.py` against the published output.
5. Playwright browser tests against that published output, including GitHub Pages 404 routing and
   Content-Security-Policy enforcement.

## `pages.yml` — build and deploy

Runs on push to `main`. Validates the catalog **before** publishing, so a schema failure cannot
reach production, then publishes, verifies the output, and deploys to GitHub Pages.

## `new-benefit-from-issue.yml` — contribution automation

Triggered when an issue is opened, labelled, or edited. If the issue carries `type:new-benefit`, it
parses the issue form, appends an entry to `data/benefits.json`, validates the result, and opens a
pull request. Re-running is safe: an issue that already has a catalog entry (matched on
`source.reference`) is skipped. A submission that fails validation gets a comment on the issue
explaining what to fix, and the `edited` trigger re-runs the import once it is corrected.

## `security.yml` — security scanning

| Job | Tool | Covers |
| --- | --- | --- |
| `secrets` | TruffleHog | Committed credentials. Gates every other job. |
| `sast` | Semgrep | Static analysis of C#, JavaScript, and Python. Pull requests only. |
| `sbom` | Syft + Grype | Dependency vulnerabilities, from `packages.lock.json`. |
| `link-check` | lychee | Dead links in the prose documentation. |
| `dast` | OWASP ZAP baseline | Passive scan of the deployed site. |
| `benefit-links` | `check_benefit_links.py` | The 200+ external URLs in the catalog. |

### Why DAST scans the deployed site

Reusable workflows check out the *caller's* repository and have no .NET build step, so they cannot
produce the published Blazor output. Rather than let ZAP serve and scan this repo's source tree —
which is what the defaults do, and which scans nothing meaningful — the job sets `serve-port: 0`
and points at <https://soldiersave.com/>.

`security-site-artifact.yml.example` is the better arrangement: build once, then hand the published
artifact to both ZAP and lychee, so a regression is caught on the pull request rather than after
deployment. It is staged rather than active because it depends on `site-artifact` and `site-path`
inputs that `security-pipelines` has not published yet.

### Link checking is split in two

`link-check` (lychee) covers the Markdown documentation. `benefit-links` covers the catalog and
maintains its own tracking issue under the `benefit-link-check` label — deliberately a different
label from lychee's `link-check`, so the two reporters can never edit each other's issue.

The catalog checker classifies results as `ok`, `error`, or `unverified`. **Unverified is not
broken**: many retailers and `.mil` sites reject requests from CI runners with a 403 or drop the
connection. Only `error` rows are worth acting on without a manual visit. Findings never fail the
job — an external site being down is not a reason to block an unrelated change.
