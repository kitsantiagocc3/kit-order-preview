"""
Functions: json_response, preview
Purpose: Return fictional order previews through an Azure HTTP trigger.
Author: Kit Nicholas Santiago
Date: 2026-10-23
Environment: Python 3.11; local Azure Functions candidate
Trigger: POST /api/preview
Inputs: JSON with id, orderNumber, and optional Account_Name.name
Reads: HTTP request body only
Writes: HTTP responses only; no files or records
Rules: Clean the order number; submitted is always false
Dependencies: azure-functions and Python's built-in json module
Changes: Initial Azure candidate matching the local preview rules
"""

import json

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def json_response(data: dict, status: int) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(data),
        status_code=status,
        mimetype="application/json",
        charset="utf-8",
        headers={"Cache-Control": "no-store"},
    )


@app.function_name(name="preview")
@app.route(route="preview", methods=["POST"])
def preview(req: func.HttpRequest) -> func.HttpResponse:
    try:
        order = req.get_json()
    except ValueError:
        return json_response(
            {"error": "Invalid JSON. Check your quotes, commas, and braces."},
            400,
        )

    if not isinstance(order, dict):
        return json_response(
            {"error": "Send a JSON object containing an orderNumber."},
            400,
        )

    raw_number = order.get("orderNumber")
    if not isinstance(raw_number, str) or not raw_number.strip():
        return json_response({"error": "Order number needed"}, 400)

    order_number = raw_number.strip().upper()

    account = order.get("Account_Name")
    raw_name = account.get("name") if isinstance(account, dict) else ""
    account_name = raw_name.strip() if isinstance(raw_name, str) else ""

    description = "Order " + order_number
    if account_name:
        description += " - " + account_name

    result = {}
    if "id" in order:
        result["id"] = order["id"]
    result.update({
        "orderNumber": order_number,
        "description": description,
        "mode": "training-preview",
        "submitted": False,
    })

    return json_response(result, 200)