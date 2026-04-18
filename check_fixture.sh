#!/usr/bin/env bash
set -u
stem="$1"
repdir="$2"
mkdir -p "$repdir"
for fmt in json html native; do
  python3 scripts/run_differential.py "tests/fixtures/json_input_screen/${stem}.json" --from json --to "$fmt" --report-id "CF-${stem}-${fmt}" --report-dir "$repdir" >/dev/null 2>&1 || { echo FAIL "$stem" "$fmt"; exit 1; }
done
echo PASS "$stem"
