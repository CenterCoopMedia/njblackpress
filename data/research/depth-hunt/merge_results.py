#!/usr/bin/env python3
"""Merge archival hunt batch and verdict files, generate findings report."""

import json
import os
from pathlib import Path
from datetime import date
from typing import Any

# Paths
DEPTH_HUNT_DIR = Path("C:/Users/Joe Amditis/Desktop/Crimes/playground/njblackpress/data/research/depth-hunt")
BATCHES_DIR = DEPTH_HUNT_DIR / "batches"
VERDICTS_DIR = DEPTH_HUNT_DIR / "verdicts"
FILES_DIR = DEPTH_HUNT_DIR / "files"

def read_json_files(directory: Path, pattern: str) -> dict[int, Any]:
    """Read all JSON files matching pattern from directory."""
    results = {}
    files = sorted(directory.glob(pattern))
    print(f"Found {len(files)} files matching {pattern}")

    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    pubId = item.get('pubId')
                    if pubId is not None:
                        results[pubId] = item
            print(f"  Loaded {filepath.name}: {len(data)} items")

    return results

def verify_file_exists(localFile: str | None) -> tuple[bool, str]:
    """Verify if a local file exists and is > 20 KB."""
    if not localFile:
        return False, "no file path provided"

    # Extract filename from path (handle both relative and full paths)
    filename = Path(localFile).name
    filepath = FILES_DIR / filename

    if not filepath.exists():
        return False, f"file not found: {filename}"

    size = filepath.stat().st_size
    if size < 20480:  # 20 KB
        return False, f"file too small ({size} bytes): {filename}"

    return True, ""

def main():
    print("Reading batch files...")
    batches = read_json_files(BATCHES_DIR, "batch-*.json")

    print("\nReading verdict files...")
    verdicts = read_json_files(VERDICTS_DIR, "verdict-*.json")

    print(f"\nBatch entries: {len(batches)}")
    print(f"Verdict entries: {len(verdicts)}")

    # Merge and categorize
    confirmed = []
    rejected = []
    none = []

    for pubId in sorted(batches.keys()):
        batch = batches[pubId]
        verdict = verdicts.get(pubId)

        # Start with batch data
        item = {**batch}

        # Merge verdict if available
        if verdict:
            item['verdict'] = verdict.get('verdict')
            item['verdictReason'] = verdict.get('reason')

        # Categorize based on result and verdict
        verdict_status = verdict.get('verdict') if verdict else batch.get('result')

        if verdict_status == "confirmed":
            # Verify file exists
            localFile = item.get('localFile')
            file_exists, err_msg = verify_file_exists(localFile)

            if file_exists:
                confirmed.append(item)
                print(f"✓ {pubId}: {item['name']}")
            else:
                # Demote to rejected
                item['verdict'] = "rejected"
                item['verdictReason'] = f"file missing: {err_msg}"
                rejected.append({
                    'pubId': pubId,
                    'name': item['name'],
                    'reason': err_msg
                })
                print(f"✗ {pubId}: {item['name']} - {err_msg}")

        elif verdict_status == "rejected" or batch.get('result') == "none":
            # Handle none results
            if batch.get('result') == "none":
                none.append({
                    'pubId': pubId,
                    'name': item['name']
                })
            else:
                rejected.append({
                    'pubId': pubId,
                    'name': item['name'],
                    'reason': verdict.get('reason') if verdict else item.get('notes', 'No verdict provided')
                })

    # Generate findings.json
    findings = {
        'generated': '2026-08-19',
        'pubsHunted': len(batches),
        'confirmedCount': len(confirmed),
        'rejectedCount': len(rejected),
        'noneCount': len(none),
        'confirmed': confirmed,
        'rejected': rejected,
        'none': none
    }

    findings_path = DEPTH_HUNT_DIR / "findings.json"
    with open(findings_path, 'w', encoding='utf-8') as f:
        json.dump(findings, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {findings_path}")
    print(f"  Confirmed: {len(confirmed)}")
    print(f"  Rejected: {len(rejected)}")
    print(f"  None: {len(none)}")

    # Generate SUMMARY.md
    summary_md = generate_summary(findings, confirmed, rejected, none)

    summary_path = DEPTH_HUNT_DIR / "SUMMARY.md"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_md)

    print(f"Wrote {summary_path}")

    return {
        'findings_file': str(findings_path),
        'summary_file': str(summary_path),
        'confirmed_count': len(confirmed),
        'none_count': len(none)
    }

def generate_summary(findings: dict, confirmed: list, rejected: list, none: list) -> str:
    """Generate SUMMARY.md report."""

    lines = [
        "# Archival hunt summary",
        "",
        "## Overview",
        "",
        f"Total publications hunted: {findings['pubsHunted']}",
        f"Confirmed finds: {findings['confirmedCount']}",
        f"Rejected results: {findings['rejectedCount']}",
        f"No results found: {findings['noneCount']}",
        "",
        "## Confirmed finds",
        "",
    ]

    if confirmed:
        # Add table header
        lines.append("| Publication | Source | Local file |")
        lines.append("|---|---|---|")

        # Add table rows
        for item in confirmed:
            pub_name = item.get('name', 'Unknown').replace('|', '\\|')
            source = item.get('source', 'Unknown').replace('|', '\\|') if item.get('source') else 'N/A'
            local_file = item.get('localFile', 'N/A').replace('|', '\\|') if item.get('localFile') else 'N/A'

            lines.append(f"| {pub_name} | {source} | {local_file} |")

        lines.append("")
    else:
        lines.append("No confirmed finds.\n")

    # Add none results section
    lines.append("## No results found")
    lines.append("")

    if none:
        lines.append("The following publications had no digitized sources located:")
        lines.append("")

        for item in none:
            lines.append(f"- {item['name']} (ID: {item['pubId']})")

        lines.append("")
    else:
        lines.append("No publications with zero results.\n")

    return "\n".join(lines)

if __name__ == "__main__":
    result = main()
    print(f"\nResults:")
    print(f"  Findings file: {result['findings_file']}")
    print(f"  Summary file: {result['summary_file']}")
    print(f"  Confirmed: {result['confirmed_count']}")
    print(f"  None: {result['none_count']}")
