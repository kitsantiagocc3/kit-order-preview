/*
Function: trainingZohoMock
Purpose: Serve the documented Zoho single-record envelope for local checks.
Author: Kit Nicholas Santiago
Date: 2026-10-23
Environment: Local Postman simulation; Node built-in modules
Trigger: Fictional GET requests from the real Python client
Inputs: Synthetic record ID and requested field names
Reads: Request path and synthetic authorization header
Writes: HTTP responses only; no CRM calls, files, or credential logs
Rules: Synthetic data only; unmodeled routes return 501
Dependencies: Node http; Zoho V8 Get Records contract
Changes: Model success, absent records, authorization, rate limits, and bad responses
*/
const http = require("node:http");

http.createServer(function trainingZohoMock(request, response) {
  const url = new URL(request.url, "http://127.0.0.1");
  const match = /^\/crm\/v8\/Leads\/(900[1-8])$/.exec(url.pathname);
  const send = (status, value) => {
    response.writeHead(status, { "Content-Type": "application/json" });
    response.end(JSON.stringify(value));
  };
  if (request.method !== "GET" || !match) {
    send(501, { code: "UNMODELED_ROUTE" });
    return;
  }
  if (request.headers.authorization !== "Zoho-oauthtoken training-simulation-only") {
    send(401, { code: "INVALID_TOKEN", message: "Synthetic authorization rejected" });
    return;
  }
  const fields = (url.searchParams.get("fields") || "").split(",").sort();
  if (JSON.stringify(fields) !== JSON.stringify(["Company", "First_Name", "Last_Name"])) {
    send(400, { code: "INVALID_DATA", message: "Expected the selected lead fields" });
    return;
  }
  const id = match[1];
  if (id === "9002") { response.writeHead(204); response.end(); return; }
  if (id === "9003") { send(401, { code: "INVALID_TOKEN" }); return; }
  if (id === "9004") { send(429, { code: "TOO_MANY_REQUESTS" }); return; }
  if (id === "9005") {
    response.writeHead(200, { "Content-Type": "application/json" });
    response.end("invalid-json");
    return;
  }
  if (id === "9006") {
    response.writeHead(302, { Location: "/must-not-follow" });
    response.end();
    return;
  }
  if (id === "9008") { send(503, { code: "SERVICE_UNAVAILABLE" }); return; }
  send(200, { data: [{
    id: id === "9007" ? "9999" : id,
    First_Name: "Alex",
    Last_Name: "Training",
    Company: "Acorn Training",
    Email: "not-for-the-page@example.invalid",
    Owner: { name: "Unreturned sample owner" }
  }] });
}).listen(process.env.PORT);
