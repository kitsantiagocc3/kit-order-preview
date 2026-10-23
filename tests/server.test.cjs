/*
Functions: startServer, preview
Purpose: Check the local server's routes, preview rules, and safe page output.
Author: Kit Nicholas Santiago
Date: 2026-10-23
Environment: Node.js test runner; starts server.cjs on 127.0.0.1:7181
Trigger: node --test tests/server.test.cjs (locally or in GitHub Actions)
Inputs: tests/preview-cases.json and both index.html pages
Reads: HTTP responses from the local test server
Writes: Test results only; no files or records
Rules: Fictional data only; no calls outside 127.0.0.1
Dependencies: Node.js built-ins: node:test, node:assert, child_process, fs, path
Changes: Initial automated checks
*/

const test = require("node:test");
const assert = require("node:assert/strict");
const { spawn } = require("node:child_process");
const { readFileSync } = require("node:fs");
const path = require("node:path");

// A different port from 7071, so a server you left running doesn't block the tests.
const PORT = 7181;
const BASE_URL = "http://127.0.0.1:" + PORT;
const ROOT = path.join(__dirname, "..");
const cases = JSON.parse(
  readFileSync(path.join(__dirname, "preview-cases.json"), "utf8")
);

let server;

function startServer() {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ["server.cjs"], {
      cwd: ROOT,
      env: { ...process.env, PORT: String(PORT) }
    });

    let errors = "";
    child.stderr.on("data", (chunk) => {
      errors += chunk;
    });
    child.stdout.on("data", (chunk) => {
      if (String(chunk).includes("Open http://")) {
        resolve(child);
      }
    });
    child.on("exit", (code) => {
      reject(new Error("server.cjs stopped (exit " + code + "): " + errors));
    });
  });
}

async function preview(body) {
  const response = await fetch(BASE_URL + "/api/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body
  });
  return { status: response.status, body: await response.json() };
}

test.before(async () => {
  server = await startServer();
}, { timeout: 10000 });

test.after(() => {
  server?.kill();
});

for (const item of cases) {
  test("preview: " + item.name, async () => {
    const result = await preview(item.body);
    assert.equal(result.status, item.status);
    assert.deepEqual(result.body, item.response);
  });
}

test("page: GET / returns the order preview page", async () => {
  const response = await fetch(BASE_URL + "/");
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type"), /text\/html/);
  assert.match(await response.text(), /id="preview-button"/);
});

test("sample: GET /sample-order.json returns valid JSON", async () => {
  const response = await fetch(BASE_URL + "/sample-order.json");
  assert.equal(response.status, 200);
  const sample = await response.json();
  assert.equal(typeof sample.orderNumber, "string");
});

test("routes: GET /api/preview returns 405 and allows POST", async () => {
  const response = await fetch(BASE_URL + "/api/preview");
  assert.equal(response.status, 405);
  assert.equal(response.headers.get("allow"), "POST");
});

test("routes: an unknown path returns 404", async () => {
  const response = await fetch(BASE_URL + "/not-a-page");
  assert.equal(response.status, 404);
});

// Order text must never be treated as HTML, or a crafted order could run script on the page.
for (const page of ["index.html", "azure-candidate/public/index.html"]) {
  test("page safety: " + page + " shows results with textContent only", () => {
    const html = readFileSync(path.join(ROOT, page), "utf8");
    assert.match(html, /output\.textContent\s*=/);
    assert.doesNotMatch(
      html,
      /innerHTML|outerHTML|insertAdjacentHTML|document\.write/
    );
  });
}
