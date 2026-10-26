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

## Deployment patterns and workflow origins

Reviewed on **2026-10-26** against Microsoft documentation and this repository's workflow. The local workflow matched GitHub `main` at `f528472`; this checks the configuration, not a new deployment result.

Azure supports both arrangements below. Use this as the training baseline; choose the hosting arrangement before copying a workflow.

A **function** is a piece of backend code. A **Function App** is an Azure resource that hosts functions. Several functions can belong to one app and deployment.

| Question | Static Web App with managed Functions | Static Web App with a separate Function App |
| --- | --- | --- |
| What is deployed? | The website and its managed API together. | The website and the standalone backend each have a deployment. |
| Which deployment action is used? | `Azure/static-web-apps-deploy` includes the frontend and API folders. | `Azure/static-web-apps-deploy` publishes the frontend; `Azure/functions-action` can publish the standalone backend. |
| Which paths identify the code? | `app_location`, `api_location`, and `output_location`. | Frontend paths stay in the web workflow; `app-name` and `package` identify the Function App target and backend code. |
| Which triggers start the functions? | HTTP requests. | HTTP requests, timers, queues, and other supported events. |
| How does the website reach the API? | Through the website's `/api/...` routes. | Through an explicitly configured connection; Azure's linked-backend option also exposes `/api/...`. |
| Which Static Web Apps plan is needed? | Managed APIs are available on Free and Standard. | Azure's built-in linked Function App integration requires Standard. This requirement concerns that integration, not standalone Functions in general. |

