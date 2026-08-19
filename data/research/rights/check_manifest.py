"""Verify data/research/rights/rights-manifest.json covers every archival file.

Checks:
1. Every non-.json/.log file in the five source directories appears exactly
   once in the manifest.
2. Every manifest entry's path exists on disk.
3. Every keeper localFile in source-catalog.json that points into the five
   directories is present in the manifest (reports orphans either way).
4. Status enum values are valid and byStatus counts match the file list.

Exit code 0 = pass, 1 = fail. Prints one line per check.
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
RESEARCH = os.path.join(ROOT, 'data', 'research')
MANIFEST_PATH = os.path.join(RESEARCH, 'rights', 'rights-manifest.json')
CATALOG_PATH = os.path.join(RESEARCH, 'source-catalog.json')

DIRS = [
    os.path.join(RESEARCH, 'newspapers-com', 'downloads'),
    os.path.join(RESEARCH, 'wayback', 'clean'),
    os.path.join(RESEARCH, 'ia', 'clean'),
    os.path.join(RESEARCH, 'danky'),
    os.path.join(RESEARCH, 'depth-hunt', 'files'),
    os.path.join(RESEARCH, 'loc'),
]
SKIP_EXT = {'.json', '.log'}
VALID_STATUSES = {'publishable', 'publishable_with_credit', 'crop_first', 'metadata_only'}


def rel(path):
    return os.path.relpath(path, ROOT).replace('\\', '/')


def main():
    ok = True

    with open(MANIFEST_PATH, encoding='utf-8') as f:
        manifest = json.load(f)
    files = manifest['files']
    paths = [f['path'] for f in files]

    # 1/2. disk <-> manifest one-to-one
    disk_files = set()
    for d in DIRS:
        for fname in os.listdir(d):
            full = os.path.join(d, fname)
            if not os.path.isfile(full):
                continue
            if os.path.splitext(fname)[1].lower() in SKIP_EXT:
                continue
            disk_files.add(rel(full))

    manifest_paths = set(paths)
    dup = len(paths) - len(manifest_paths)
    if dup:
        print(f'FAIL duplicate paths in manifest: {dup}')
        ok = False
    else:
        print('PASS no duplicate paths in manifest')

    missing_from_manifest = disk_files - manifest_paths
    if missing_from_manifest:
        print(f'FAIL {len(missing_from_manifest)} disk file(s) missing from manifest:')
        for p in sorted(missing_from_manifest):
            print('  -', p)
        ok = False
    else:
        print(f'PASS all {len(disk_files)} disk files present in manifest')

    extra_in_manifest = manifest_paths - disk_files
    if extra_in_manifest:
        print(f'FAIL {len(extra_in_manifest)} manifest entr(y/ies) do not exist on disk:')
        for p in sorted(extra_in_manifest):
            print('  -', p)
        ok = False
    else:
        print('PASS no manifest entries pointing at missing files')

    # 3. keeper localFile cross-check
    with open(CATALOG_PATH, encoding='utf-8') as f:
        catalog = json.load(f)

    scoped_prefixes = (
        'data/research/newspapers-com/downloads/',
        'data/research/wayback/clean/',
        'data/research/ia/clean/',
        'data/research/danky/',
        'data/research/depth-hunt/files/',
        'data/research/loc/',
    )
    keeper_files = set()
    for p in catalog['publications']:
        for k in p.get('keepers', []):
            lf = k.get('localFile')
            if not lf:
                continue
            lf = lf.replace('\\', '/')
            if lf.startswith(scoped_prefixes):
                keeper_files.add(lf)

    keeper_not_in_manifest = keeper_files - manifest_paths
    if keeper_not_in_manifest:
        print(f'FAIL {len(keeper_not_in_manifest)} keeper localFile(s) missing from manifest:')
        for p in sorted(keeper_not_in_manifest):
            print('  -', p)
        ok = False
    else:
        print(f'PASS all {len(keeper_files)} in-scope keeper localFile references are covered by the manifest')

    manifest_no_keeper = manifest_paths - keeper_files
    print(f'INFO {len(manifest_no_keeper)} manifest file(s) are not referenced by any keeper '
          f'(orphans on disk vs. catalog -- expected for danky, debug artifacts, and out-of-state supporting clips)')

    # 4. status validity + count reconciliation
    bad_status = [f['path'] for f in files if f['status'] not in VALID_STATUSES]
    if bad_status:
        print(f'FAIL {len(bad_status)} file(s) with invalid status:')
        for p in bad_status:
            print('  -', p)
        ok = False
    else:
        print('PASS all statuses are valid enum values')

    computed_by_status = {}
    for f in files:
        computed_by_status[f['status']] = computed_by_status.get(f['status'], 0) + 1
    if computed_by_status != manifest['metadata']['byStatus']:
        print(f'FAIL metadata.byStatus mismatch: computed={computed_by_status} '
              f'manifest={manifest["metadata"]["byStatus"]}')
        ok = False
    else:
        print('PASS metadata.byStatus matches computed counts')

    if manifest['metadata']['totalCount'] != len(files):
        print(f'FAIL metadata.totalCount ({manifest["metadata"]["totalCount"]}) != len(files) ({len(files)})')
        ok = False
    else:
        print(f'PASS metadata.totalCount matches file count ({len(files)})')

    print()
    print('RESULT:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
