"""Tests for surface_presence.py. Synthetic fixtures only — no real transcripts.

Each test targets a failure mode from run 3 or a charter rule:
  - naming-sparse cell reported as engine behavior, not subject gap
  - Muck Rack counted as surface, never as firm
  - mode conservation
  - error rows excluded from denominators
  - destruction lock on output paths
  - Bark/Clutch false-positive vectors
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent
TOOL = HERE / "surface_presence.py"

sys.path.insert(0, str(HERE))
import surface_presence as sp  # noqa: E402


def row(text, model="claude-sonnet-5", family="buyer_intent", pid="BI-01", err=None):
    r = {
        "response_text": text,
        "model": model,
        "family": family,
        "prompt_id": pid,
        "request_payload": {"model": model},
        "sha256": "0" * 64,
    }
    if err:
        r["error"] = err
        r["response_text"] = ""
    return r


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


@pytest.fixture
def firms_file(tmp_path):
    p = tmp_path / "firms.txt"
    p.write_text("Clarity PR\nBospar\nEdelman\n", encoding="utf-8")
    return str(p)


def test_referral_routing_detected(tmp_path):
    ev = tmp_path / "ev.jsonl"
    write_jsonl(
        ev,
        [
            row("You could try HARO or Qwoted to get media coverage yourself."),
            row("Check the PRSA Find-a-Firm directory for vetted agencies."),
            row("I can't recommend specific firms without knowing your budget."),
        ],
    )
    res = sp.run([str(ev)], "Credible PR", None, None, None)
    cell = res["engine_behavior"][0]
    assert cell["modes"]["REFERS_TO_SURFACES"] == 2
    assert cell["modes"]["REFUSES_OPAQUE"] == 1
    assert cell["naming_sparse"] is True
    sids = {r["surface_id"] for r in res["referral_surfaces"]}
    assert sids == {"journalist_matching", "professional_directory"}


def test_naming_sparse_is_engine_behavior_not_gap(tmp_path, firms_file):
    """Run 3's core failure: 0% naming must surface as engine behavior."""
    ev = tmp_path / "ev.jsonl"
    write_jsonl(ev, [row("Try HARO for earned media.") for _ in range(10)])
    res = sp.run([str(ev)], "Credible PR", firms_file, None, None)
    cell = res["engine_behavior"][0]
    assert cell["naming_sparse"] is True
    assert "UNDEFINED" in cell["primary_finding"]
    # subject is never mentioned in output as having a "gap" — no gaps field exists here at all
    assert "gaps" not in res


def test_muckrack_is_surface_not_firm(tmp_path, firms_file):
    ev = tmp_path / "ev.jsonl"
    write_jsonl(ev, [row("Use Muck Rack to find journalists in your beat.")])
    res = sp.run([str(ev)], None, firms_file, None, None)
    assert res["engine_behavior"][0]["modes"]["REFERS_TO_SURFACES"] == 1
    assert res["referral_surfaces"][0]["surface_id"] == "media_database"


def test_firm_naming_takes_precedence(tmp_path, firms_file):
    ev = tmp_path / "ev.jsonl"
    write_jsonl(ev, [row("Bospar is strong in tech PR; you can also try HARO.")])
    res = sp.run([str(ev)], None, firms_file, None, None)
    m = res["engine_behavior"][0]["modes"]
    assert m["NAMES_FIRMS"] == 1
    # surface still counted (Step R runs on NAMES_FIRMS too)
    assert res["referral_surfaces"][0]["surface_id"] == "journalist_matching"


def test_mode_conservation(tmp_path, firms_file):
    ev = tmp_path / "ev.jsonl"
    texts = [
        "Bospar leads here.",
        "Try Qwoted.",
        "I cannot recommend specific firms.",
        "PR is about relationships and consistency.",
    ]
    write_jsonl(ev, [row(t, pid=f"P{i}") for i, t in enumerate(texts)])
    res = sp.run([str(ev)], None, firms_file, None, None)
    cell = res["engine_behavior"][0]
    assert sum(cell["modes"].values()) == cell["denominator"] == 4


def test_error_rows_excluded_from_denominator(tmp_path):
    """D0's lesson: check clean, never the console."""
    ev = tmp_path / "ev.jsonl"
    write_jsonl(ev, [row("Try HARO."), row("", err="transport"), row("", err="429")])
    res = sp.run([str(ev)], None, None, None, None)
    assert res["rows_attempted"] == 3
    assert res["rows_clean"] == 1
    assert res["engine_behavior"][0]["denominator"] == 1


