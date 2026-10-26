"""
Functions: ZohoSandboxTests
Purpose: Check identity and configuration boundaries without calling CRM.
Author: Kit Nicholas Santiago
Date: 2026-10-23
Environment: Python 3.11 unittest
Trigger: Existing unittest discovery
Inputs: Synthetic identities and configuration dictionaries
Reads: Python handler results only
Writes: Test output only; no network, records, or files
Rules: No real credentials; allow only sandbox or explicit local simulation
Dependencies: Existing azure-functions dependency and unittest
Changes: Add checks for the first Zoho read route
"""

import base64
import json
import unittest
from unittest.mock import patch

import azure.functions as func

from function_app import training_lead
from zoho_sandbox import SANDBOX_ORIGIN, ZohoError, authenticated, load_settings


def principal(roles=None):
    value = {"userId": "fictional-trainee", "userRoles": roles or ["authenticated"]}
    return base64.b64encode(json.dumps(value).encode()).decode()


def configuration(**overrides):
    return {"ZOHO_TRAINING_LEAD_ID": "9001", "ZOHO_CLIENT_ID": "placeholder-client",
            "ZOHO_CLIENT_SECRET": "placeholder-secret", "ZOHO_REFRESH_TOKEN": "placeholder-refresh",
            **overrides}


class ZohoSandboxTests(unittest.TestCase):
    def test_identity_is_required_before_configuration_or_crm_access(self):
        for identity in ("", "bad-base64", principal(["anonymous"])):
            with self.subTest(identity=identity):
                request = func.HttpRequest("GET", "http://localhost/api/zoho/training-lead",
                                           headers={"x-ms-client-principal": identity}, body=b"")
                self.assertEqual(training_lead(request).status_code, 401)

    def test_queries_cannot_select_a_different_record(self):
        request = func.HttpRequest("GET", "http://localhost/api/zoho/training-lead",
                                   headers={"x-ms-client-principal": principal()},
                                   params={"recordId": "9999"}, body=b"")
        self.assertEqual(training_lead(request).status_code, 400)

    def test_unconfigured_connection_has_a_safe_response(self):
        request = func.HttpRequest("GET", "http://localhost/api/zoho/training-lead",
                                   headers={"x-ms-client-principal": principal()}, body=b"")
        with patch.dict("os.environ", {}, clear=True):
            response = training_lead(request)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(json.loads(response.get_body()), {
            "error": "The Zoho sandbox connection is not configured."
        })

    def test_sandbox_is_the_default(self):
        settings = load_settings(configuration())
        self.assertEqual(settings.origin, SANDBOX_ORIGIN)
        self.assertNotIn("placeholder", repr(settings))

    def test_production_and_arbitrary_hosts_are_rejected(self):
        for origin in ("https://www.zohoapis.com", "https://example.invalid",
                       "http://127.0.0.1:4901/zoho"):
            with self.subTest(origin=origin), self.assertRaises(ZohoError):
                load_settings(configuration(ZOHO_API_BASE_URL=origin))

    def test_local_simulation_rejects_real_credentials_and_cloud_runtime(self):
        base = {"ZOHO_TRAINING_LEAD_ID": "9001", "ZOHO_CLIENT_ID": "training-simulation-client",
                "ZOHO_CLIENT_SECRET": "training-simulation-secret", "ZOHO_REFRESH_TOKEN": "training-simulation-refresh",
                "ZOHO_ACCOUNTS_URL": "http://127.0.0.1:4901/zoho-accounts",
                "ZOHO_API_BASE_URL": "http://127.0.0.1:4901/zoho", "ZOHO_LOCAL_SIMULATION": "1"}
        self.assertTrue(load_settings(base).simulation)
        for extra in ({"ZOHO_CLIENT_SECRET": "placeholder"}, {"WEBSITE_INSTANCE_ID": "sample"},
                      {"ZOHO_API_BASE_URL": "http://127.0.0.1:4901/zoho?other=1"}):
            with self.subTest(extra=extra), self.assertRaises(ZohoError):
                load_settings({**base, **extra})

    def test_invalid_ids_and_header_values_are_rejected(self):
        for values in ({"ZOHO_TRAINING_LEAD_ID": "../Accounts"},
                       {"ZOHO_CLIENT_SECRET": "header\r\ninjection"}):
            with self.subTest(values=values), self.assertRaises(ZohoError):
                load_settings(configuration(**values))

    def test_accounts_host_cannot_be_changed_to_an_arbitrary_service(self):
        with self.assertRaises(ZohoError):
            load_settings(configuration(ZOHO_ACCOUNTS_URL="https://example.invalid"))


if __name__ == "__main__":
    unittest.main()
