/*
Functions: sendJson, handleRequest
Purpose: Serve the page and return fictional order previews.
Author: Kit Nicholas Santiago
Date: 2026-10-23
Environment: Local Node.js; 127.0.0.1:7071
Trigger: HTTP requests
Inputs: Request method, path, and JSON body
Reads: index.html, sample-order.json, and the request body
Writes: HTTP responses only; no files or records
Rules: Preview only; submitted is always false
Dependencies: Node.js built-ins: http, fs/promises, path
Changes: Load sample-order.json; allow a separate test port through PORT
*/

const http = require("node:http");
const { readFile } = require("node:fs/promises");
const path = require("node:path");

const HOST = "127.0.0.1";
const PORT = Number(process.env.PORT) || 7071;
const pagePath = path.join(__dirname, "index.html");
const samplePath = path.join(__dirname, "sample-order.json");

function sendJson(response, status, data) {
  response.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store"
  });
  response.end(JSON.stringify(data));
}

async function handleRequest(request, response) {
  try {
    const pathname = request.url.split("?")[0];

    if (
      request.method === "GET" &&
      (pathname === "/" || pathname === "/index.html")
    ) {
      const page = await readFile(pagePath, "utf8");
      response.writeHead(200, {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "no-store"
      });
      return response.end(page);
    }

    if (request.method === "GET" && pathname === "/sample-order.json") {
      try {
        const sample = JSON.parse(await readFile(samplePath, "utf8"));
        return sendJson(response, 200, sample);
      } catch {
        return sendJson(response, 500, {
          error: "Could not load sample-order.json. Check that it exists and contains valid JSON."
        });
      }
    }

    if (pathname !== "/api/preview") {
      return sendJson(response, 404, { error: "Route not found" });
    }

    if (request.method !== "POST") {
      response.setHeader("Allow", "POST");
      return sendJson(response, 405, { error: "Use POST /api/preview" });
    }

    let body = "";
    request.setEncoding("utf8");
    for await (const chunk of request) {
      body += chunk;
    }

    let order;
    try {
      order = JSON.parse(body);
    } catch {
      return sendJson(response, 400, {
        error: "Invalid JSON. Check your quotes, commas, and braces."
      });
    }

    if (!order || typeof order !== "object" || Array.isArray(order)) {
      return sendJson(response, 400, {
        error: "Send a JSON object containing an orderNumber."
      });
    }

    if (
      typeof order.orderNumber !== "string" ||
      !order.orderNumber.trim()
    ) {
      return sendJson(response, 400, { error: "Order number needed" });
    }

    const orderNumber = order.orderNumber.trim().toUpperCase();
    const accountName =
      typeof order.Account_Name?.name === "string"
        ? order.Account_Name.name.trim()
        : "";

    let description = "Order " + orderNumber;
    if (accountName) {
      description += " - " + accountName;
    }

    return sendJson(response, 200, {
      id: order.id,
      orderNumber,
      description,
      mode: "training-preview",
      submitted: false
    });
  } catch {
    if (!response.headersSent && !response.destroyed) {
      sendJson(response, 500, {
        error: "Local server error. Check that the project files are saved together."
      });
    }
  }
}

const server = http.createServer(handleRequest);

server.on("error", (error) => {
  console.error(
    error.code === "EADDRINUSE"
      ? "Port " + PORT + " is already in use. Check your other local servers."
      : "Could not start the local server: " + error.message
  );
  process.exitCode = 1;
});

server.listen(PORT, HOST, () => {
  console.log("Open http://" + HOST + ":" + PORT);
});
