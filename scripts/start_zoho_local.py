"""
Functions: main
Purpose: Start the existing Python Functions tools with approved process settings.
Author: Kit Nicholas Santiago
Date: 2026-10-23
Environment: Windows; Python 3.11; local training workspace
Trigger: Run this script from the Zoho task checkout
Inputs: Fictional lead ID, mode, port, and existing process OAuth settings
Reads: Process settings and the installed local Functions tools
Writes: Child-process settings and host output only; no credential files or records
Rules: Never prompt for or print credentials; sandbox or synthetic loopback only
Dependencies: Existing func-practice Python environment and azure-demo local tools
Changes: Use Python to respect Windows PowerShell script execution policy
"""

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Start the local Zoho training backend.")
    parser.add_argument("--mode", choices=("Sandbox", "Simulation"), default="Sandbox")
    parser.add_argument("--lead-id", default="")
    parser.add_argument("--port", type=int, default=7184)
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 11):
        parser.error("Use the existing Python 3.11 environment.")
    if not 1024 <= args.port <= 65535:
        parser.error("Choose a port from 1024 through 65535.")
    project = Path(__file__).resolve().parents[1]
    workspace = project.parent
    venv = workspace / "func-practice" / ".venv"
    functions_cli = workspace / "azure-demo" / "tools" / "node_modules" / ".bin" / "func.cmd"
    if not functions_cli.is_file() or not (venv / "Scripts" / "python.exe").is_file():
        parser.error("The existing Functions tools or Python environment were not found.")
    lead_id = args.lead_id or os.environ.get("ZOHO_TRAINING_LEAD_ID", "")
    if args.mode == "Simulation" and not lead_id:
        lead_id = "9001"
    if not re.fullmatch(r"[0-9]{1,25}", lead_id):
        parser.error("Supply the approved fictional lead ID.")
    required = ("ZOHO_CLIENT_ID", "ZOHO_CLIENT_SECRET", "ZOHO_REFRESH_TOKEN")
    if args.mode == "Sandbox" and any(not os.environ.get(name) for name in required):
        parser.error("Required Zoho OAuth settings are missing from this process. Use the approved local credential provider, then run again. Do not paste credentials into chat or files.")
    child_env = os.environ.copy()
    child_env.update({
        "VIRTUAL_ENV": str(venv),
        "PATH": str(venv / "Scripts") + os.pathsep + child_env.get("PATH", ""),
        "FUNCTIONS_WORKER_RUNTIME": "python",
        "ZOHO_TRAINING_LEAD_ID": lead_id,
    })
    if args.mode == "Simulation":
        child_env.update({
            "ZOHO_CLIENT_ID": "training-simulation-client",
            "ZOHO_CLIENT_SECRET": "training-simulation-secret",
            "ZOHO_REFRESH_TOKEN": "training-simulation-refresh",
            "ZOHO_ACCOUNTS_URL": "http://127.0.0.1:4901/zoho-accounts",
            "ZOHO_API_BASE_URL": "http://127.0.0.1:4901/zoho",
            "ZOHO_LOCAL_SIMULATION": "1",
        })
    else:
        child_env["ZOHO_API_BASE_URL"] = "https://sandbox.zohoapis.com"
        child_env["ZOHO_ACCOUNTS_URL"] = "https://accounts.zoho.com"
        child_env.pop("ZOHO_LOCAL_SIMULATION", None)
    print(f"Starting the local {args.mode} backend on port {args.port}.", flush=True)
    try:
        return subprocess.call([str(functions_cli), "start", "--port", str(args.port),
                                "--address", "127.0.0.1"],
                               cwd=project / "azure-candidate" / "api", env=child_env)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
