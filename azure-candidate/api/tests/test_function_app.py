"""
Functions: PreviewCaseTests
Purpose: Check the Azure Functions preview against the shared preview cases.
Author: Kit Nicholas Santiago
Date: 2026-10-23
Environment: Python 3.11; runs locally or in GitHub Actions without Azure
Trigger: python -m unittest discover -s tests (from azure-candidate/api)
Inputs: tests/preview-cases.json at the repository root
Reads: The shared cases file only
Writes: Test results only; no files or records
Rules: Same cases as the local Node server; submitted is always false
Dependencies: azure-functions and Python's built-in json, pathlib, unittest
Changes: Initial automated checks
"""

import json
import unittest
from pathlib import Path

import azure.functions as func

from function_app import preview

CASES_PATH = Path(__file__).resolve().parents[3] / "tests" / "preview-cases.json"
CASES = json.loads(CASES_PATH.read_text(encoding="utf-8"))

# The decorators wrap the function; build() gives back the plain handler to call directly.
handler = preview.build().get_user_function()


class PreviewCaseTests(unittest.TestCase):
    def test_shared_cases(self):
        for case in CASES:
            with self.subTest(case["name"]):
                request = func.HttpRequest(
                    method="POST",
                    url="/api/preview",
                    headers={"Content-Type": "application/json"},
                    body=case["body"].encode("utf-8"),
                )
                response = handler(request)
                self.assertEqual(response.status_code, case["status"])
                self.assertEqual(json.loads(response.get_body()), case["response"])


if __name__ == "__main__":
    unittest.main()