def test_no_firms_list_prints_warning(tmp_path):
    ev = tmp_path / "ev.jsonl"
    write_jsonl(ev, [row("Edelman is the largest PR firm.")])
    res = sp.run([str(ev)], None, None, None, None)
    assert res["note_no_firms"] is not None
    # without a firms list this lands in OTHER, not silently in NAMES_FIRMS
    assert res["engine_behavior"][0]["modes"]["OTHER"] == 1


def test_presence_file_validated_and_applied(tmp_path):
    ev = tmp_path / "ev.jsonl"
    write_jsonl(ev, [row("Try HARO."), row("Also HARO.", pid="BI-02")])
    good = tmp_path / "presence.json"
    good.write_text(json.dumps({"journalist_matching": "ABSENT"}), encoding="utf-8")
    res = sp.run([str(ev)], "Credible PR", None, str(good), None)
    assert res["referral_surfaces"][0]["subject_presence"] == "ABSENT"

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"journalist_matching": "maybe"}), encoding="utf-8")
    with pytest.raises(SystemExit):
        sp.run([str(ev)], None, None, str(bad), None)


def test_default_presence_not_measured(tmp_path):
    ev = tmp_path / "ev.jsonl"
    write_jsonl(ev, [row("Try HARO.")])
    res = sp.run([str(ev)], "Credible PR", None, None, None)
    assert res["referral_surfaces"][0]["subject_presence"] == "NOT_MEASURED"


def test_bark_and_clutch_fp_vectors(tmp_path):
    ev = tmp_path / "ev.jsonl"
    write_jsonl(
        ev,
        [
            row("Dogs bark at strangers; in a clutch situation stay calm."),
            row("Browse Clutch or Bark.com for rated agencies.", pid="BI-02"),
        ],
    )
    res = sp.run([str(ev)], None, None, None, None)
    cell = res["engine_behavior"][0]
    assert cell["modes"]["OTHER"] == 1  # the dog sentence hits nothing
    assert cell["modes"]["REFERS_TO_SURFACES"] == 1
    rs = res["referral_surfaces"][0]
    assert rs["surface_id"] == "review_marketplace"
    assert rs["count"] == 1


def test_low_n_flag(tmp_path):
    ev = tmp_path / "ev.jsonl"
    write_jsonl(ev, [row("Try HARO."), row("Use Qwoted.", pid="BI-02")])
    res = sp.run([str(ev)], None, None, None, None)
    assert res["referral_surfaces"][0]["count"] == 2
    assert res["referral_surfaces"][0]["low_n"] is True


def test_engine_mapping():
    assert sp.engine_of("claude-sonnet-5") == "anthropic"
    assert sp.engine_of("gpt-4o") == "openai"
    assert sp.engine_of("sonar-pro") == "perplexity"
    assert sp.engine_of("gemini-2.0") == "google"
    assert sp.engine_of("") == "unknown"


def test_cli_refuses_existing_output(tmp_path):
    """Destruction lock: never overwrite."""
    ev = tmp_path / "ev.jsonl"
    write_jsonl(ev, [row("Try HARO.")])
    out = tmp_path / "out.json"
    out.write_text("precious", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(TOOL), str(ev), "--out", str(out)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "REFUSED" in proc.stderr or "REFUSED" in proc.stdout
    assert out.read_text(encoding="utf-8") == "precious"


def test_cli_end_to_end(tmp_path):
    ev = tmp_path / "ev.jsonl"
    write_jsonl(ev, [row("Try HARO or Muck Rack."), row("PRSA has a directory.", pid="BI-02")])
    out = tmp_path / "res.json"
    rep = tmp_path / "rep.md"
    proc = subprocess.run(
        [sys.executable, str(TOOL), str(ev), "--subject", "Credible PR",
         "--out", str(out), "--report", str(rep)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["canon_version"] == "referral_surfaces_v0.1"
    assert len(data["canon_sha256"]) == 64
    md = rep.read_text(encoding="utf-8")
    assert "NOT_MEASURED" in md
    assert "UNVALIDATED_PARSE_PENDING_KAPPA" in md


def test_canon_hash_stable():
    assert sp.canon_hash() == sp.canon_hash()
