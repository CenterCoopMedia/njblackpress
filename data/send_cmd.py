"""Send one command to the long-lived browser daemon and wait for the result."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"
CMD = OUT / "cmd.json"
RESULT = OUT / "cmd-result.json"


def send(payload: dict, timeout: float = 90) -> dict:
    before = RESULT.stat().st_mtime if RESULT.exists() else 0
    CMD.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.3)
        if not RESULT.exists():
            continue
        if RESULT.stat().st_mtime <= before:
            continue
        return json.loads(RESULT.read_text(encoding="utf-8"))
    return {"ok": False, "error": "timeout waiting for daemon"}


if __name__ == "__main__":
    action = sys.argv[1]
    args = {}
    if len(sys.argv) > 2:
        args = json.loads(sys.argv[2])
    args["action"] = action
    print(json.dumps(send(args), indent=2, ensure_ascii=False))
