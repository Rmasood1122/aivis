echo "sacrificial first line - seal_v1.sh"
# seal_v1.sh - seal and check the restaurant_v1 pre-registration. Run from the repo root.
#
#   bash restaurant_v1/seal_v1.sh make    # writes restaurant_v1/PREREG_SEALED_v1.txt, then YOU commit it
#   bash restaurant_v1/seal_v1.sh check   # exit 0 only if every sealed file still matches
#
# What is hashed: the bytes git stores at HEAD (git show HEAD:<path>), not the bytes on disk. On Windows
# git rewrites text files with CRLF at checkout, so a disk hash differs between machines; the stored
# blob does not. `make` and `check` both also require the working copy to equal HEAD for every sealed
# file, so the thing that is hashed is the thing that runs.
# The seal is tamper-evident, not proof of date: the date comes from the commit that adds the seal file.
set -u

MODE="${1:-}"
SEAL="restaurant_v1/PREREG_SEALED_v1.txt"
FILES="
restaurant_v1/PREREG_restaurant_test_v1.md
restaurant_v1/nyc_restaurant_prompts_v1.jsonl
restaurant_v1/ma_restaurant_prompts_v1.jsonl
restaurant_v1/de_restaurant_prompts_v1.jsonl
restaurant_v1/ct_restaurant_prompts_v1.jsonl
restaurant_v1/gen_restaurant_banks_v1.py
restaurant_v1/analyze_restaurant_run_v1.py
restaurant_v1/test_analyze_restaurant_run_v1.py
restaurant_v1/run_market_v2.sh
restaurant_v1/seal_v1.sh
"
case "$MODE" in make|check) ;; *) echo "usage: $0 make|check"; exit 64;; esac
[ -f run_bank_multi_v2.py ] || { echo "REFUSE: run from the aivis repo root"; exit 66; }

# every sealed file must be committed, and unchanged in the working copy
for F in $FILES; do
  git cat-file -e "HEAD:$F" 2>/dev/null || { echo "REFUSE: $F is not committed at HEAD"; exit 65; }
  git diff --quiet HEAD -- "$F" || { echo "REFUSE: $F differs from HEAD - commit it (or discard your edit) first"; exit 65; }
done

blob_sha() { git show "HEAD:$1" | sha256sum | cut -d' ' -f1; }

if [ "$MODE" = "make" ]; then
  [ -e "$SEAL" ] && { echo "REFUSE: $SEAL exists. A seal is made once; a change is a v2."; exit 65; }
  grep -q '____' restaurant_v1/PREREG_restaurant_test_v1.md && {
    echo "REFUSE: the Predictions section still has blank ____ lines. Fill them in, commit, then seal."; exit 65; }
  {
    echo "# restaurant_v1 pre-registration seal"
    echo "# sealed_at_utc $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "# head_commit $(git rev-parse HEAD)"
    echo "# hash = sha256 of the git blob at head_commit"
    for F in $FILES; do echo "$(blob_sha "$F")  $F"; done
  } > "$SEAL"
  echo "WROTE $SEAL FILES $(grep -vc '^#' "$SEAL")"
  echo "NEXT: git add $SEAL && git commit -m \"restaurant_v1: seal prereg, banks, analyzer, runner\" && git push"
  exit 0
fi

[ -f "$SEAL" ] || { echo "SEAL CHECK FAIL: $SEAL does not exist"; exit 1; }
N=0; BAD=0
for F in $FILES; do
  N=$((N + 1))
  WANT="$(tr -d '\r' < "$SEAL" | grep -v '^#' | awk -v f="$F" '$2 == f {print $1}')"
  HAVE="$(blob_sha "$F")"
  if [ -n "$WANT" ] && [ "$WANT" = "$HAVE" ]; then :; else
    BAD=$((BAD + 1)); echo "MISMATCH $F sealed=${WANT:-absent} now=$HAVE"
  fi
done
echo "SEAL CHECK MATCH $((N - BAD)) of $N"
[ "$BAD" -eq 0 ]
