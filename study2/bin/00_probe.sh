#!/usr/bin/env bash
# 00_probe.sh — LIVE CREDENTIAL GATE.
# Nothing downstream runs unless this writes out/probe_receipt.json this session.
# This exists because a prior run emitted 1,260 calls of telemetry with zero calls placed.
set -euo pipefail
cd "$(dirname "$0")/.."

STAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
mkdir -p out
RECEIPT=out/probe_receipt.json
: > out/.probe_tmp

probe_anthropic() {
  [ -z "${ANTHROPIC_API_KEY:-}" ] && { echo "anthropic|NOKEY|-"; return; }
  code=$(curl -s -o out/.a_body -w '%{http_code}' https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d '{"model":"claude-sonnet-4-6","max_tokens":8,"messages":[{"role":"user","content":"ok"}]}' || echo 000)
  id=$(grep -o '"id":"[^"]*"' out/.a_body 2>/dev/null | head -1 | cut -d'"' -f4)
  echo "anthropic|$code|${id:--}"
}

probe_openai() {
  [ -z "${OPENAI_API_KEY:-}" ] && { echo "openai|NOKEY|-"; return; }
  code=$(curl -s -o out/.o_body -w '%{http_code}' https://api.openai.com/v1/chat/completions \
    -H "Authorization: Bearer $OPENAI_API_KEY" -H "content-type: application/json" \
    -d '{"model":"gpt-4o-mini","max_tokens":8,"messages":[{"role":"user","content":"ok"}]}' || echo 000)
  id=$(grep -o '"id":"[^"]*"' out/.o_body 2>/dev/null | head -1 | cut -d'"' -f4)
  echo "openai|$code|${id:--}"
}

probe_xai() {
  [ -z "${XAI_API_KEY:-}" ] && { echo "xai|NOKEY|-"; return; }
  code=$(curl -s -o out/.x_body -w '%{http_code}' https://api.x.ai/v1/chat/completions \
    -H "Authorization: Bearer $XAI_API_KEY" -H "content-type: application/json" \
    -d '{"model":"grok-2-latest","max_tokens":8,"messages":[{"role":"user","content":"ok"}]}' || echo 000)
  id=$(grep -o '"id":"[^"]*"' out/.x_body 2>/dev/null | head -1 | cut -d'"' -f4)
  echo "xai|$code|${id:--}"
}

LIVE=0
{
  echo "{"
  echo "  \"probed_at\": \"$STAMP\","
  echo "  \"engines\": ["
  first=1
  for r in "$(probe_anthropic)" "$(probe_openai)" "$(probe_xai)"; do
    name=${r%%|*}; rest=${r#*|}; code=${rest%%|*}; id=${rest##*|}
    [ "$code" = "200" ] && LIVE=$((LIVE+1))
    [ $first -eq 0 ] && echo ","
    first=0
    printf '    {"engine":"%s","http":"%s","response_id":"%s","live":%s}' \
      "$name" "$code" "$id" "$([ "$code" = 200 ] && echo true || echo false)"
  done
  echo ""
  echo "  ],"
  echo "  \"live_engine_count\": $LIVE"
  echo "}"
} > "$RECEIPT"

rm -f out/.a_body out/.o_body out/.x_body out/.probe_tmp
cat "$RECEIPT"

if [ "$LIVE" -lt 1 ]; then
  echo ""
  echo "GATE FAILED: 0 live engines. Nothing downstream may run."
  echo "No telemetry may be reported for a run that did not happen."
  rm -f "$RECEIPT"
  exit 1
fi
echo ""
echo "GATE PASSED: $LIVE live engine(s). Receipt at $RECEIPT"
