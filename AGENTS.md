# Project guidance

These rules apply to this repository. Start with [README.md](README.md), then read the relevant [CI/CD guide](docs/ci-cd.md) or [verification record](docs/verification.md).

## Purpose and limits

- This is Kit's order-preview training project. Use fictional data only.
- Return previews without saving or submitting orders. Keep successful responses at `mode: "training-preview"` and `submitted: false`.
- The site and repository are public. Do not add customer data, credentials, company-wide notes, or files from neighboring projects.
- CRM, databases, paid services, new cloud resources, and changes to company production resources need their own explicit scope. The current preview does not use them.

## Structure and runtime

- Local version: plain HTML/browser JavaScript, `server.cjs`, and `sample-order.json`. Use Node 24 built-ins; no application packages or framework are needed.
- Azure page: `azure-candidate/public`.
- Managed Functions API: `azure-candidate/api`, Python **3.11**, with the existing pinned `azure-functions` dependency.
- `azure-candidate/public/staticwebapp.config.json` must keep `platform.apiRuntime: "python:3.11"`.
- Hosting target: the existing **Free** Static Web App `kit-demo-training-dev`. App location is `azure-candidate/public`, API location is `azure-candidate/api`, and output location is empty.
- The Python API is already hosted with the Static Web App. Do not create a duplicate deployment workflow or separate Function App for this exercise.

## API contract

- `POST /api/preview` accepts JSON with `orderNumber`, optional `id`, and optional `Account_Name.name`.
- Trim and uppercase the order number; copy `id` only if present.
- A blank/missing account name is allowed and omits the account suffix from the description.
- Missing, blank, or non-text order number returns **400** with `Order number needed`.
- Malformed JSON and non-object JSON return their existing **400** responses.
- Keep Node and Python behavior consistent using `tests/preview-cases.json` as the shared cases.
- Display browser output through `textContent`; never interpret order text as HTML.

## Checks

- From the repository root: `node --check server.cjs` and `node --test tests/server.test.cjs`.
- From `azure-candidate/api`, with Python 3.11 and the existing dependency available: `python -m unittest discover -s tests -v`.
- Node checks start their own loopback listener on port 7181 and stop it afterward. Normal local use defaults to 7071. Do not stop an unrelated server to run checks.
- After deployment, `scripts/check_live_preview.py` checks the page, sample, and shared cases at the approved training hostname. Set `TRAINING_SITE_URL` to that public URL only.
- Run checks relevant to the change. Passing syntax/import checks alone do not prove a live endpoint works.
- Kit explicitly requested automated preview behavior tests for CI/CD on 2026-10-23. Keep them. The earlier closed PR #1 is historical; do not reopen it as part of routine work.

## GitHub and release process

- Use the installed **gh CLI** for GitHub account/repository/PR/workflow operations and Git for commits and pushes.
- Repository owner and commit author: **kitsantiagocc3**. Do not add AI attribution to code, docs, commits, or PRs.
- Check the working tree and remote state before changes. Use a task branch from current `main`; preserve existing work.
- Commit and push only when Kit requests it. Stage only intended project files; never force-push.
- Open a PR into `main`. Both **Check local Node server** and **Check Azure Functions candidate** must pass, and the branch must be up to date.
- Kit reviews and approves training changes for now. Only Kit currently has repository access, so external GitHub PR approvals are not required. A PR author cannot approve their own PR review.
- Merging into `main` runs CI again, then the **training-release** environment requires Kit's deployment approval. Branch pushes, PR runs, and manual check runs do not deploy.
- Leave merging and deployment approval to Kit unless that specific action is explicitly requested. Never bypass protections or fabricate approval.
- When a team reviewer is agreed, confirm their GitHub account/access and update the review policy. Do not invite an unconfirmed person.

## Documentation and safety

- Keep README as the entry point, `docs/ci-cd.md` as the setup/release guide, and `docs/verification.md` as dated evidence and repeatable checks.
- After meaningful work, update the relevant docs with decisions, observed results, unresolved issues, and next steps. Record CI/release evidence in the PR and standing work notes.
- Distinguish local checks, pushed commits, passing GitHub runs, merged code, deployed code, and live behavior. A branch push does not establish deployment.
- Never print, store, or request token values, passwords, connection strings, function keys, or secret settings. Do not read private settings to work around an access denial.
- Keep environment files, `local.settings.json`, virtual environments, packages, logs, and caches out of commits. Do not copy personal or company-wide guidance into this public repository.
- Use simple English in documentation and handoffs. Explain what changed, why, what was checked, and what remains.
