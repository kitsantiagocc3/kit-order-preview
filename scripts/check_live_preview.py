"""
Functions: request, verify, main
Purpose: Verify the deployed training page and HTTP functions after deployment.
Author: Kit Nicholas Santiago
Date: 2026-10-23
Environment: Python 3.11; local or GitHub Actions
Trigger: python scripts/check_live_preview.py
Inputs: TRAINING_SITE_URL and shared preview/GET cases in tests/
Reads: Shared fictional cases; public training HTTP responses
Writes: Preview requests and check results only; no order records or files
Rules: Only the approved training hostname; complete expected JSON must match
Dependencies: Python standard library
Changes: Verify health and hello alongside the existing preview cases
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


TRAINING_HOST = "green-sea-04ba4b40f.1.azurestaticapps.net"
CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "preview-cases.json"
GET_CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "function-get-cases.json"


def request(base_url, route, body=None):
    headers = {"Content-Type": "application/json"} if body is not None else {}
    data = body.encode("utf-8") if body is not None else None
    outgoing = urllib.request.Request(base_url + route, data=data, headers=headers)
    try:
        response = urllib.request.urlopen(outgoing, timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.headers.get_content_type(), response.read().decode("utf-8")


def verify(base_url, cases, get_cases):
    status, content_type, page = request(base_url, "/")
    if status != 200 or content_type != "text/html" or 'id="preview-button"' not in page:
        raise AssertionError("The live training page did not return the expected HTML")

    status, _, sample = request(base_url, "/sample-order.json")
    parsed_sample = json.loads(sample)
    if status != 200 or not isinstance(parsed_sample, dict) or not isinstance(parsed_sample.get("orderNumber"), str):
        raise AssertionError("The live sample did not return an order JSON object")

    for case in get_cases:
        status, content_type, body = request(base_url, case["path"])
        if status != case["status"] or content_type != "application/json" or json.loads(body) != case["response"]:
            raise AssertionError("Live GET function failed: " + case["name"])

    for case in cases:
        status, content_type, body = request(base_url, "/api/preview", case["body"])
        if status != case["status"] or content_type != "application/json" or json.loads(body) != case["response"]:
            raise AssertionError("Live preview failed: " + case["name"])


def main():
    raw_url = os.environ.get("TRAINING_SITE_URL", "")
    parsed = urllib.parse.urlsplit(raw_url)
    if (
        parsed.scheme != "https"
        or parsed.netloc != TRAINING_HOST
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        print("Set TRAINING_SITE_URL to the approved HTTPS training site URL.", file=sys.stderr)
        return 1

    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    get_cases = json.loads(GET_CASES_PATH.read_text(encoding="utf-8"))
    base_url = "https://" + TRAINING_HOST
    for attempt in range(1, 4):
        try:
            verify(base_url, cases, get_cases)
            print(f"Passed: page, sample, {len(cases)} preview cases, and {len(get_cases)} GET function cases.")
            return 0
        except (AssertionError, urllib.error.URLError, TimeoutError, ValueError) as error:
            print(f"Live verification attempt {attempt}/3 failed: {error}", file=sys.stderr)
            if attempt < 3:
                time.sleep(5)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
