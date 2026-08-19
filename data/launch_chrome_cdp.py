"""Launch Chrome with this machine's real profile and CDP enabled.

The Windows user is 'Joe Amditis' (space included). Paths must be passed
as a process argument list so the space is not split.
"""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path
from subprocess import Popen

USERPROFILE = Path.home()
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
USER_DATA = USERPROFILE / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
CDP = "http://127.0.0.1:9222/json/version"


def cdp_ready() -> bool:
    try:
        with urllib.request.urlopen(CDP, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def main() -> int:
    print(f"home={USERPROFILE}")
    print(f"chrome_exists={CHROME.exists()}")
    print(f"user_data={USER_DATA}")
    print(f"user_data_exists={USER_DATA.exists()}")
    if cdp_ready():
        print("cdp already up")
        return 0
    if not CHROME.exists():
        print("chrome not found")
        return 1
    args = [
        str(CHROME),
        "--remote-debugging-port=9222",
        "--remote-allow-origins=*",
        f"--user-data-dir={USER_DATA}",
        "--profile-directory=Default",
        "--no-first-run",
        "--no-default-browser-check",
        "https://www.newspapers.com/",
    ]
    print("launching", json.dumps(args))
    Popen(args)
    for _ in range(20):
        time.sleep(1)
        if cdp_ready():
            print("cdp ready")
            return 0
    print("cdp did not come up")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
