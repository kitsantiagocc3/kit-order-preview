# CI/CD and Azure deployment

This guide describes the existing training target and the release process reported from Chris's meeting. Read [project guidance](../AGENTS.md) before making changes.

## Azure target

Verified on **2026-10-23**:

| Setting | Value |
| --- | --- |
| Resource | `kit-demo-training-dev` |
| Subscription / resource group | Azure subscription 1 / `CC3` |
| Plan / API region | Free / East US 2 |
| Repository / branch | `kitsantiagocc3/kit-order-preview` / `main` |
| App location | `azure-candidate/public` |
| API location | `azure-candidate/api` |
| Output location | Empty; the page needs no build step. |
| API runtime | `python:3.11` |
| Deployment authorization policy | GitHub, as selected during resource creation. |

Kit created the resource through the Azure portal after refreshing access. Azure added the **Azure Static Web Apps CI/CD** workflow to GitHub. [Deployment run 40007094109](https://github.com/kitsantiagocc3/kit-order-preview/actions/runs/40007094109) completed successfully for commit `2b2a225f709f8059f9a76541bae305b4b764438f`.

The Python preview function is deployed as a managed API with the page. This exercise needs no separate Function App, storage account, or database. The root `server.cjs` remains the local Node version. See [Microsoft's managed Functions documentation](https://learn.microsoft.com/en-us/azure/static-web-apps/apis-functions).

## Review and approval rules

This follows the process Kit reported from Chris's meeting: work on a task branch, check changes, open a pull request, review and approve the release, merge into `main`, and verify deployment.

**GitHub settings configured and read back on 2026-10-23:**

- `main` requires a pull request and successful **Check local Node server** and **Check Azure Functions candidate** jobs. The branch must be up to date. These rules apply to administrators too; force pushes and branch deletion are disabled.
- Kit is the training approver for now. External GitHub PR approvals are set to zero because only Kit currently has repository access and a PR author cannot approve their own PR. Kit reviews the diff and completes the PR checklist before merging.
- The **training-release** environment requires deployment approval from **kitsantiagocc3** and allows deployment only from the `main` branch. Self-review is allowed for this training arrangement. This deployment approval is separate from a GitHub PR review.
- When a team reviewer is agreed, add their approved repository access, update the environment reviewer, and require an external PR approval. Do not invent or send an invitation to an unconfirmed account.

## Branch, review, and release steps

1. Build and check a task branch. Push only when Kit asks, using the installed GitHub CLI (`gh`) for repository/workflow operations and Git for commits/pushes. Check and reconcile remote state first.
2. Pushes and pull requests run the Node and Python jobs. The shared cases check complete response JSON and expected 200/400 statuses. These jobs need no Azure credentials.
3. Open a pull request into `main`. Kit reviews the diff/checks and records training release approval before merging. Branch pushes, PR runs, and manual check runs do not deploy to Azure.
4. After the merge, CI runs again on `main`. The deployment job depends on both successful CI jobs, then pauses for the **training-release** approval.
5. Kit opens the Actions run, selects **Review deployments**, chooses **training-release**, and clicks **Approve and deploy** after reviewing the checks.
6. The existing Azure action builds/deploys the static page and managed Python API with the same authentication and folder settings. No duplicate deployment workflow or separate Function App is added.
7. The final step checks the deployed URL returned by the Azure action: page, sample, and all ten preview cases. It accepts only the existing HTTPS training hostname, retries temporary failures up to three times, and returns a failure if verification does not pass. A verification failure is reported; it does not roll back a completed deployment.
8. Record the run link, live results, issues, and next step in the relevant docs. Never record secrets. Do not bypass the protections or approve a release on Kit's behalf.

The deployment and approval steps apply when this workflow is on `main`. Publishing a task branch runs CI only; merge and deployment approval are separate actions. Check the PR and Actions for the current revision and result.

GitHub documents [job dependencies](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs), [branch protections](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), and [deployment approval environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

For test evidence and commands, see [Verification record](verification.md).
