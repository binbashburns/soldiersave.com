# Security Policy

## Reporting a vulnerability

Please report security issues privately rather than opening a public issue.

Use GitHub's private vulnerability reporting on this repository:
**Security → Report a vulnerability**
(<https://github.com/binbashburns/soldiersave.com/security/advisories/new>).

Include what you found, how to reproduce it, and what an attacker could do with it. You will get an
acknowledgement as soon as the report is read. This is a volunteer-maintained project, so please
allow a reasonable window for a fix before disclosing publicly.

## Scope

This project is a static site: a Blazor WebAssembly application and a JSON catalog, served from
GitHub Pages. It stores no user data, has no backend, no accounts, and no authentication.

In scope:

- Cross-site scripting or content injection through the benefit catalog or the site itself.
- Flaws in the GitHub Actions workflows, particularly the issue-to-pull-request automation, that
  could allow code or unreviewed data into the repository.
- Supply chain issues in the dependencies declared in `packages.lock.json`.

Out of scope:

- The content or security posture of third-party sites the catalog links to. If a link is wrong,
  dead, or now points somewhere it shouldn't, please open a normal issue instead.
- Missing HTTP response headers that GitHub Pages does not allow a project to set. The site sets
  what it can through a `Content-Security-Policy` meta tag; `frame-ancestors` and
  `X-Content-Type-Options` are header-only and cannot be applied.
- Findings from automated scanners without a demonstrated impact.

## Data

The catalog contains links to publicly available military benefit programs and discounts. It
contains no personal data and no credentials. If you believe something published here is sensitive
or personally identifying, please report it privately using the process above.
