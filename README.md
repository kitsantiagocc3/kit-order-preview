# Kit order preview

A training app for turning a fictional order into a readable preview. Enter or edit JSON, click **Preview order**, and see either the preview or an explanation of what needs fixing.

The local version uses plain HTML, browser JavaScript, and Node.js built-in modules at `http://127.0.0.1:7071`. The Azure version uses the page in `azure-candidate/public` and a Python 3.11 managed Functions API in `azure-candidate/api`.

The Free Azure Static Web App is live at [kit-demo-training-dev](https://green-sea-04ba4b40f.1.azurestaticapps.net). Both versions return previews without saving or submitting orders. Use fictional data only; the hosted site and repository are public.

## Documentation

| Document | Use it for |
| --- | --- |
| [Project guidance](AGENTS.md) | Scope, runtime, API rules, safety, and contribution process. |
| [CI/CD and Azure deployment](docs/ci-cd.md) | Hosting settings, GitHub checks, review, deployment approval, and release steps. |
| [Verification record](docs/verification.md) | Dated evidence, historical results, and commands to repeat the checks. |
| [Read a Zoho sandbox lead](docs/zoho-sandbox.md) | Local Python-to-CRM read, backend configuration, and simulation checks. |

## Files and their roles

| File | What it does |
| --- | --- |
| `index.html` | Displays the page, loads the sample, sends the editable JSON to the API, and displays the response. It includes the page's CSS and browser JavaScript. |
| `sample-order.json` | Holds the fictional starting input. The page fetches this file through the local server when it opens. |
| `server.cjs` | Serves the page and sample file, checks preview requests, and builds JSON responses. |
| `azure-candidate/public/` | Contains the page and fictional sample deployed to Azure. |
| `azure-candidate/public/staticwebapp.config.json` | Selects `python:3.11` for the managed API. |
| `azure-candidate/api/function_app.py` | Implements `POST /api/preview` with the same preview rules in Python. |
| `azure-candidate/api/host.json` and `requirements.txt` | Configure the Functions host and its Python dependency. |
| `tests/preview-cases.json` | Defines ten fictional requests and their exact expected responses. |
| `tests/server.test.cjs` | Checks the local Node routes, preview behavior, and safe page output. |
| `azure-candidate/api/tests/test_function_app.py` | Runs the same ten cases against the Python handler. |
| `scripts/check_live_preview.py` | Checks the hosted page, sample, and ten preview cases after deployment. |
| `.github/workflows/azure-static-web-apps-green-sea-04ba4b40f.yml` | Runs CI and gates the existing Azure deployment on successful checks and release approval. |
| `.github/pull_request_template.md` | Records the review and release checklist. |
| `.gitattributes` | Keeps workflow YAML line endings consistent on Windows and Linux. |
| `README.md`, `AGENTS.md`, and `docs/` | Explain how to run, check, change, and release the project. |

The original exercise specified two application files. A third application file, `sample-order.json`, was added so the starting data has a clear, separate location. The server reads that file; it does not write order results back to it.

## How to run

Node.js is required. The installed version checked during this exercise was **v24.22.1**. No package installation is needed.

1. Open `kit-order-preview` in VS Code.
2. Choose **Terminal > New Terminal**. Make sure the terminal is in this folder.
3. Check the version and start the server:

   ```powershell
   node --version
   node server.cjs
   ```

4. The terminal should show `Open http://127.0.0.1:7071`.
5. Open that address in a browser and keep the terminal running.

To stop the server, press **Ctrl + C** in its terminal. To restart it, run `node server.cjs` again.

`127.0.0.1` means this computer. The same local server serves the page, sample data, and preview API.

## What happens locally from start to finish

1. The browser requests `GET /`. The server reads `index.html` and sends the page back.
2. The page runs `loadSampleOrder()`, which requests `GET /sample-order.json`.
3. The server reads and parses `sample-order.json`, then returns its JSON data. The page puts that data into the editable **Order JSON** box.
4. The user can change the text in that box. These browser edits do not change the saved JSON file.
5. Clicking **Preview order** runs `previewOrder()`. It sends the box's current text to `POST /api/preview` with `Content-Type: application/json`.
6. The server collects the request text and uses `JSON.parse()` to read it. Invalid JSON returns an error with HTTP status **400**.
7. For a valid JSON object, the server checks the order number, removes surrounding spaces, and changes its letters to uppercase. It builds a description using the optional account name.
8. The server sends either the successful preview or an error as JSON. The page shows the HTTP status and places the formatted response in the **Result** box using `textContent`.

An API is a route a program can call to exchange data. Here, the preview route performs a calculation and returns a response. It does not create an order record.

The Result box is the `<pre id="result">` element in `index.html`. The complete preview response is created in memory by `server.cjs`; it is not read from a saved results file.

## Sample input and expected response

At the time this README was written, the saved sample contained `orderNumber: "TRAINING-301"` and an account name containing one space. That is a blank-account example, so its expected description is `Order TRAINING-301`.

For the original normal example, put the following in the page's editable box:

```json
{
  "id": "TRAINING-301",
  "orderNumber": " so-100 ",
  "Account_Name": {
    "name": "Acorn Training"
  }
}
```

The expected response is **HTTP 200**:

```json
{
  "id": "TRAINING-301",
  "orderNumber": "SO-100",
  "description": "Order SO-100 - Acorn Training",
  "mode": "training-preview",
  "submitted": false
}
```

`id` is copied from the input when present. `orderNumber` is cleaned. `description` is constructed by the server. `mode` and `submitted` are fixed preview values.

## Local routes

| Method and route | Purpose |
| --- | --- |
| `GET /` or `GET /index.html` | Open the page. |
| `GET /sample-order.json` | Read the saved sample input. The **View sample JSON** link opens this route. |
| `POST /api/preview` | Send the current editable input and receive a preview or validation error. |

Opening an address in the browser's address bar sends a GET request. To use the POST preview route, click **Preview order** on the page.

## Validation rules

| Input | Result |
| --- | --- |
| Valid order number | Trim surrounding spaces and uppercase the number; return **200**. |
| Blank or missing account name | Allow the preview and omit the account suffix from the description. Whitespace-only account names are also treated as blank. |
| Blank, missing, or non-string order number | Return **400** with `Order number needed`. |
| Invalid JSON, including an empty request body | Return **400** with `Invalid JSON. Check your quotes, commas, and braces.` |
| Valid JSON that is not an object, such as `null` or an array | Return **400** with a message asking for an order object. |

Every successful preview response includes `mode: "training-preview"` and `submitted: false`.

## Checking the preview

Use the normal example above, a blank account, missing/blank order numbers, and malformed JSON. For recorded results, exact commands, and browser Network instructions, see the [verification record](docs/verification.md).

## Editing and troubleshooting

| Change or problem | What to do |
| --- | --- |
| Changed `server.cjs` | Stop and restart Node. It does not automatically reload this server code. |
| Changed `index.html` | Refresh the page. |
| Changed `sample-order.json` | Save valid JSON, then refresh the page. The running server reads the file again for each sample request. |
| Changed the browser's editable box | Click Preview to send those edits. They are not saved back to the file. Refreshing reloads the saved sample. |
| `Route not found` for the sample file after adding its route | Restart the server from this project folder, then refresh. This occurred during the exercise and was resolved by restarting Node. |
| Port 7071 is already in use | Check the other local server using it. Relay's Functions server also uses 7071; run one at a time. |
| Sample cannot load | Confirm `sample-order.json` is beside `server.cjs` and contains valid JSON. A missing or invalid sample file returns **500** from the sample route. |
| Page cannot reach the API | Confirm Node is running and open the page through `http://127.0.0.1:7071`. |

Use only fictional input. The server reads the HTML, sample file, and incoming request; it writes HTTP responses only. The browser updates the page without writing order records or browser storage.

## Azure and GitHub releases

The deployed page and Python API run together in the Free Static Web App. Follow the [CI/CD guide](docs/ci-cd.md) for the exact build folders, required checks, Kit's review/approval, and live verification. The [project guidance](AGENTS.md) defines the working rules. A task-branch push runs checks; deployment follows a merge to `main` and Kit's deployment approval.
