"""
Functions: load_settings, authenticated, get_access_token, read_training_lead
Purpose: Read one configured fictional lead from the Zoho CRM sandbox.
Author: Kit Nicholas Santiago
Date: 2026-10-23
Environment: Python 3.11; Static Web Apps managed API or local simulation
Trigger: Called by GET /api/zoho/training-lead
Inputs: Backend environment settings and the platform client principal
Reads: One sandbox Lead; id, First_Name, Last_Name, and Company only
Writes: OAuth refresh POST and CRM GET requests; no CRM records or credential logs
Rules: Sandbox host only; fixed lead ID; no redirects; filter response fields
Dependencies: Python standard library; existing sandbox OAuth authorization
Changes: Read backend OAuth settings; cache access tokens in memory and refresh them
"""

import base64
import binascii
import hashlib
import http.client
import json
import os
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field


SANDBOX_ORIGIN = "https://sandbox.zohoapis.com"
ACCOUNTS_ORIGIN = "https://accounts.zoho.com"
LEAD_FIELDS = ("id", "First_Name", "Last_Name", "Company")
TIMEOUT_SECONDS = 10
MAX_RESPONSE_BYTES = 512 * 1024


class ZohoError(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


class ZohoAuthorizationError(ZohoError):
    pass


@dataclass(frozen=True)
class Settings:
    lead_id: str
    client_id: str = field(repr=False)
    client_secret: str = field(repr=False)
    refresh_token: str = field(repr=False)
    origin: str = SANDBOX_ORIGIN
    accounts_origin: str = ACCOUNTS_ORIGIN
    simulation: bool = False


def load_settings(environ=None):
    settings = os.environ if environ is None else environ
    lead_id = settings.get("ZOHO_TRAINING_LEAD_ID", "").strip()
    credentials = [settings.get(name, "").strip() for name in
                   ("ZOHO_CLIENT_ID", "ZOHO_CLIENT_SECRET", "ZOHO_REFRESH_TOKEN")]
    origin = settings.get("ZOHO_API_BASE_URL", SANDBOX_ORIGIN).rstrip("/")
    accounts_origin = settings.get("ZOHO_ACCOUNTS_URL", ACCOUNTS_ORIGIN).rstrip("/")
    simulation = origin != SANDBOX_ORIGIN or accounts_origin != ACCOUNTS_ORIGIN
    valid_id = lead_id.isascii() and lead_id.isdigit() and len(lead_id) <= 25
    valid_credentials = all(value and value.isascii() and not any(c.isspace() for c in value)
                            for value in credentials)
    if not valid_id or not valid_credentials:
        raise ZohoError("The Zoho sandbox connection is not configured.", 503)

    if simulation:
        def loopback(value, path):
            try:
                parsed = urllib.parse.urlsplit(value)
                port = parsed.port
            except ValueError:
                return False
            return (parsed.scheme == "http" and parsed.hostname == "127.0.0.1"
                    and port is not None and parsed.path == path
                    and not parsed.username and not parsed.password
                    and not parsed.query and not parsed.fragment)
        local_only = (
            settings.get("ZOHO_LOCAL_SIMULATION") == "1"
            and not settings.get("WEBSITE_INSTANCE_ID")
            and not settings.get("WEBSITE_SITE_NAME")
            and loopback(origin, "/zoho")
            and loopback(accounts_origin, "/zoho-accounts")
            and credentials == ["training-simulation-client", "training-simulation-secret",
                                "training-simulation-refresh"]
        )
        if not local_only:
            raise ZohoError("The Zoho sandbox connection is not configured.", 503)

    return Settings(lead_id, *credentials, origin, accounts_origin, simulation)


def authenticated(encoded_principal):
    """The managed Static Web Apps platform supplies this header after sign-in."""
    try:
        principal = json.loads(base64.b64decode(encoded_principal, validate=True))
        return (
            isinstance(principal, dict)
            and isinstance(principal.get("userRoles"), list)
            and "authenticated" in principal["userRoles"]
            and isinstance(principal.get("userId"), str)
            and bool(principal["userId"])
        )
    except (ValueError, TypeError, binascii.Error, UnicodeError):
        return False


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_token_lock = threading.Lock()
_token_cache = None


def get_access_token(settings, force=False):
    """Keep the short-lived access token in this worker's memory only."""
    global _token_cache
    key = hashlib.sha256(json.dumps([
        settings.accounts_origin, settings.origin, settings.client_id,
        settings.client_secret, settings.refresh_token,
    ]).encode()).digest()
    with _token_lock:
        if not force and _token_cache and _token_cache[0] == key and time.monotonic() < _token_cache[2]:
            return _token_cache[1]
        _token_cache = None
        body = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "refresh_token": settings.refresh_token,
        }).encode()
        request = urllib.request.Request(settings.accounts_origin + "/oauth/v2/token",
                                         data=body, method="POST", headers={
                                             "Content-Type": "application/x-www-form-urlencoded",
                                             "Accept": "application/json",
                                         })
        try:
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=TIMEOUT_SECONDS) as response:
                raw = response.read(65537)
                if response.status != 200 or len(raw) > 65536:
                    raise ZohoError("Zoho sandbox authorization needs attention.")
                payload = json.loads(raw)
            token = payload.get("access_token") if isinstance(payload, dict) else None
            ttl = payload.get("expires_in") if isinstance(payload, dict) else None
            if (not isinstance(token, str) or not token or not token.isascii()
                    or any(c.isspace() for c in token)
                    or type(ttl) not in (int, float) or not 0 < ttl <= 86400):
                raise ZohoError("Zoho sandbox authorization needs attention.")
        except urllib.error.HTTPError as error:
            error.close()
            raise ZohoError("Zoho sandbox authorization needs attention.") from None
        except (TimeoutError, socket.timeout):
            raise ZohoError("Zoho authorization did not respond in time.", 504) from None
        except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError, UnicodeError):
            raise ZohoError("Zoho sandbox authorization needs attention.") from None
        _token_cache = (key, token, time.monotonic() + max(0, ttl - 60))
        return token


