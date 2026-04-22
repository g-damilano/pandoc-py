from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TRACKERS_DIR = REPO_ROOT / 'trackers'
BASE_MATRIX = TRACKERS_DIR / 'CAPABILITY_MATRIX.csv'
SUPPLEMENT_GLOB = 'CAPABILITY_MATRIX_*SUPPLEMENT*.csv'
OUTPUT = TRACKERS_DIR / 'CONVERSION_PROGRESS.md'

IMPLEMENTED_STATES = {'skeleton_only', 'partially_implemented', 'implemented_unverified', 'verified_smoke', 'verified_standard', 'verified_extended', 'done'}
VERIFIED_STATES = {'verified_smoke', 'verified_standard', 'verified_extended', 'done'}


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.read_text(encoding='utf-8').splitlines()))


rows = _read_csv_rows(BASE_MATRIX)
supplement_paths = sorted(TRACKERS_DIR.glob(SUPPLEMENT_GLOB))
for supplement_path in supplement_paths:
    rows.extend(_read_csv_rows(supplement_path))

total = len(rows)
implemented = sum(1 for row in rows if row['State'] in IMPLEMENTED_STATES)
verified = sum(1 for row in rows if row['State'] in VERIFIED_STATES)
coarse_inventory_rows = sum(1 for row in rows if row['Capability ID'].startswith('INV-'))
fine_grained_rows = total - coarse_inventory_rows
supplement_count = len(supplement_paths)

content = (
    '# Conversion progress\n\n'
    'This percentage is for the **governed active matrix**, including the base capability matrix plus any admitted supplement matrices.\n'
    'It is therefore a more honest measure of how much of the admitted Pandoc surface is actually implemented and verified.\n\n'
    f'- Base governed matrix: **{BASE_MATRIX.name}**\n'
    f'- Admitted supplement matrices: **{supplement_count}**\n'
    f'- Active governed rows: **{total}**\n'
    f'- Fine-grained capability rows: **{fine_grained_rows}**\n'
    f'- Coarse inventory rows: **{coarse_inventory_rows}**\n'
    f'- Implemented-or-better rows: **{implemented}/{total}** (**{implemented / total * 100:.1f}%**)\n'
    f'- Smoke-verified-or-better rows: **{verified}/{total}** (**{verified / total * 100:.1f}%**)\n'
)
OUTPUT.write_text(content, encoding='utf-8')
print(content)
