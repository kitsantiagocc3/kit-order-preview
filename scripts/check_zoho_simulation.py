"""
Functions: main
Purpose: Run the real Python handler and HTTP client against a local Zoho simulation.
Author: Kit Nicholas Santiago
Date: 2026-10-23
Environment: Python 3.11 with the existing azure-functions dependency
Trigger: Run after starting the documented Postman simulation on port 4901
Inputs: Fixed local simulation origin and synthetic record IDs
Reads: Local HTTP responses only
Writes: Synthetic local OAuth/GET requests and check output; no real CRM calls
Rules: No real credentials; compare status, selected fields, and safe errors
Dependencies: Existing API dependency; running local Postman simulation
Changes: Verify the new integration over HTTP without a live sandbox token
"""

import base64
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import azure.functions as func

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "azure-candidate" / "api"))
from function_app import training_lead
from zoho_sandbox import Settings, ZohoError, get_access_token


def main():
    identity = base64.b64encode(json.dumps({
        "userId": "fictional-trainee", "userRoles": ["authenticated"]
    }).encode()).decode()
    cases = [
        ("9001", 200, None),
        ("9002", 404, "The configured training lead was not found."),
        ("9003", 502, "Zoho sandbox authorization needs attention."),
        ("9004", 503, "Zoho is temporarily busy. Try again later."),
        ("9005", 502, "Zoho returned an unexpected response."),
        ("9006", 502, "Zoho returned an unexpected response."),
        ("9007", 502, "Zoho returned an unexpected response."),
        ("9008", 502, "Zoho returned an unexpected response."),
    ]
    for record_id, expected_status, error in cases:
        with patch.dict(os.environ, {
            "ZOHO_TRAINING_LEAD_ID": record_id,
            "ZOHO_CLIENT_ID": "training-simulation-client",
            "ZOHO_CLIENT_SECRET": "training-simulation-secret",
            "ZOHO_REFRESH_TOKEN": "training-simulation-refresh",
            "ZOHO_ACCOUNTS_URL": "http://127.0.0.1:4901/zoho-accounts",
            "ZOHO_API_BASE_URL": "http://127.0.0.1:4901/zoho",
            "ZOHO_LOCAL_SIMULATION": "1",
        }):
            request = func.HttpRequest("GET", "http://localhost/api/zoho/training-lead",
                                       headers={"x-ms-client-principal": identity}, body=b"")
            response = training_lead(request)
        assert response.status_code == expected_status, (record_id, response.status_code)
        assert response.headers["Cache-Control"] == "no-store"
        payload = json.loads(response.get_body())
        if error:
            assert payload == {"error": error}, (record_id, payload)
        else:
            assert payload == {
                "source": "local-simulation", "module": "Leads",
                "record": {"id": "9001", "First_Name": "Alex", "Last_Name": "Training", "Company": "Acorn Training"},
                "mode": "training-preview", "submitted": False,
            }, payload
        print("Passed: synthetic case", record_id, "HTTP", expected_status)
    invalid = Settings("9001", "invalid-simulation-client", "training-simulation-secret",
                       "training-simulation-refresh", "http://127.0.0.1:4901/zoho",
                       "http://127.0.0.1:4901/zoho-accounts", True)
    try:
        get_access_token(invalid)
    except ZohoError as error:
        assert error.status == 502 and str(error) == "Zoho sandbox authorization needs attention."
    else:
        raise AssertionError("A 200 OAuth error body was accepted as a token.")
    print("Passed: an HTTP 200 OAuth error body is rejected safely.")
    print("Passed: 8 record cases and 1 OAuth error case over local HTTP.")


if __name__ == "__main__":
    main()
