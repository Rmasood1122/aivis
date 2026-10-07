echo "sacrificial first line - run_market_v1.sh"
# run_market_v1.sh - one market, four engines, web search ON, 5 reps. Wraps run_bank_multi_v2.py.
#
#   bash restaurant_v1/run_market_v1.sh smoke nyc            # 1 prompt x 1 run per engine, prints text + citations
#   bash restaurant_v1/run_market_v1.sh full  nyc 20261007   # 20 prompts x 5 reps x 4 engines = 400 calls
#
# Run from the repo root (the runner reads ./.env). Markets: nyc ma de ct.
# Model strings default to the ones recorded in realtor_v1/runs (2026-09-23); override with
# OPENAI_MODEL / ANTHROPIC_MODEL / GEMINI_MODEL / PERPLEXITY_MODEL. The resolved model is stored per row.
# No error is swallowed: every engine's exit status is printed and the script exits non-zero if any failed.
set -u

MODE="${1:-}"; MARKET="${2:-}"; STAMP="${3:-}"
case "$MODE" in smoke|full) ;; *) echo "usage: $0 smoke|full nyc|ma|de|ct [YYYYMMDD]"; exit 64;; esac
case "$MARKET" in nyc|ma|de|ct) ;; *) echo "REFUSE: market must be nyc|ma|de|ct"; exit 64;; esac
[ -f run_bank_multi_v2.py ] || { echo "REFUSE: run from the aivis repo root"; exit 66; }
[ -f .env ] || { echo "REFUSE: no .env in $(pwd) - the runner needs the four engine keys"; exit 66; }
BANK="restaurant_v1/${MARKET}_restaurant_prompts_v1.jsonl"
[ -f "$BANK" ] || { echo "REFUSE: missing bank $BANK"; exit 66; }
if [ "$MODE" = "full" ]; then
  case "$STAMP" in [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]) ;; *) echo "REFUSE: full needs a YYYYMMDD stamp"; exit 64;; esac
  [ -f restaurant_v1/PREREG_SEALED_v1.txt ] || { echo "REFUSE: prereg not sealed - see PREREG 'Seal' section"; exit 65; }
fi

OPENAI_MODEL="${OPENAI_MODEL:-gpt-4o-2024-08-06}"
ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-claude-sonnet-5}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-3.8-flash}"
PERPLEXITY_MODEL="${PERPLEXITY_MODEL:-sonar}"

FAILED=0
for ENGINE in openai anthropic gemini perplexity; do
  case "$ENGINE" in
    openai) MODEL="$OPENAI_MODEL";; anthropic) MODEL="$ANTHROPIC_MODEL";;
    gemini) MODEL="$GEMINI_MODEL";; perplexity) MODEL="$PERPLEXITY_MODEL";;
  esac
  if [ "$MODE" = "smoke" ]; then
    OUT="restaurant_v1/smoke/smoke_${ENGINE}_${MARKET}_$(date -u +%Y%m%dT%H%M%SZ).jsonl"
    python run_bank_multi_v2.py --engine "$ENGINE" --model "$MODEL" --bank "$BANK" --search --smoke --out "$OUT"
  else
    OUT="restaurant_v1/runs/multi_${ENGINE}_${MARKET}_restaurant_v1_${STAMP}.jsonl"
    python run_bank_multi_v2.py --engine "$ENGINE" --model "$MODEL" --bank "$BANK" --search --runs 5 --out "$OUT"
  fi
  RC=$?
  echo "ENGINE $ENGINE EXIT $RC OUT $OUT"
  [ "$RC" -eq 0 ] || FAILED=$((FAILED + 1))
done
echo "MARKET $MARKET MODE $MODE ENGINES_FAILED $FAILED POPULATION 4"
[ "$FAILED" -eq 0 ]
