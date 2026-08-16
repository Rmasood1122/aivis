#!/usr/bin/env bash
set -euo pipefail

echo "=== Running tests ==="
poetry run pytest -q

echo ""
echo "=== Running smoke test ==="
poetry run aivis smoke --prompt-id PM-D01 --runs 5

echo ""
echo "=== Done ==="
echo "Check data/reports/smoke_report.pdf"
echo "Check data/aggregates/smoke_aggregate.json"
