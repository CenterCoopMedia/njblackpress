#!/usr/bin/env python3
"""
Merge research findings into publications.json.
Reads JSON files from data/research/ and updates publications.json with new data.
Only fills in gaps - does not overwrite existing non-null values.
"""

import json
import os
import glob

PUBLICATIONS_PATH = 'publications.json'
FEATURED_PATH = 'featured-publications.json'
RESEARCH_DIR = 'research'

def merge_publication(existing, research):
    """Merge research data into existing publication, filling gaps only."""
    updated = dict(existing)
    fields_updated = []

    # Fields that can be filled from research
    fillable_fields = [
        'archiveUrl', 'websiteUrl', 'missionStatement', 'historicalNotes',
        'primaryFocus', 'targetAudience', 'keyStaff', 'alternateName',
        'frequency', 'format', 'languages'
    ]

    for field in fillable_fields:
        if field in research and research[field]:
            if not existing.get(field):
                updated[field] = research[field]
                fields_updated.append(field)

    return updated, fields_updated


def main():
    # Load existing publications
    with open(PUBLICATIONS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    publications = {p['id']: p for p in data['publications']}
    total_updates = 0
    field_counts = {}

    # Load all research files
    research_files = glob.glob(os.path.join(RESEARCH_DIR, '*.json'))
    print(f"Found {len(research_files)} research files")

    for filepath in sorted(research_files):
        with open(filepath, 'r', encoding='utf-8') as f:
            research_data = json.load(f)

        findings = research_data if isinstance(research_data, list) else research_data.get('findings', [])

        for finding in findings:
            pub_id = finding.get('id')
            if pub_id and pub_id in publications:
                updated, fields = merge_publication(publications[pub_id], finding)
                if fields:
                    publications[pub_id] = updated
                    total_updates += 1
                    for field in fields:
                        field_counts[field] = field_counts.get(field, 0) + 1
                    print(f"  Updated ID {pub_id} ({finding.get('name', '?')}): {', '.join(fields)}")

    # Rebuild output
    data['publications'] = sorted(publications.values(), key=lambda x: x['id'])

    # Recalculate metadata
    active_count = sum(1 for p in data['publications'] if p['isActive'])
    data['metadata']['activeCount'] = active_count
    data['metadata']['ceasedCount'] = len(data['publications']) - active_count

    # Save updated publications
    with open(PUBLICATIONS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nTotal publications updated: {total_updates}")
    print(f"Fields filled:")
    for field, count in sorted(field_counts.items(), key=lambda x: -x[1]):
        print(f"  {field}: {count}")


if __name__ == '__main__':
    main()
