# Read one fictional Zoho lead

This lesson adds a separate CRM read to the existing Python API and page.
Its code is prepared locally and is not yet pushed or deployed.
The order preview continues to accept fictional JSON and does not save orders.

## Request flow

1. **Load training lead** calls `GET /api/zoho/training-lead`.
2. Static Web Apps requires sign-in for `/api/zoho/*`. The handler also checks
   the platform client principal. Its identity header is trusted only behind
   Static Web Apps or the local emulator; do not expose the bare Functions host.
3. The Python backend reads its OAuth settings, refreshes an access token when
   needed, and uses the fixed lead ID.
4. It sends `GET https://sandbox.zohoapis.com/crm/v8/Leads/{id}` with
   `fields=First_Name,Last_Name,Company`. The authorization header stays in Python.
5. The page displays only `id`, `First_Name`, `Last_Name`, and `Company` using
   `textContent`. Extra CRM fields are discarded.

There is no record-ID input or general CRM proxy in the page. Query parameters
cannot select another record. This lesson does not create or edit CRM records.

## Backend configuration in Azure

For the hosted managed API, use **kit-demo-training-dev > Settings > Environment
variables**. Select its main environment (labelled Production even for this
training app), add the settings below, then Apply and save. An authorized operator
enters credential values through the approved setup. These settings are for the
backend API; they are separate from frontend build variables.

| Setting | Purpose |
| --- | --- |
| `ZOHO_CLIENT_ID` | Existing approved sandbox OAuth client ID. |
| `ZOHO_CLIENT_SECRET` | Its private client secret, configured through the approved secret process. |
| `ZOHO_REFRESH_TOKEN` | Existing refresh token authorized for the approved sandbox organization. |
| `ZOHO_ACCOUNTS_URL` | `https://accounts.zoho.com` for this US sandbox. |
| `ZOHO_TRAINING_LEAD_ID` | The one fictional sandbox record selected for this lesson. |
| `ZOHO_API_BASE_URL` | Defaults to `https://sandbox.zohoapis.com`. Production and arbitrary hosts are rejected. |

No Azure settings were inspected or changed while preparing this code. If the
Environment variables page is denied, the authorized resource owner must configure
them; do not read settings through another tool to work around a denial.

Postman's private Current Values and this chat's Zoho connector do not supply
credentials to Python automatically. For optional local checks, use the same names
in an approved process environment or the local Functions configuration. Deploying
code does not transfer local configuration to Azure. The provided local launcher
uses process variables and does not prompt for, print, or create credential files.

Python submits the refresh grant as a form body to `/oauth/v2/token`, never in a
URL. Access tokens stay in worker memory, are reused until shortly before expiry,
and are refreshed once after a CRM 401 before one GET retry. The refresh token
stays in backend configuration. No separate `ZOHO_ACCESS_TOKEN` setting is needed.
The read needs an appropriate sandbox module READ scope and the user's CRM access.

Before any hosted release, arrange the approved backend settings. Sign-in
with a built-in provider is available to any account that can authenticate; it is
not a CC3-only authorization policy. Only the explicitly selected fictional record
may be configured for this public training app. Real CRM data needs a separate
authorization design.

## Run locally with approved sandbox authorization

Use a terminal whose approved credential provider already supplies
the three OAuth credential settings. The launcher stops if they are absent;
do not paste values into chat or add them to files. From this checkout, replacing the fictional ID below
with the selected record ID:

```powershell
& '..\func-practice\.venv\Scripts\python.exe' scripts/start_zoho_local.py --mode Sandbox --lead-id '<fictional-record-id>'
```

In a second terminal at the same checkout:

```powershell
& '..\azure-demo\tools\node_modules\.bin\swa.cmd' start .\azure-candidate\public --api-devserver-url http://127.0.0.1:7184 --host 127.0.0.1 --port 4281 --swa-config-location .\azure-candidate\public
```

Open `http://127.0.0.1:4281`. Click **Load training lead**, follow the sign-in link,
and use the emulator's fictional identity form. No real GitHub password is needed
by that local form. Load the lead again and expect a response with
`source: "zoho-sandbox"`, the four selected fields, and `submitted: false`.
This real app-to-sandbox result remains unverified until backend authorization is
provided. A connector read is separate evidence.

Use **Ctrl+C** to stop each owned server. Choose free ports if these are occupied;
do not stop someone else's process. The root Node server does not run this Python
route; use the Functions host and emulator for the integration lesson.

## Repeat without real credentials

The local mock is based on the official Zoho V8 Get Records envelope and fields.
No reusable mock existed in the named training workspace's MCP mock inventory;
the CLI was not signed in for its separate cloud mock inventory.

In terminal 1:

```powershell
postman simulation run postman/simulations/zoho-sandbox.sim.yaml --port 4901 --output ndjson --no-history
```

In terminal 2:

```powershell
& '..\func-practice\.venv\Scripts\python.exe' scripts/start_zoho_local.py --mode Simulation
```

Start the emulator in terminal 3 with the same command above. The result says
`source: "local-simulation"` and contains an invented lead. Simulation mode accepts
only a fixed non-secret placeholder, loopback address, and explicit local flag;
it is rejected when Azure runtime markers are present. The simulation includes
separate Zoho Accounts and CRM members so token refresh runs over real local HTTP.

Run the real handler/client against eight record cases and one OAuth error case:

```powershell
& '..\func-practice\.venv\Scripts\python.exe' scripts/check_zoho_simulation.py
```

The cases cover a valid response with extra fields, no record, rejected Zoho
authorization, rate limiting, malformed JSON, redirects, a mismatched record ID,
and an upstream server error. A separate OAuth case rejects an HTTP 200 response
containing an error instead of an access token. Check the simulation request log to confirm GETs
reached `/crm/v8/Leads/{id}`. The redirect must not reach `/must-not-follow`.
These checks exercise real HTTP against a stand-in, not the live Zoho service.

## Response contract

| Situation | Status |
| --- | --- |
| Selected lead loaded | 200 |
| Client query attempts to choose another record | 400 |
| No platform sign-in | 401 |
| Configured record not found | 404 |
| Zoho authorization or response failed | 502 |
| Missing backend setup or upstream rate limit | 503 |
| Zoho request timed out | 504 |

Upstream authorization errors use 502, not the application's 401 sign-in response.
Zoho error bodies and credentials are never returned to the browser. Responses use
`Cache-Control: no-store`. No new packages or Azure resources are required.

References: [Zoho Get Records](https://www.zoho.com/crm/developer/docs/api/v8/get-records.html),
[Zoho environment-specific authorization](https://www.zoho.com/crm/developer/docs/api/v8/auth-request.html),
[Zoho access token refresh](https://www.zoho.com/crm/developer/docs/api/v8/refresh.html),
[Static Web Apps application settings](https://learn.microsoft.com/azure/static-web-apps/application-settings),
[Static Web Apps identity](https://learn.microsoft.com/azure/static-web-apps/user-information),
and [route access rules](https://learn.microsoft.com/azure/static-web-apps/configuration).
