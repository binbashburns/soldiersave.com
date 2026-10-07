# soldiersave.com

[![Last commit](https://img.shields.io/github/last-commit/binbashburns/soldiersave.com?color=bd93f9&labelColor=282a36)](https://github.com/binbashburns/soldiersave.com/commits/main)
[![Open issues](https://img.shields.io/github/issues/binbashburns/soldiersave.com?color=ff5555&labelColor=282a36)](https://github.com/binbashburns/soldiersave.com/issues)
[![Live site](https://img.shields.io/badge/live-SoldierSave.com-50fa7b?labelColor=282a36)](https://soldiersave.com)
[![Benefits](https://img.shields.io/badge/benefits-211-6272a4?labelColor=282a36)](data/benefits.json)
[![Resume](https://img.shields.io/badge/resume-binbashburns.com-F1FA8C?labelColor=282a36)](https://binbashburns.com)

Repository that holds links and data for SoldierSave. Open an issue to add a new resource now!

## Project layout

- `data/benefits.json` – canonical list of benefits, discounts, and resources.
- `src/SoldierSave.Web` – Blazor WebAssembly frontend (GitHub Pages–friendly).

## Prerequisites

- .NET SDK 9.x installed (`dotnet --version` should show 9.x).

## Running the Blazor site locally

From the repo root:

```bash
dotnet restore
dotnet run --project src/SoldierSave.Web/SoldierSave.Web.csproj
```

Then open the URL printed in the console (for example `http://127.0.0.1:5xxx`).  
You should see the SoldierSave landing page with tag-based filtering over all benefits.

## Requesting a new benefit (auto-PR flow)

The preferred way to suggest a new benefit, discount, or resource is via a GitHub issue:

- Open a new issue and choose **“New Benefit or Resource”**.
- Fill out the form (name, primary URL, extra URLs, category, tags, eligibility, short description).

When the issue is created:

- A GitHub Actions workflow parses the issue form.
- It automatically appends a new entry to `data/benefits.json`.
  - Sets:
    - `source.type` to `community`.
    - `source.reference` to `issue-<number>`.
    - `addedBy` to your GitHub handle.
  - Opens a pull request on a branch named `new-benefit/issue-<number>` with the change.

I will then review and merge the PR.

## Suggesting new features

For general improvements or new capabilities (not specific to a single benefit), open a **“Feature Request”** issue:

- Use the user-story format in the template:
  - _“As a &lt;type of user&gt;, I would like &lt;capability&gt; so that &lt;benefit&gt;.”_
- Add any supporting details or examples that clarify what you want.

These issues help shape the roadmap for SoldierSave.com and are the main way to collect feedback and future ideas.

## Running the tests

Three suites cover the site and its automation. The browser suite needs a Release publish first, at
that exact path.

```bash
python -m pip install -r .github/scripts/requirements.txt -r tests/browser/requirements.txt

node --test tests/workflows/*.test.cjs                      # issue-form importer
python -m unittest discover -s tests/maintenance -v          # maintenance scripts
python .github/scripts/validate_catalog.py                   # catalog schema + invariants

dotnet publish src/SoldierSave.Web/SoldierSave.Web.csproj -c Release -o artifacts/publish
python .github/scripts/check_publish.py artifacts/publish/wwwroot
python -m playwright install chromium
python -m unittest discover -s tests/browser -v              # Playwright
```

## Automatic link checking

A scheduled GitHub Actions job runs weekly and checks every URL in `data/benefits.json`:

- Each unique URL gets an HTTP request (HEAD, falling back to GET).
- Responses in the 2xx–3xx range count as successful.
- Results are classified as `ok`, `error`, or `unverified`. **Unverified is not broken** — many
  retailers and `.mil` sites reject requests from CI runners with a 403 or drop the connection
  entirely, which says nothing about whether the benefit is still available. Only `error` rows are
  worth acting on without visiting the page.
- Findings are written to a workflow artifact and to a single tracking issue labeled `type:bug`,
  `area:data`, and `benefit-link-check`. The issue is updated in place rather than reopened, and is
  closed automatically once every link responds.

A broken external site never fails the build.

See [`docs/ci.md`](docs/ci.md) for the full CI and security pipeline layout.

## Screenshots

### Landing page with tag filters and search  
  ![landing-page](docs/screenshots/landing-page.png)

### Example benefit details + attribution  
  ![benefit-detail](docs/screenshots/benefit-detail.png)

### About page and “Contribute on GitHub” banner  
  ![about-page](docs/screenshots/about-page.png)
