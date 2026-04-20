#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PORT_INDEX = REPO_ROOT / 'PORT_INDEX.yaml'
MATRIX = REPO_ROOT / 'trackers' / 'CAPABILITY_MATRIX.csv'
VERIFICATION_STATUS = REPO_ROOT / 'trackers' / 'VERIFICATION_STATUS.md'
PACKAGE_INIT = REPO_ROOT / 'src' / 'pandoc_py' / '__init__.py'
NEXT_ITERATION = REPO_ROOT / 'trackers' / 'NEXT_ITERATION.md'
OUTPUT = REPO_ROOT / 'trackers' / 'CONTROL_PLANE_STATUS.md'

REQUIRED_FILES = [
    REPO_ROOT / 'INDEX.md',
    PORT_INDEX,
    REPO_ROOT / 'docs' / '00_program' / 'AI_START_HERE.md',
    REPO_ROOT / 'docs' / '00_program' / 'ITERATION_PROTOCOL.md',
    REPO_ROOT / 'docs' / '00_program' / 'OPERATING_MODEL.md',
    REPO_ROOT / 'docs' / '00_program' / 'TRANSLATION_PROGRAM_FRAMEWORK.md',
    REPO_ROOT / 'docs' / '03_contracts' / 'CAPABILITY_CONTRACT.md',
    REPO_ROOT / 'docs' / '03_contracts' / 'VERIFICATION_CONTRACT.md',
    REPO_ROOT / 'docs' / '03_contracts' / 'WORK_PACKET_CONTRACT.md',
    REPO_ROOT / 'trackers' / 'WORK_PACKET_TEMPLATE.md',
    REPO_ROOT / 'trackers' / 'ITERATION_STATE.yaml',
    REPO_ROOT / 'trackers' / 'ITERATION_INDEX.yaml',
    MATRIX,
    REPO_ROOT / 'trackers' / 'IMPLEMENTATION_LOG.md',
    VERIFICATION_STATUS,
    NEXT_ITERATION,
]

REQUIRED_MATRIX_COLUMNS = [
    'Capability ID',
    'Area',
    'Haskell source',
    'Python target',
    'User-visible behavior',
    'Priority',
    'State',
    'Verification level',
    'Known divergences',
    'Notes',
]


def read_package_version() -> str:
    text = PACKAGE_INIT.read_text(encoding='utf-8')
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('__version__'):
            return line.split('=', 1)[1].strip().strip("'").strip('"')
    raise RuntimeError('Could not find __version__.')


def verify_version_consistency(package_version: str) -> tuple[bool, str]:
    text = VERIFICATION_STATUS.read_text(encoding='utf-8')
    needle = f'Package version: pandoc_py {package_version}.'
    return (needle in text, needle)


def main() -> int:
    missing = [str(path.relative_to(REPO_ROOT)) for path in REQUIRED_FILES if not path.exists()]

    matrix_ok = False
    matrix_note = 'not checked'
    if MATRIX.exists():
        with MATRIX.open('r', encoding='utf-8', newline='') as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
            missing_cols = [col for col in REQUIRED_MATRIX_COLUMNS if col not in columns]
            if missing_cols:
                matrix_note = f'missing columns: {", ".join(missing_cols)}'
            else:
                rows = list(reader)
                matrix_ok = bool(rows)
                matrix_note = f'{len(rows)} rows present' if rows else 'no capability rows present'

    next_iteration_ok = False
    next_note = 'missing'
    if NEXT_ITERATION.exists():
        text = NEXT_ITERATION.read_text(encoding='utf-8').strip()
        next_iteration_ok = len(text.splitlines()) >= 2 and len(text) > len('# Next iteration')
        next_note = 'present and non-empty' if next_iteration_ok else 'present but empty'

    package_version = read_package_version()
    version_ok, version_expected = verify_version_consistency(package_version)

    checks = [
        ('required_files', not missing, 'all required files present' if not missing else 'missing: ' + ', '.join(missing)),
        ('capability_matrix', matrix_ok, matrix_note),
        ('next_iteration', next_iteration_ok, next_note),
        ('version_consistency', version_ok, f'expected line in verification status: {version_expected}'),
    ]

    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    overall = 'PASS' if passed == total else 'FAIL'

    lines = [
        '# Control plane status',
        '',
        f'- Overall: **{overall}** ({passed}/{total} checks passed)',
        f'- Package version: **pandoc_py {package_version}**',
        '',
        '| Check | Status | Note |',
        '|---|---|---|',
    ]
    for name, ok, note in checks:
        lines.append(f'| {name} | {"PASS" if ok else "FAIL"} | {note} |')
    lines.append('')
    OUTPUT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))
    return 0 if overall == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