def read_training_lead(settings):
    token = get_access_token(settings)
    try:
        return _read_lead(settings, token)
    except ZohoAuthorizationError:
        return _read_lead(settings, get_access_token(settings, force=True))


def _read_lead(settings, token):
    query = urllib.parse.urlencode({"fields": ",".join(LEAD_FIELDS[1:])})
    url = settings.origin + "/crm/v8/Leads/" + settings.lead_id + "?" + query
    request = urllib.request.Request(url, headers={
        "Authorization": "Zoho-oauthtoken " + token,
        "Accept": "application/json",
    }, method="GET")
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status == 204:
                raise ZohoError("The configured training lead was not found.", 404)
            if response.status != 200:
                raise ZohoError("Zoho returned an unexpected response.")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ZohoError("Zoho returned an unexpected response.")
            payload = json.loads(raw)
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        if status == 401:
            raise ZohoAuthorizationError("Zoho sandbox authorization needs attention.") from None
        if status == 403:
            raise ZohoError("Zoho sandbox authorization needs attention.") from None
        if status == 404:
            raise ZohoError("The configured training lead was not found.", 404) from None
        if status == 429:
            raise ZohoError("Zoho is temporarily busy. Try again later.", 503) from None
        raise ZohoError("Zoho returned an unexpected response.") from None
    except (TimeoutError, socket.timeout):
        raise ZohoError("Zoho did not respond in time.", 504) from None
    except urllib.error.URLError as error:
        if isinstance(error.reason, (TimeoutError, socket.timeout)):
            raise ZohoError("Zoho did not respond in time.", 504) from None
        raise ZohoError("Could not reach the Zoho sandbox.") from None
    except (ValueError, UnicodeError):
        raise ZohoError("Zoho returned an unexpected response.") from None
    except (http.client.HTTPException, OSError):
        raise ZohoError("Could not reach the Zoho sandbox.") from None

    records = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(records, list) or len(records) != 1:
        raise ZohoError("Zoho returned an unexpected response.")
    record = records[0]
    if not isinstance(record, dict) or record.get("id") != settings.lead_id:
        raise ZohoError("Zoho returned an unexpected response.")
    if any(record.get(key) is not None and not isinstance(record.get(key), str)
           for key in LEAD_FIELDS):
        raise ZohoError("Zoho returned an unexpected response.")
    return {key: record.get(key) for key in LEAD_FIELDS}
