/*
Function: trainingOAuthMock
Purpose: Model Zoho's documented refresh-token request for local HTTP checks.
Author: Kit Nicholas Santiago
Date: 2026-10-23
Environment: Local Postman simulation; Node built-in modules
Trigger: POST /oauth/v2/token with synthetic credentials only
Inputs: Synthetic form-urlencoded OAuth fields
Reads: Local request body
Writes: Synthetic token response only; no real service calls or credential logs
Rules: Validate the grant and fields; do not log request bodies
Dependencies: Node http; Zoho V8 refresh-token contract
Changes: Add OAuth as a separate simulation dependency
*/
const http = require("node:http");

http.createServer(function trainingOAuthMock(request, response) {
  const send = (status, value) => {
    response.writeHead(status, { "Content-Type": "application/json" });
    response.end(JSON.stringify(value));
  };
  if (request.method !== "POST" || request.url !== "/oauth/v2/token") {
    send(501, { error: "unmodeled_route" });
    return;
  }
  let body = "";
  request.on("data", chunk => { body += chunk; });
  request.on("end", () => {
    const form = new URLSearchParams(body);
    if (form.get("grant_type") !== "refresh_token"
        || form.get("client_id") !== "training-simulation-client"
        || form.get("client_secret") !== "training-simulation-secret"
        || form.get("refresh_token") !== "training-simulation-refresh") {
      send(200, { error: "invalid_client" });
      return;
    }
    send(200, { access_token: "training-simulation-only", expires_in: 3600,
      api_domain: "https://sandbox.zohoapis.com", token_type: "Bearer" });
  });
}).listen(process.env.PORT);
