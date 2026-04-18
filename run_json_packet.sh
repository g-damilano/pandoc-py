#!/usr/bin/env bash
set -u
repo=$(pwd)
repdir="$1"
shift
mkdir -p "$repdir"
for stem in "$@"; do
  ok=1
  for fmt in json html native; do
    python3 scripts/run_differential.py "tests/fixtures/json_input_screen/${stem}.json" --from json --to "$fmt" --report-id "PK-${stem}-${fmt}" --report-dir "$repdir" >/tmp/pk_out.txt 2>/tmp/pk_err.txt
    rc=$?
    if [ $rc -ne 0 ]; then
      ok=0
      break
    fi
  done
  if [ $ok -eq 1 ]; then
    echo "PASS $stem"
  else
    echo "FAIL $stem"
    tail -n 20 /tmp/pk_out.txt
    tail -n 20 /tmp/pk_err.txt
  fi
done
