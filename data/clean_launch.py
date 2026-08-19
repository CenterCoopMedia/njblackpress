"""Relaunch the CDP Chrome with the repo profile. Leaves Chrome running."""

from __future__ import annotations

import subprocess
import time
import urllib.request
from pathlib import Path

CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
PROFILE = Path(__file__).resolve().parents[1] / ".chrome-cdp"
CDP = "http://127.0.0.1:9222"


def cdp_ready() -> bool:
    try:
        with urllib.request.urlopen(CDP + "/json/version", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def main() -> None:
    if cdp_ready():
        print("chrome already up")
        return
    args = [
        str(CHROME),
        "--remote-debugging-port=9222",
        "--remote-allow-origins=*",
        f"--user-data-dir={PROFILE}",
        "--profile-directory=Default",
        "--no-first-run",
        "--no-default-browser-check",
        "--start-maximized",
        "https://www.newspapers.com/",
    ]
    subprocess.Popen(args)
    for i in range(40):
        time.sleep(1)
        if cdp_ready():
            print(f"cdp ready after {i + 1}s")
            return
    raise SystemExit("Chrome CDP did not come up")


if __name__ == "__main__":
    main()
