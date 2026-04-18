from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MATRIX = REPO_ROOT / 'trackers' / 'CAPABILITY_MATRIX.csv'
OUTPUT = REPO_ROOT / 'trackers' / 'CONVERSION_PROGRESS.md'

IMPLEMENTED_STATES = {'skeleton_only', 'partially_implemented', 'implemented_unverified', 'verified_smoke', 'verified_standard', 'verified_extended', 'done'}
VERIFIED_STATES = {'verified_smoke', 'verified_standard', 'verified_extended', 'done'}

rows = list(csv.DictReader(MATRIX.read_text(encoding='utf-8').splitlines()))
total = len(rows)
implemented = sum(1 for row in rows if row['State'] in IMPLEMENTED_STATES)
verified = sum(1 for row in rows if row['State'] in VERIFIED_STATES)
coarse_inventory_rows = sum(1 for row in rows if row['Capability ID'].startswith('INV-'))
fine_grained_rows = total - coarse_inventory_rows

content = (
    '# Conversion progress\n\n'
    'This percentage is for the **governed active matrix**, which now includes both fine-grained implemented capabilities and coarse repo-scope inventory rows that have only been mapped.\n'
    'It is therefore a more honest measure of how much of the admitted Pandoc surface is actually implemented and verified.\n\n'
    f'- Active governed rows: **{total}**\n'
    f'- Fine-grained capability rows: **{fine_grained_rows}**\n'
    f'- Coarse inventory rows: **{coarse_inventory_rows}**\n'
    f'- Implemented-or-better rows: **{implemented}/{total}** (**{implemented / total * 100:.1f}%**)\n'
    f'- Smoke-verified-or-better rows: **{verified}/{total}** (**{verified / total * 100:.1f}%**)\n'
)
OUTPUT.write_text(content, encoding='utf-8')
print(content)
