# CLAUDE.md

Guidance for AI coding agents working in this repository.

## What this is

SoldierSave is a **Blazor WebAssembly** static site that renders a searchable catalog of US
military benefits, discounts, and resources. It is deployed to GitHub Pages at
<https://soldiersave.com>. There is no backend, no database, and no authentication — the entire
application is static files plus one JSON document.

Contributions arrive as GitHub issues; a workflow parses the issue form and opens a pull request.

## Layout

| Path | Purpose |
| --- | --- |
| `data/benefits.json` | **Canonical catalog.** A flat JSON array of benefit objects. |
| `data/benefits.schema.json` | JSON Schema (draft 2020-12) for **one entry**, not the array. |
| `src/SoldierSave.Web/` | The only project. `net9.0`, `Microsoft.NET.Sdk.BlazorWebAssembly`. |
| `.github/scripts/` | Maintenance tooling: catalog validation, link checking, issue import. |
| `.github/workflows/` | Deploy, validation, security, and issue-to-PR automation. |
| `tests/` | Three suites: `workflows/` (node), `maintenance/` (unittest), `browser/` (Playwright). |
| `docs/ci.md` | What each workflow does and why. |

There is no `global.json`, `Directory.Build.props`, or `nuget.config`; the SDK version is pinned
only in CI via `actions/setup-dotnet`. `Microsoft.NET.ILLink.Tasks` is referenced explicitly in the csproj
so the lockfile does not depend on the SDK patch level (see the comment there). Bootstrap 5.3.8 is vendored under `wwwroot/lib/` as the
minified CSS (plus source map) only; the site loads no Bootstrap JavaScript, so the rest of the
dist is deliberately not checked in.

## Rules that are easy to get wrong

**Never edit `src/SoldierSave.Web/wwwroot/data/benefits.json`.** It is a generated copy, produced by
the `CopyBenefitsJsonToWwwroot` MSBuild target and gitignored. Edit `data/benefits.json`.

**The issue form and the importer are a contract.** The `### <heading>` strings in
`.github/ISSUE_TEMPLATE/new-benefit.yml` must stay byte-identical to the labels parsed in
`.github/scripts/benefit-import.cjs` and asserted in `tests/workflows/benefit-import.test.cjs`.
Renaming a form field silently breaks contributions unless all three change together.

**`packages.lock.json` is committed on purpose.** CI restores with `--locked-mode`. After changing a
`PackageReference`, regenerate it with a restore using the force-evaluate flag and commit the result,
or CI will fail.

**No inline `style` attributes in components.** `wwwroot/index.html` ships a Content-Security-Policy
meta tag with `style-src 'self'`, so an inline style is blocked and silently unstyled. Use a CSS
class (see the `.tag-color-*` rules in `wwwroot/css/app.css`). `tests/browser/test_home.py` asserts
there are no CSP violations, so a regression fails the build.

**`<base href="/">` assumes the apex custom domain.** The site will not work when served from a
`user.github.io/repo` style path without changing it.

**`404.html` is what makes deep links work.** GitHub Pages serves it for any unknown path; because
it is a copy of `index.html` (made by the `CreatePagesFallback` target), Blazor boots and the router
resolves the route client-side.

## Catalog conventions

Each entry is a flat object. Required: `id`, `name`, `url`, `summary`, `categories`, `tags`,
`addedBy`. Optional: `urls`, `eligibility`, `source` (`{type, reference}`), `addedAt`.
`additionalProperties` is `false` — an unrecognised key fails validation.

- `id` is a unique lowercase hyphenated slug, matching `[a-z0-9]+(?:-[a-z0-9]+)*`.
- `url` and every entry in `urls` must be an absolute `http(s)` URL with no credentials.
- `addedBy` is a `@github-handle` for community submissions.
- `source.type` is one of `adoc`, `pdf`, or `community`; community entries use
  `reference: "issue-<number>"`, which is also the idempotency key that stops an issue being
  imported twice.

The tag vocabulary grew from two separate bulk imports and contains near-duplicates
(`travel` / `traveling` / `travel-recreation`, `financial-stuff` / `legal-financial`). Consolidating
it is a known open item; do not do it as a side effect of an unrelated change.

## Commands

```bash
# Run locally (from the repo root)
dotnet restore
dotnet run --project src/SoldierSave.Web/SoldierSave.Web.csproj

# Validate the catalog (needs `pip install -r .github/scripts/requirements.txt`)
python .github/scripts/validate_catalog.py

# Issue-importer unit tests
node --test tests/workflows/*.test.cjs

# Maintenance script tests
python -m unittest discover -s tests/maintenance -v

# Browser tests -- these REQUIRE a publish first, to this exact path
dotnet publish src/SoldierSave.Web/SoldierSave.Web.csproj -c Release -o artifacts/publish
python .github/scripts/check_publish.py artifacts/publish/wwwroot
python -m playwright install chromium
python -m unittest discover -s tests/browser -v

# Check every catalog URL (writes artifacts/link-check/, never fails on findings)
python .github/scripts/check_benefit_links.py --workers 8 --timeout 10
```

## Workflows

- **`pages.yml`** — validates the catalog, publishes, verifies the published output, deploys to
  Pages. Runs on push to `main`.
- **`validate.yml`** — runs all three test suites plus catalog validation. The correctness gate.
- **`security.yml`** — delegates to reusable workflows in `binbashburns/security-pipelines`
  (TruffleHog, Semgrep, Syft+Grype, lychee, ZAP), plus a catalog link audit. See `docs/ci.md`.
- **`new-benefit-from-issue.yml`** — parses a `type:new-benefit` issue into a catalog entry,
  validates it, and opens a PR.

Note that PRs opened by this last workflow use `GITHUB_TOKEN` and therefore **do not trigger other
workflows** — which is why it validates the catalog itself rather than relying on `validate.yml`.

## Conventions

- C# is nullable-enabled with implicit usings. Match the surrounding style; there is no
  `.editorconfig` and no formatter step.
- Python scripts are stdlib-only except `jsonschema`; keep them runnable with
  `python <script>` from the repo root and always pass `encoding='utf-8'` explicitly.
- Workflow scripts are CommonJS (`.cjs`) so `actions/github-script` can `require` them, and are
  kept free of side effects where practical so they can be unit tested.
- This repository is **public**. Do not add internal notes, personal data, credentials, or
  references to non-public systems.
