"""Regression: cli brand match must normalize the client brand the same
way parser.norm_name normalizes tool names (F10, measured 2026-08-17).
Written BEFORE the fix — must fail 6/7 against current code."""
import json
import pytest
from aivis import cli

# (client_brand, expected brand_mentioned) — stub output contains all of these
CASES = [
    ("Asana", True),                          # control: passes pre-fix
    ("Monday", True),                         # alias -> monday.com
    ("Click Up", True),                       # alias -> clickup
    ("Jira Software", True),                  # alias -> jira
    ("Wrike Project Management", True),       # alias -> wrike
    ("Smartsheet Project Management", True),  # alias -> smartsheet
    ("Base Camp", True),                      # alias -> basecamp
]

@pytest.mark.parametrize("brand,expected", CASES, ids=[c[0] for c in CASES])
def test_brand_match_survives_normalization(tmp_path, brand, expected):
    out = tmp_path / "runs.jsonl"
    cli.run(client_brand=brand, out=out)  # stub mode, no API call
    row = json.loads(out.read_text(encoding="utf-8").splitlines()[-1])
    assert row["brand_mentioned"] is expected, f"{brand!r} invisible to brand match"
