#!/usr/bin/env bash
set -u
stem="$1"
repdir="$2"
mkdir -p "$repdir"
for fmt in json html native; do
  timeout 60s python3 scripts/run_differential.py "tests/fixtures/json_input_screen/${stem}.json" --from json --to "$fmt" --report-id "CFT-${stem}-${fmt}" --report-dir "$repdir" >/dev/null 2>&1
  rc=$?
  if [ $rc -ne 0 ]; then echo "FAIL $stem $fmt rc=$rc"; exit 1; fi
done
echo "PASS $stem"
