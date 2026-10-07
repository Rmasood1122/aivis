echo "sacrificial first line - run_market_v2.sh"
# run_market_v2.sh - one market, web-search tool offered, 5 reps. Wraps run_bank_multi_v2.py.
# Supersedes run_market_v1.sh (left in place). Changes, all from the 2026-10-07 smoke run and the
# realtor evidence files: Perplexity model is perplexity/sonar (the API rejects "sonar");
# --max-tokens 4096 (4 of 100 ChatGPT realtor answers were cut at 2048); a full run requires the seal
# to CHECK, not merely exist; one engine can be run alone.
#
#   bash restaurant_v1/run_market_v2.sh smoke nyc                 # 1 prompt x 1 run, all four engines
#   bash restaurant_v1/run_market_v2.sh smoke nyc gemini          # one engine
#   bash restaurant_v1/run_market_v2.sh full  nyc 20261007        # 20 prompts x 5 reps x 4 engines = 400 calls
#   bash restaurant_v1/run_market_v2.sh full  nyc 20261007 gemini # one engine: 100 calls
#
# Run from the repo root (the runner reads ./.env). Markets: nyc ma de ct.
# Override models with OPENAI_MODEL / ANTHROPIC_MODEL / GEMINI_MODEL / PERPLEXITY_MODEL.
# The runner refuses to overwrite a run file. To re-run an engine that failed outright, set RUN_TAG
# (e.g. RUN_TAG=retry1) so the new file gets a new name, and analyse the new file INSTEAD of the old one.
# No error is swallowed: every engine's exit status is printed and the script exits non-zero if any failed.
set -u

MODE="${1:-}"; MARKET="${2:-}"
case "$MODE" in smoke|full) ;; *) echo "usage: $0 smoke|full nyc|ma|de|ct [YYYYMMDD] [engine]"; exit 64;; esac
case "$MARKET" in nyc|ma|de|ct) ;; *) echo "REFUSE: market must be nyc|ma|de|ct"; exit 64;; esac
if [ "$MODE" = "full" ]; then STAMP="${3:-}"; ONLY="${4:-}"; else STAMP=""; ONLY="${3:-}"; fi
case "$ONLY" in ""|openai|anthropic|gemini|perplexity) ;; *) echo "REFUSE: engine must be openai|anthropic|gemini|perplexity"; exit 64;; esac
[ -f run_bank_multi_v2.py ] || { echo "REFUSE: run from the aivis repo root"; exit 66; }
[ -f .env ] || { echo "REFUSE: no .env in $(pwd) - the runner needs the four engine keys"; exit 66; }
BANK="restaurant_v1/${MARKET}_restaurant_prompts_v1.jsonl"
[ -f "$BANK" ] || { echo "REFUSE: missing bank $BANK"; exit 66; }
if [ "$MODE" = "full" ]; then
  case "$STAMP" in [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]) ;; *) echo "REFUSE: full needs a YYYYMMDD stamp"; exit 64;; esac
  bash restaurant_v1/seal_v1.sh check || { echo "REFUSE: seal check failed - see restaurant_v1/seal_v1.sh"; exit 65; }
fi

OPENAI_MODEL="${OPENAI_MODEL:-gpt-4o-2024-08-06}"
ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-claude-sonnet-5}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-3.8-flash}"
PERPLEXITY_MODEL="${PERPLEXITY_MODEL:-perplexity/sonar}"
TAG="${RUN_TAG:+_${RUN_TAG}}"
MAXTOK=4096

RAN=0; FAILED=0
for ENGINE in openai anthropic gemini perplexity; do
  [ -z "$ONLY" ] || [ "$ONLY" = "$ENGINE" ] || continue
  case "$ENGINE" in
    openai) MODEL="$OPENAI_MODEL";; anthropic) MODEL="$ANTHROPIC_MODEL";;
    gemini) MODEL="$GEMINI_MODEL";; perplexity) MODEL="$PERPLEXITY_MODEL";;
  esac
  if [ "$MODE" = "smoke" ]; then
    OUT="restaurant_v1/smoke/smoke_${ENGINE}_${MARKET}_$(date -u +%Y%m%dT%H%M%SZ)${TAG}.jsonl"
    python run_bank_multi_v2.py --engine "$ENGINE" --model "$MODEL" --bank "$BANK" --search --max-tokens "$MAXTOK" --smoke --out "$OUT"
  else
    OUT="restaurant_v1/runs/multi_${ENGINE}_${MARKET}_restaurant_v1_${STAMP}${TAG}.jsonl"
    python run_bank_multi_v2.py --engine "$ENGINE" --model "$MODEL" --bank "$BANK" --search --max-tokens "$MAXTOK" --runs 5 --out "$OUT"
  fi
  RC=$?
  RAN=$((RAN + 1))
  echo "ENGINE $ENGINE EXIT $RC OUT $OUT"
  [ "$RC" -eq 0 ] || FAILED=$((FAILED + 1))
done
echo "MARKET $MARKET MODE $MODE ENGINES_FAILED $FAILED POPULATION $RAN"
[ "$FAILED" -eq 0 ] && [ "$RAN" -gt 0 ]