Microsoft describes [managed and separate Functions](https://learn.microsoft.com/en-us/azure/static-web-apps/apis-functions) and the [Standard-plan requirement for a linked backend](https://learn.microsoft.com/en-us/azure/static-web-apps/functions-bring-your-own). For a linked backend, the web workflow uses an empty `api_location`, and the Function App has its own deployment. These are comparison details; keep this exercise's existing non-empty API location.

### Where the workflow files come from

- **Static Web Apps:** connecting a new Static Web App to GitHub can generate `.github/workflows/azure-static-web-apps-<name>.yml`. That happened for this training app. The folder settings come from the creation choices and can be maintained afterward. See [Microsoft's workflow configuration guide](https://learn.microsoft.com/en-us/azure/static-web-apps/build-configuration).
- **Standalone Function App:** enabling GitHub Actions deployment through Azure can generate a Functions workflow. A developer can also start from a supported template. Creating a Function App alone does not establish that GitHub deployment is configured. See [Microsoft's Functions workflow guide](https://learn.microsoft.com/en-us/azure/azure-functions/functions-how-to-github-actions).
- **Project release rules:** tests, job dependencies, branch conditions, and the `training-release` approval gate are maintained in this project. Treat the generated file as a starting point, then read its current contents to understand the release behavior.

A workflow is the YAML file in `.github/workflows`; a job groups steps; an action is a reusable step such as `Azure/static-web-apps-deploy`; a run is one execution of the workflow. Separate jobs or files do not establish that there are separate Azure resources. Separate deployment targets can also be handled by different jobs in one workflow.

### How to read this project's workflow

The file is [azure-static-web-apps-green-sea-04ba4b40f.yml](../.github/workflows/azure-static-web-apps-green-sea-04ba4b40f.yml).

| Job | What it does | Deploys to Azure? |
| --- | --- | --- |
| `local-server` / Check local Node server | Checks syntax and the local Node behavior. | No. |
| `azure-candidate` / Check Azure Functions candidate | Installs the Python dependency and runs handler tests. | No. |
| `build_and_deploy_job` / Build and Deploy Job | Waits for both checks and release approval, then calls `Azure/static-web-apps-deploy` with the frontend and API locations. | Yes, for an approved push to `main`. |

The Functions check job is a test job. The deployment step publishes both `azure-candidate/public` and `azure-candidate/api`. Adding another HTTP route to this API normally uses the same deployment.

**My recommendation:** keep managed Functions for this Free training exercise. Calls to another API or a database do not, by themselves, require a standalone Function App. Consider a separate backend when requirements call for scheduled or queue work, managed identity, a runtime unsupported by managed APIs, or independent backend releases. Agree on its target, permissions, configuration, and costs before changing the hosting arrangement.

## Standard plan for the next training change

1. **Define the behavior.** Write the fictional input, expected response, error cases, and what the function reads or writes. Decide which trigger and hosting arrangement it needs.
2. **Keep code locations clear.** Preserve this project's frontend and Python API folders. Separate source folders can share one repository and release.
3. **Build and check locally.** Run the relevant Node/Python checks and test the requested behavior. Include the website-to-API interaction when it changes.
4. **Review through a pull request.** Push only when requested. Keep checks on task branches and PRs; reuse the existing workflow and approval rules below.
5. **Release the agreed revision.** After merge and successful checks on `main`, Kit approves `training-release`. For the managed API, one deployment publishes the page and API. A future separate backend needs explicit deployment dependencies and verification for each target; two jobs must not be assumed to finish in a useful order.
6. **Verify the hosted behavior.** Check the page, the API's expected status and response, and the browser interaction. For a separate backend, check the intended website connection and access rules as well. A successful upload or handler import alone is insufficient evidence.
7. **Record the result.** Save the commit, Actions run link, verification result, unresolved issues, and next step. For separate releases, record each component's deployed revision. Follow-up fixes or restoration of an earlier version need their own approved release.

The detailed project release steps below implement the managed-API path. The separate-backend path is an option for future requirements, not a workflow or resource created by this documentation update.

## Review and approval rules

This follows the process Kit reported from Chris's meeting: work on a task branch, check changes, open a pull request, review and approve the release, merge into `main`, and verify deployment.

**GitHub settings configured and read back on 2026-10-23:**

- `main` requires a pull request and successful **Check local Node server** and **Check Azure Functions candidate** jobs. The branch must be up to date. These rules apply to administrators too; force pushes and branch deletion are disabled.
- Kit is the training approver for now. External GitHub PR approvals are set to zero because only Kit currently has repository access and a PR author cannot approve their own PR. Kit reviews the diff and completes the PR checklist before merging.
- The **training-release** environment requires deployment approval from **kitsantiagocc3** and allows deployment only from the `main` branch. Self-review is allowed for this training arrangement. This deployment approval is separate from a GitHub PR review.
- Kit remains the **only deployment approver**. Add another reviewer or approval job only when Kit explicitly asks; confirm the GitHub account/access before that change.

## Branch, review, and release steps

1. Build and check a task branch. Push only when Kit asks, using the installed GitHub CLI (`gh`) for repository/workflow operations and Git for commits/pushes. Check and reconcile remote state first.
2. Pushes and pull requests run the Node and Python jobs. The shared cases check complete response JSON and expected 200/400 statuses. These jobs need no Azure credentials.
3. Open a pull request into `main`. Kit reviews the diff/checks and records training release approval before merging. Branch pushes, PR runs, and manual check runs do not deploy to Azure.
4. After the merge, CI runs again on `main`. The deployment job depends on both successful CI jobs, then pauses for the **training-release** approval.
5. Kit opens the Actions run, selects **Review deployments**, chooses **training-release**, and clicks **Approve and deploy** after reviewing the checks.
6. The existing Azure action builds/deploys the static page and managed Python API with the same authentication and folder settings. No duplicate deployment workflow or separate Function App is added.
7. The final step checks the deployed URL returned by the Azure action: page, sample, ten preview cases, and six health/hello GET cases (**18 checks**). It accepts only the existing HTTPS training hostname, retries temporary failures up to three times, and returns a failure if verification does not pass. A verification failure is reported; it does not roll back a completed deployment.
8. Record the run link, live results, issues, and next step in the relevant docs. Never record secrets. Do not bypass the protections or approve a release on Kit's behalf.

The deployment and approval steps apply when this workflow is on `main`. Publishing a task branch runs CI only; merge and deployment approval are separate actions. Check the PR and Actions for the current revision and result.

GitHub documents [job dependencies](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs), [branch protections](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), and [deployment approval environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

For test evidence and commands, see [Verification record](verification.md).

For efficient changes, keep one coherent lesson on one branch/PR. The existing Python unittest discovery finds new test files, and the existing hosted-check step reads the shared cases. Several functions can ship together with one deployment approval from Kit; adding a function does not require another workflow or Azure resource.
