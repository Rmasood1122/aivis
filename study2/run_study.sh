#!/usr/bin/env bash
# run_study.sh — orchestrates the automatable steps and STOPS at the two that are not.
# Usage:  ./run_study.sh <stage>
#   stages: probe | validate | plan | measure | score | sheets | analyze
set -euo pipefail
cd "$(dirname "$0")"
STAGE="${1:-help}"
RUNID="${RUNID:-$(date -u +%Y%m%d-%H%M)}"

case "$STAGE" in
  probe)
    bash bin/00_probe.sh
    ;;

  validate)
    [ -f config/sample_worksheet.csv ] || {
      echo "STOP — HUMAN STEP 1 NOT DONE."
      echo "  cp config/sample_worksheet_TEMPLATE.csv config/sample_worksheet.csv"
      echo "  then fill 50 rows by hand. No script may populate it."
      exit 1; }
    python3 bin/02_validate_sample.py config/sample_worksheet.csv
    ;;

  plan)
    python3 bin/03_measure.py --out "data/runs_${RUNID}.jsonl" --dry-run
    ;;

  measure)
    [ -f out/probe_receipt.json ] || { echo "STOP: run './run_study.sh probe' first."; exit 1; }
    [ -f data/sample_validated.csv ] || { echo "STOP: run './run_study.sh validate' first."; exit 1; }
    python3 bin/03_measure.py --out "data/runs_${RUNID}.jsonl"
    echo "RUNID=$RUNID"
    ;;

  score)
    LATEST=$(ls -t data/runs_*.jsonl 2>/dev/null | head -1)
    [ -n "$LATEST" ] || { echo "STOP: no data/runs_*.jsonl found."; exit 1; }
    python3 bin/04_score.py "$LATEST"
    ;;

  sheets)
    python3 bin/05_make_coding_sheets.py "${SEED:-20260829}" "${CODERS:-4}"
    echo ""
    echo "STOP — HUMAN STEP 2. Coders fill out/coding_sheets/*.csv."
    echo "They must NOT be told which brands are ranked. Do not send them the key files."
    ;;

  analyze)
    python3 bin/06_analyze.py
    ;;

  *)
    cat <<'EOF'
STAGES, in order:

  1. ./run_study.sh probe      automated   live credential gate, writes a receipt
  2. ./run_study.sh validate   HUMAN FIRST you fill the 50-row worksheet, script checks it
  3. ./run_study.sh plan       automated   prints call count and cost, places no calls
  4. ./run_study.sh measure    automated   the API run, both orders, hashed rows
  5. ./run_study.sh score      automated   assigns ranked/middle/non-ranked from data
  6. ./run_study.sh sheets     automated   blinded coding sheets  -> HUMAN SECOND
  7. ./run_study.sh analyze    automated   prevalence differences, CIs, verdict

Two steps are human and cannot be scripted: filling the sample worksheet (step 2)
and coding the features (step 6). Everything else runs unattended.
EOF
    ;;
esac
