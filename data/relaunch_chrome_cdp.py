"""Restart Chrome on a copy of the logged-in profile so CDP works.

Chrome refuses --remote-debugging-port on the default User Data folder.
This copies cookies/session files into a custom profile, then relaunches.
The original Chrome window must close first so those files unlock.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

HOME = Path.home()
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
SRC_ROOT = HOME / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
SRC_DEFAULT = SRC_ROOT / "Default"
DST_ROOT = Path(__file__).resolve().parents[1] / ".chrome-cdp"
DST_DEFAULT = DST_ROOT / "Default"
CDP = "http://127.0.0.1:9222/json/version"

SKIP_DIRS = {
    "Cache",
    "Code Cache",
    "GPUCache",
    "GrShaderCache",
    "ShaderCache",
    "DawnCache",
    "Service Worker",
    "optimization_guide_hint_cache_store",
    "optimization_guide_model_store",
    "JumpListIconsMostVisited",
    "JumpListIconsRecentClosed",
}


def cdp_ready() -> dict | None:
    try:
        with urllib.request.urlopen(CDP, timeout=2) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def close_chrome() -> None:
    subprocess.run(
        ["taskkill", "/IM", "chrome.exe"],
        capture_output=True,
        text=True,
        check=False,
    )
    for _ in range(20):
        time.sleep(0.5)
        running = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq chrome.exe"],
            capture_output=True,
            text=True,
            check=False,
        )
        if "chrome.exe" not in running.stdout.lower():
            return
    subprocess.run(
        ["taskkill", "/IM", "chrome.exe", "/F"],
        capture_output=True,
        text=True,
        check=False,
    )
    time.sleep(2)


def copy_profile() -> None:
    DST_ROOT.mkdir(parents=True, exist_ok=True)
    local_state = SRC_ROOT / "Local State"
    if local_state.exists():
        shutil.copy2(local_state, DST_ROOT / "Local State")
    DST_DEFAULT.mkdir(parents=True, exist_ok=True)
    for item in SRC_DEFAULT.iterdir():
        if item.name in SKIP_DIRS:
            continue
        dest = DST_DEFAULT / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)


def launch() -> None:
    args = [
        str(CHROME),
        "--remote-debugging-port=9222",
        "--remote-allow-origins=*",
        f"--user-data-dir={DST_ROOT}",
        "--profile-directory=Default",
        "--no-first-run",
        "--no-default-browser-check",
        "https://www.newspapers.com/",
    ]
    print("launching", json.dumps(args))
    subprocess.Popen(args)


def main() -> int:
    print(f"home={HOME}")
    print(f"src={SRC_DEFAULT} exists={SRC_DEFAULT.exists()}")
    print(f"dst={DST_ROOT}")
    print("closing chrome so profile files unlock")
    close_chrome()
    print("copying logged-in profile into custom debug dir")
    copy_profile()
    launch()
    for i in range(30):
        time.sleep(1)
        info = cdp_ready()
        if info:
            print(json.dumps({"cdp": True, "attempt": i + 1, "info": info}, indent=2))
            return 0
        print(f"waiting for cdp {i + 1}")
    print(json.dumps({"cdp": False, "reason": "port 9222 never opened"}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
