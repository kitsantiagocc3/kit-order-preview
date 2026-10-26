"""
Functions: json_response, health, hello, lesson, preview
Purpose: Teach HTTP triggers and return fictional training responses.
Author: Kit Nicholas Santiago
Date: 2026-10-23
Environment: Python 3.11; local host and Static Web Apps managed API
Trigger: GET health/hello/lessons/{lesson_id}; POST /api/preview
Inputs: Optional name query parameter; lesson path ID; fictional preview JSON
Reads: HTTP query/path parameters, fixed lesson titles, and request body only
Writes: HTTP responses and fixed host-log messages only; no files or records
Rules: Clean the order number; submitted is always false
Dependencies: azure-functions and Python's built-in json and logging modules
Changes: Add HTTP lessons for status, query input, path input, and 404 responses
"""

import json
import logging

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


@app.function_name(name="health")
@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Training health HTTP trigger invoked")
    return json_response({
        "status": "ok",
        "service": "order-preview",
        "mode": "training-preview",
        "submitted": False,
    }, 200)


@app.function_name(name="hello")
@app.route(route="hello", methods=["GET"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Training hello HTTP trigger invoked")
    name = (req.params.get("name") or "").strip() or "trainee"
    return json_response({
        "message": "Hello, " + name + "!",
        "mode": "training-preview",
        "submitted": False,
    }, 200)


@app.function_name(name="lesson")
@app.route(route="lessons/{lesson_id}", methods=["GET"])
def lesson(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Training lesson HTTP trigger invoked")
    lesson_titles = {
        "http": "HTTP triggers",
        "validation": "Request validation",
    }
    lesson_id = req.route_params.get("lesson_id", "")
    title = lesson_titles.get(lesson_id)
    if title is None:
        return json_response({
            "error": "Lesson not found",
            "mode": "training-preview",
            "submitted": False,
        }, 404)

    return json_response({
        "lessonId": lesson_id,
        "title": title,
        "mode": "training-preview",
        "submitted": False,
    }, 200)


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
