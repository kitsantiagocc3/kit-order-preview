# Learn Azure HTTP functions

This lesson adds functions to the existing Python API. The examples are prepared and tested locally on `learn/http-functions`; they are not a claim that the new routes are already deployed.

## What runs where

| Function | Request | What you learn |
| --- | --- | --- |
| `health` | `GET /api/health` | A trigger, route, JSON response, and host log. |
| `hello` | `GET /api/hello?name=Alex` | Query input, defaults, and trimming. |
| `preview` | `POST /api/preview` | JSON request bodies, validation, and 200/400 responses. |

All three are defined in `azure-candidate/api/function_app.py`. A **trigger** is what starts a function; here it is an HTTP request. `FunctionApp` collects the functions, and Azure registers their routes when the code is deployed.

One Static Web App can host this page and these managed functions. You do not create a separate Azure resource for each function. The root `node server.cjs` is the original Node exercise; it does not run these Python GET routes.

## 1. Start the Python Functions host

Open a PowerShell terminal in the repository root. These commands reuse the Python environment and Core Tools already installed in the training workspace; they install nothing and change no Azure resources.

```powershell
$lessonProjectRoot = (Get-Location).Path
$lessonWorkspaceRoot = Split-Path $lessonProjectRoot -Parent
$env:VIRTUAL_ENV = Join-Path $lessonWorkspaceRoot 'func-practice\.venv'
$env:Path = "$env:VIRTUAL_ENV\Scripts;$env:Path"
$env:FUNCTIONS_WORKER_RUNTIME = 'python'
$lessonFunctionsCli = Join-Path $lessonWorkspaceRoot 'azure-demo\tools\node_modules\.bin\func.cmd'
Set-Location (Join-Path $lessonProjectRoot 'azure-candidate\api')
& $lessonFunctionsCli start --port 7182 --address 127.0.0.1
```

The terminal should list **health [GET]**, **hello [GET]**, and **preview [POST]**. Keep it running. If port 7182 is already occupied, choose a free port and use that number in the examples; do not stop an unrelated process.

## 2. Open health

Open `http://127.0.0.1:7182/api/health` in your browser. The address bar sends a GET request. Expect **200** and:

```json
{"status":"ok","service":"order-preview","mode":"training-preview","submitted":false}
```

This proves that the handler responded. It does not check a database, CRM, storage account, or the Azure platform's overall health. The terminal logs a fixed trigger message and execution result; it does not log your input values.

## 3. Change hello's query input

Open each URL and compare the message:

| URL after `http://127.0.0.1:7182` | Expected message |
| --- | --- |
| `/api/hello?name=Alex` | `Hello, Alex!` |
| `/api/hello` | `Hello, trainee!` |
| `/api/hello?name=` | `Hello, trainee!` |
| `/api/hello?name=%20Alex%20` | `Hello, Alex!` |

`?name=Alex` is a **query parameter**: input attached to the URL. `%20` encodes a space. Use fictional names in this public training example.

Read the complete `hello` function in `function_app.py`:

- `@app.function_name(name="hello")` gives the function its name in the host/logs.
- `@app.route(route="hello", methods=["GET"])` registers the route and method. Azure supplies `/api`; do not put `/api/hello` in the decorator.
- `req.params.get("name")` reads query input. Trimming removes outer spaces; blank input uses `trainee`.
- `json_response(..., 200)` returns JSON with HTTP status 200.

Each request builds a fresh response. These functions save no records and make no external service calls.

## 4. Compare GET with POST

In a second PowerShell terminal, call the existing preview function:

```powershell
$lessonOrder = @{id='TRAINING-301'; orderNumber=' so-100 '; Account_Name=@{name='Acorn Training'}} | ConvertTo-Json -Depth 3
Invoke-RestMethod -Uri 'http://127.0.0.1:7182/api/preview' -Method Post -ContentType 'application/json' -Body $lessonOrder
```

Expect `SO-100`, `Order SO-100 - Acorn Training`, and `submitted: false`. Compare the code: hello reads `req.params`; preview reads `req.get_json()`. Opening `/api/preview` in the address bar does not send POST.

## 5. Run the checks

Open another terminal in the repository root:

```powershell
$lessonWorkspaceRoot = Split-Path (Get-Location).Path -Parent
$lessonPython = Join-Path $lessonWorkspaceRoot 'func-practice\.venv\Scripts\python.exe'
Set-Location .\azure-candidate\api
& $lessonPython -m unittest discover -s tests -v
```

There are two unittest methods that iterate over **16 scenarios**: ten preview cases and six GET cases. `OK` means the handler results matched. These direct handler checks are separate from real host routing; the local host and emulator were also exercised during setup, as recorded in [verification](verification.md).

After editing Python code, save and restart your host if the change has not loaded. Repeat the same URL and check the actual response. Stop your host with **Ctrl+C** when finished.

## 6. Your turn: add about

Try this as your next small change; it is not yet added to the app. Put this complete function after `hello`, update the file header's function list, and restart the host:

```python
@app.function_name(name="about")
@app.route(route="about", methods=["GET"])
def about(req: func.HttpRequest) -> func.HttpResponse:
    return json_response({
        "lesson": "HTTP triggers",
        "mode": "training-preview",
        "submitted": False,
    }, 200)
```

It reads no input and writes only an HTTP response. Open `http://127.0.0.1:7182/api/about` and compare its JSON with the function. Then add a GET case in `tests/function-get-cases.json`, and import/map `about` in `azure-candidate/api/tests/test_http_functions.py`. Run the checks again. No additional workflow job is needed.

## Release and next topics

Batch related learning changes into one branch/PR. When Kit requests a push, publish the branch and inspect CI. After Kit reviews/merges, the existing deployment waits for **Kit only**; then the hosted checker verifies all registered examples. Do not add another approver or approval job until Kit explicitly requests it.

For now, learn HTTP routes, query input, JSON bodies, validation, tests, and logs. Managed Static Web Apps APIs support HTTP triggers. Timer and queue lessons require a separate approved setup; they are a later exercise, not additional cloud resources to create for this lesson.

Microsoft references: [Python programming model](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python), [managed Functions API](https://learn.microsoft.com/en-us/azure/static-web-apps/apis-functions), and [runtime support](https://learn.microsoft.com/en-us/azure/static-web-apps/languages-runtimes).
