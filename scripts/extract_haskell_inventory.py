#!/usr/bin/env python3
"""Extract a seeded Haskell inventory from a Pandoc source tree or zip archive.

This script is intentionally lightweight and deterministic. It does not try to
fully parse Cabal metadata. It inventories Haskell source modules and emits
CSV/JSON summaries that can seed the port-control trackers.
"""
from __future__ import annotations
import argparse, csv, io, json, os, zipfile
from collections import Counter

ROOTS = [
    ('core', 'pandoc-main/src/Text/Pandoc/'),
    ('cli', 'pandoc-main/pandoc-cli/src/'),
    ('lua', 'pandoc-main/pandoc-lua-engine/src/'),
    ('server', 'pandoc-main/pandoc-server/src/'),
]

def iter_names(repo_path: str):
    if zipfile.is_zipfile(repo_path):
        with zipfile.ZipFile(repo_path) as zf:
            for name in zf.namelist():
                yield name
    else:
        for root, _, files in os.walk(repo_path):
            for fn in files:
                rel = os.path.relpath(os.path.join(root, fn), repo_path).replace('\\', '/')
                yield f'pandoc-main/{rel}' if not rel.startswith('pandoc-main/') else rel

def classify(path: str) -> str:
    if path.startswith('pandoc-main/src/Text/Pandoc/Readers/'):
        return 'reader'
    if path.startswith('pandoc-main/src/Text/Pandoc/Writers/'):
        return 'writer'
    if path.startswith('pandoc-main/src/Text/Pandoc/Parsing/'):
        return 'parsing'
    if path.startswith('pandoc-main/src/Text/Pandoc/Citeproc/'):
        return 'citeproc'
    if path.startswith('pandoc-main/src/Text/Pandoc/Class/'):
        return 'runtime_class'
    if path.startswith('pandoc-main/pandoc-lua-engine/src/Text/Pandoc/Lua/') or path.endswith('/Text/Pandoc/Lua.hs'):
        return 'lua'
    if path.startswith('pandoc-main/pandoc-server/src/'):
        return 'server'
    if path.startswith('pandoc-main/pandoc-cli/src/'):
        return 'cli'
    if path.startswith('pandoc-main/src/Text/Pandoc/App/') or path.endswith('/Text/Pandoc/App.hs'):
        return 'app'
    return 'core_support'

def module_name(path: str, root: str) -> str:
    rel = path[len(root):]
    if rel.endswith('.hs'):
        rel = rel[:-3]
    return rel.replace('/', '.')

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('repo_path', help='Path to pandoc-main checkout or zip archive')
    ap.add_argument('outdir', help='Directory to receive inventory outputs')
    args = ap.parse_args()

    names = list(iter_names(args.repo_path))
    rows = []
    for path in names:
        if not path.endswith('.hs'):
            continue
        matched = None
        for pkg, root in ROOTS:
            if path.startswith(root):
                matched = (pkg, root)
                break
        if matched is None:
            continue
        pkg, root = matched
        mod = module_name(path, root)
        rows.append({
            'subsystem': classify(path),
            'module_name': mod,
            'module_path': path.replace('pandoc-main/', ''),
            'package_root': pkg,
            'nesting_level': mod.count('.'),
        })

    os.makedirs(args.outdir, exist_ok=True)
    with open(os.path.join(args.outdir, 'haskell_module_inventory.csv'), 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['subsystem', 'module_name', 'module_path', 'package_root', 'nesting_level'])
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: (r['subsystem'], r['module_name'])))

    payload = {
        'module_count': len(rows),
        'subsystem_counts': Counter(r['subsystem'] for r in rows),
        'package_root_counts': Counter(r['package_root'] for r in rows),
        'scope_gaps': ['pandoc-types is not included in the pandoc-main archive'],
    }
    with open(os.path.join(args.outdir, 'haskell_inventory_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
