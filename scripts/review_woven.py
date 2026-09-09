"""Thin wrapper kept for the old command name.

The 3D exhibit this script used to check is gone; the history hall replaced
it. All of its still-relevant flat timeline, fallback, mobile, and context
loss checks now live in scripts/review_hall.py, which also carries the hall's
own checks. Run that directly, or run this: both check the same thing.

Run: python3 scripts/review_woven.py --output /tmp/woven-review
"""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--output', default='/tmp/woven-review')
args = parser.parse_args()

result = subprocess.run(
    [sys.executable, str(ROOT / 'scripts' / 'review_hall.py'), '--output', args.output])
raise SystemExit(result.returncode)
