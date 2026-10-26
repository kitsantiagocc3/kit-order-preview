# Verification record

Checks below were observed on **2026-10-23**. This record separates local checks and the existing live app from a new deployment. Check [GitHub Actions](https://github.com/kitsantiagocc3/kit-order-preview/actions) and the relevant pull request for the current commit's CI result.

## Test results recorded during the exercise

These observations were shared during the training session on **2026-10-23**. The screenshot rows describe browser results, not a separate live endpoint test run.

| Check | Observed result | Evidence |
| --- | --- | --- |
| Normal preview | The shared response contained `SO-100`, a description including the supplied account name, `training-preview`, and `submitted: false`. | Response body shared in the session. The HTTP status was not captured alongside that body. |
| Blank account name | **200**; description `Order TRAINING-301`; `submitted: false`. | Browser screenshot with `orderNumber: "TRAINING-301"` and an empty account name. |
| Blank order number | **400**; `Order number needed`. | Browser screenshot with an empty order number. |
| Invalid JSON | **400**; `Invalid JSON. Check your quotes, commas, and braces.` | Browser screenshot with an empty JSON box. |

Those screenshots record the earlier local browser checks. The hosted checks below separately verified the normal-case HTTP status and the response when the order number is missing.

Additional checks during the build passed JavaScript syntax validation and in-memory request/display checks, including sample loading and the four preview cases. Live GET requests for the page and sample file returned **200**. In-memory checks do not replace observing the actual browser requests.

### How to repeat the checks

1. Keep `sample-order.json` valid and make temporary error-test edits in the browser box.
2. Use the [normal example in README](../README.md#sample-input-and-expected-response) for the full successful preview.
3. Clear `Account_Name.name` and check the shorter description.
4. Clear `orderNumber`, then separately remove that field, and check the **400** message.
5. Remove the final closing brace from otherwise valid JSON and check the invalid-JSON **400** message.
6. Restore valid input and confirm that a normal preview still succeeds.

To inspect the actual requests in Edge or Chrome, right-click the page, choose **Inspect**, and open **Network** before clicking **Preview order**. Select the `preview` request:

- **Headers:** request URL, method, and HTTP status.
- **Payload:** the JSON text sent by the page.
- **Response:** the JSON returned by the API.

## Initial hosted checks

These checks sent fictional input to the live site and compared actual status codes and JSON responses with the expected results. All **7 checks passed** on 2026-10-23:

| Check | Verified result |
| --- | --- |
| `GET /` | **200**, HTML containing the preview API call. |
| `GET /sample-order.json` | **200**, JSON containing an order number. |
| Normal preview | **200**, `SO-100`, `Order SO-100 - Acorn Training`, `training-preview`, and `submitted: false`. |
| Blank account name | **200**, `Order SO-100` without an account suffix. |
| Missing order number | **400**, `Order number needed`. |
| Blank order number | **400**, `Order number needed`. |
| Malformed JSON | **400**, the expected message about quotes, commas, and braces. |

The successful preview responses matched the complete expected JSON, including the input ID when supplied. These HTTP checks establish the page and API responses; a manual click through the live browser page is the next learning step.

An initial HTTP client attempt failed during name lookup. DNS resolution and a direct retry succeeded. The portal later displayed **Waiting for deployment** even though the workflow succeeded and the page returned **200**. Refresh the portal and check the workflow and live URL before treating that label as a deployment failure.

## Test history

[PR #1](https://github.com/kitsantiagocc3/kit-order-preview/pull/1) contained checks that passed locally and on GitHub: **16 Node checks and 10 Python cases**. [Checks run 40004740584](https://github.com/kitsantiagocc3/kit-order-preview/actions/runs/40004740584) passed for commit `eca2b5cc8854431d3c46954be74c463b809b0f9c`.

Kit deliberately removed the tests and closed the PR without merging it. Later on 2026-10-23, Kit explicitly requested automated preview tests for CI/CD. The shared cases and checks are included in the CI/CD task branch; PR #1 remains closed.

## CI/CD preparation checks

| Check performed on 2026-10-23 | Result |
| --- | --- |
| Local Node syntax and behavior checks | **16/16 passed**. Tests start/stop their own server on port 7181; the normal local default remains 7071. |
| Python handler checks | **10 shared cases passed** in the unittest subtest loop. |
| Workflow YAML and configuration | Parsed successfully; CI dependencies, main-only deployment, approval environment, paths, runtime, and hosted checker step verified. |
| New hosted checker against the existing live app | **Page, sample, and all 10 preview cases passed**. One temporary DNS failure was recovered by its retry. |

To repeat the local Node checks from the repository root:

```powershell
node --check server.cjs
node --test tests/server.test.cjs
```

With the existing Python 3.11 environment active, run the handler checks from `azure-candidate/api`:

```powershell
python -m unittest discover -s tests -v
```

To check the live training site from the repository root with Python 3.11:

```powershell
$env:TRAINING_SITE_URL = "https://green-sea-04ba4b40f.1.azurestaticapps.net"
python scripts/check_live_preview.py
```

GitHub approval and branch settings were configured as described in the [CI/CD guide](ci-cd.md). These setup checks did not change Azure resources or deploy a new application version. Review the PR checks for the current task revision before merging.

## Zoho read integration, local preparation (2026-10-23)

The new read route and page section are prepared on `feature/zoho-sandbox-read`.
They have not been committed, pushed, or deployed. The hosted API's configuration
belongs in the Static Web App's backend environment variables; the same names can
be supplied separately to a local backend for checks. See the
[Zoho lesson](zoho-sandbox.md) for the six setting names and request flow.

| Verification | Observed result |
| --- | --- |
| Existing Node behavior/page checks | 16 tests passed. |
| Python unittest discovery | 9 methods passed, including the existing ten preview subcases and the new identity/configuration boundaries. |
| Real handler/client against Postman simulation | Eight record cases and one OAuth error-body case passed; exit 0. |
| Running Functions host, launched with Python 3.11 | Two read requests returned 200 and only the four selected lead fields. |
| Dependency evidence | Local simulation recorded OAuth refresh POSTs and CRM GETs. No redirect target was followed. Only synthetic credentials and records were used. |
| Website emulator | Page/sample returned 200; sign-in form returned 200; anonymous and spoofed-principal requests were rejected with 401; existing preview returned 200. |
| Browser script and launcher | Syntax checks passed. The launcher validates missing OAuth configuration before starting the host. |

The local Functions host emitted a storage health warning because
`AzureWebJobsStorage` was not configured; the HTTP handlers above still succeeded.
These HTTP results do not establish the health of external storage or the Azure
platform. No storage account or new resource was created.

An authorized connector separately verified the selected sandbox and read the
user-selected fictional lead. This is not evidence that the application's own
OAuth settings are configured. Real application-to-sandbox OAuth, live sign-in,
the manual browser click, and a hosted Zoho release remain unverified. No real
credentials were read from private files or printed, and no Azure settings were
read or changed. Local test servers were stopped after verification.
