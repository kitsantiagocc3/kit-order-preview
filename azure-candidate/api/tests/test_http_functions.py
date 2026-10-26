"""
Functions: HttpFunctionCaseTests
Purpose: Check HTTP learning functions against shared fictional GET examples.
Author: Kit Nicholas Santiago
Date: 2026-10-23
Environment: Python 3.11; local checks and GitHub CI
Trigger: python -m unittest discover -s tests -v
Inputs: tests/function-get-cases.json at the repository root
Reads: Shared fixtures and HTTP query/path values only
Writes: Test results only; no records or network requests
Rules: Exact status/JSON; training mode; submitted remains false
Dependencies: azure-functions and Python standard library
Changes: Cover health, hello, and lesson lookup including missing lessons
"""

import json
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import azure.functions as func

from function_app import health, hello, lesson


CASES_PATH = Path(__file__).resolve().parents[3] / "tests" / "function-get-cases.json"
CASES = json.loads(CASES_PATH.read_text(encoding="utf-8"))
HANDLERS = {
    "health": health.build().get_user_function(),
    "hello": hello.build().get_user_function(),
    "lesson": lesson.build().get_user_function(),
}


class HttpFunctionCaseTests(unittest.TestCase):
    def test_shared_get_cases(self):
        for case in CASES:
            with self.subTest(case["name"]):
                query = parse_qs(urlsplit(case["path"]).query, keep_blank_values=True)
                request = func.HttpRequest(
                    method="GET",
                    url=case["path"],
                    params={key: values[-1] for key, values in query.items()},
                    route_params=case.get("route_params", {}),
                    body=b"",
                )
                response = HANDLERS[case["function"]](request)
                self.assertEqual(response.status_code, case["status"])
                self.assertEqual(json.loads(response.get_body()), case["response"])


if __name__ == "__main__":
    unittest.main()
