"""
Functions: json_response, preview, training_lead
Purpose: Return fictional order previews and read one configured sandbox lead.
Author: Kit Nicholas Santiago
Date: 2026-10-23
Environment: Python 3.11; local Azure Functions candidate
Trigger: POST /api/preview; GET /api/zoho/training-lead
Inputs: Preview JSON; platform identity; backend Zoho settings
Reads: Preview request or one configured fictional Zoho sandbox lead
Writes: HTTP responses, OAuth refresh POST, and Zoho GET; no files or CRM record changes
Rules: Clean the order number; signed-in CRM reads; submitted is always false
Dependencies: azure-functions, json, and zoho_sandbox
Changes: Add the first read-only sandbox integration
"""

import json

import azure.functions as func

from zoho_sandbox import ZohoError, authenticated, load_settings, read_training_lead

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.function_name(name="training_lead")
@app.route(route="zoho/training-lead", methods=["GET"])
def training_lead(req: func.HttpRequest) -> func.HttpResponse:
    if not authenticated(req.headers.get("x-ms-client-principal", "")):
        return json_response({"error": "Sign in to load the training lead."}, 401)
    if req.params:
        return json_response({"error": "This route reads the configured training lead."}, 400)
    try:
        settings = load_settings()
        lead = read_training_lead(settings)
    except ZohoError as error:
        return json_response({"error": str(error)}, error.status)
    return json_response({
        "source": "local-simulation" if settings.simulation else "zoho-sandbox",
        "module": "Leads",
        "record": lead,
        "mode": "training-preview",
        "submitted": False,
    }, 200)


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
