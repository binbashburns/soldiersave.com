# soldiersave.com

[![Last commit](https://img.shields.io/github/last-commit/binbashburns/soldiersave.com?color=bd93f9&labelColor=282a36)](https://github.com/binbashburns/soldiersave.com/commits/main)
[![Open issues](https://img.shields.io/github/issues/binbashburns/soldiersave.com?color=ff5555&labelColor=282a36)](https://github.com/binbashburns/soldiersave.com/issues)
[![Live site](https://img.shields.io/badge/live-SoldierSave.com-50fa7b?labelColor=282a36)](https://soldiersave.com)
[![Benefits](https://img.shields.io/badge/benefits-219-6272a4?labelColor=282a36)](data/benefits.json)
[![Resume](https://img.shields.io/badge/resume-binbashburns.com-F1FA8C?labelColor=282a36)](https://binbashburns.com)

Repository that holds links and data for SoldierSave. Open an issue to add a new resource now!

## Project layout

- `data/benefits.json` – canonical list of benefits, discounts, and resources.
- `src/SoldierSave.Web` – Blazor WebAssembly frontend (GitHub Pages–friendly).

## Prerequisites

- .NET SDK 9.x installed (`dotnet --version` should show 9.x).

## Running the Blazor site locally

From the repo root (`soldiersave.com` directory):

```bash
cd soldiersave.com
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
- It automatically:
  - Appends a new entry to `data/benefits.json` (and mirrors it into `src/SoldierSave.Web/wwwroot/data/benefits.json`).
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

## Automatic link checking

To keep links fresh, a scheduled GitHub Actions workflow runs once a week and checks every URL in `data/benefits.json`:

- For each unique URL, it performs an HTTP request (HEAD with a GET fallback).
- Responses in the 2xx–3xx range are treated as successful.
- Any failures (4xx/5xx responses or network errors) are collected and reported.
- If any broken or suspicious links are found, the workflow automatically opens a GitHub issue labeled:
  - `type:bug`
  - `area:data`
  - `link-check`

## Screenshots

### Landing page with tag filters and search  
  ![landing-page](docs/screenshots/landing-page.png)

### Example benefit details + attribution  
  ![benefit-detail](docs/screenshots/benefit-detail.png)

### About page and “Contribute on GitHub” banner  
  ![about-page](docs/screenshots/about-page.png)
