# Contributing to SoldierSave

Thanks for helping improve SoldierSave and making it easier for Soldiers and families to find benefits.

## How to request a new benefit

The easiest way to contribute is by opening a **“New Benefit or Resource”** issue:

1. Go to the repo’s **Issues** tab.
2. Click **New issue** and pick **“New Benefit or Resource”**.
3. Fill out the form with the benefit name, URL(s), category, tags, and a short description.

When the issue is created, a GitHub Actions workflow will:

- Parse the issue form.
- Append a new entry to `data/benefits.json` (and mirror it into `src/SoldierSave.Web/wwwroot/data/benefits.json`).
- Set:
  - `source.type` to `community`.
  - `source.reference` to `issue-<number>`.
  - `addedBy` to your GitHub handle.
- Open a pull request on a `new-benefit/issue-<number>` branch with those changes.

I (or another maintainer) will then review and merge the PR.

## Editing benefits data directly

All benefits live in `data/benefits.json`.

Each entry looks roughly like:

```jsonc
{
  "id": "expert-voice",
  "name": "Expert Voice",
  "url": "https://www.expertvoice.com/categories/military/",
  "urls": ["https://www.expertvoice.com/categories/military/"],
  "summary": "Short description of the benefit.",
  "categories": ["discounts", "outdoor"],
  "tags": ["discounts", "outdoor"],
  "eligibility": ["active-duty", "veteran"],
  "source": {
    "type": "community",
    "reference": "issue-123"
  },
  "addedBy": "your-github-username",
  "addedAt": "2025-01-01T00:00:00Z"
}
```

Guidelines:

- Keep `id` unique, lowercase, and hyphenated (no spaces).
- `tags` should be short slugs (e.g., `discounts`, `travel`, `taxes`, `veterans-day`).
- Use your GitHub username (or preferred handle) for `addedBy`.

## Imported data

Existing benefits from the original `army-benefits-unofficial-pages` content and the initial PDF import are already present in `data/benefits.json`.

Those entries are marked with `source.type` of:

- `"adoc"` for content imported from the legacy AsciiDoc repositories.
- `"pdf"` for content imported from the original Military Benefits PDF.

Please do **not** edit those imported entries by hand unless you’re fixing obvious typos or broken links. If you want to add new benefits, use the issue template or append new entries with `"source.type": "community"` instead.

## Development

To run the site locally:

```bash
dotnet restore
dotnet run --project src/SoldierSave.Web/SoldierSave.Web.csproj
```

Then browse to the URL printed in the console (usually `https://localhost:port`).
