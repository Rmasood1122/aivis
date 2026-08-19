"""
Contract tests for the B3 evidence trail (src/aivis/evidence.py).

These pin the claim the PDF now makes: every number is backed by a stored
transcript whose hash is printed, re-verifiable, and shipped alongside.
"""
from __future__ import annotations

import hashlib
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path

from aivis.evidence import (
    bundle_digest,
    evidence_appendix_lines,
    verify_hashes,
    write_evidence_jsonl,
)
from aivis.models import VisibilityObj
from aivis.storage import read_jsonl


def _sha(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def _row(run_index: int = 1, raw: str = "1. Asana - great (no citation)",
         parse_success: bool = True) -> VisibilityObj:
    return VisibilityObj(
        visibility_id=f"vis-{run_index}",
        client_id="demo",
        client_brand_name="Asana",
        category="PM",
        prompt_id="PM-D01",
        prompt_text="best pm tools?",
        prompt_version="v1.0",
        prompt_family="discovery",
        expected_list_min=5,
        model_provider="anthropic",
        model_name="claude-sonnet-5",
        model_version_hint="claude-sonnet-5-20260115" if parse_success else None,
        temperature=None,
        max_tokens=2048,
        run_index=run_index,
        executed_at_utc=datetime(2026, 8, 19, 12, 0, run_index,
                                 tzinfo=timezone.utc),
        request_payload={"prompt_text": "best pm tools?", "stub": True},
        raw_response_text=raw,
        raw_response_json=None,
        response_hash=_sha(raw),
        tool_list=[],
        brand_mentioned=parse_success,
        brand_rank=1 if parse_success else None,
        brand_cited=False,
        brand_citation_domains=[],
        parse_success=parse_success,
        parse_errors=[] if parse_success else ["PE-01"],
        list_length=0,
        has_duplicates=False,
        output_contract_violations=[],
        parse_mode="stub",
        mention_score=1.0 if parse_success else "INSUFFICIENT_EVIDENCE",
        rank_score=1.0 if parse_success else "INSUFFICIENT_EVIDENCE",
        citation_score=0.0 if parse_success else "INSUFFICIENT_EVIDENCE",
        stability_anchor_key="demo:PM-D01:anthropic:claude-sonnet-5:na:v1.0",
        high_variance_flag=False,
        low_confidence_cap=1.0,
        cap_reasons=[],
    )


# --- the appendix carries the actual evidence ---------------------------

def test_appendix_contains_full_hash_of_every_run():
    objs = [_row(1, "response one"), _row(2, "response two"), _row(3, "x" * 500)]
    text = "\n".join(evidence_appendix_lines(objs))
    for o in objs:
        assert o.response_hash in text          # full 64 chars, untruncated
        assert len(o.response_hash) == 64


def test_appendix_run_count_matches():
    objs = [_row(i) for i in range(1, 6)]
    text = "\n".join(evidence_appendix_lines(objs))
    assert "Runs in trail: 5" in text


def test_appendix_includes_abstained_runs():
    objs = [_row(1), _row(2, raw="garbage", parse_success=False)]
    text = "\n".join(evidence_appendix_lines(objs))
    assert objs[1].response_hash in text
    assert "success=False" in text
    assert "PE-01" in text


def test_appendix_names_served_model_and_temperature():
    text = "\n".join(evidence_appendix_lines([_row(1)]))
    assert "claude-sonnet-5-20260115" in text
    assert "temperature: n/a" in text


def test_appendix_reports_clean_integrity_when_hashes_match():
    text = "\n".join(evidence_appendix_lines([_row(1), _row(2)]))
    assert "re-verified" in text
    assert "MISMATCH" not in text


def test_appendix_surfaces_tamper_instead_of_hiding_it():
    good = _row(1)
    tampered = _row(2, raw="original text")
    tampered = tampered.model_copy(update={"raw_response_text": "edited text"})
    text = "\n".join(evidence_appendix_lines([good, tampered]))
    assert "EVIDENCE INTEGRITY CHECK FAILED" in text
    assert "HASH MISMATCH run 2" in text


# --- verify_hashes ------------------------------------------------------

def test_verify_hashes_empty_on_clean_rows():
    assert verify_hashes([_row(1), _row(2)]) == []


def test_verify_hashes_catches_single_character_edit():
    r = _row(1, raw="the model said X")
    r = r.model_copy(update={"raw_response_text": "the model said Y"})
    problems = verify_hashes([r])
    assert len(problems) == 1
    assert "run 1" in problems[0]


# --- bundle digest ------------------------------------------------------

def test_bundle_digest_is_sha256_of_joined_hashes_in_run_order():
    objs = [_row(1, "a"), _row(2, "b")]
    joined = "\n".join(o.response_hash for o in objs)
    assert bundle_digest(objs) == _sha(joined)


def test_bundle_digest_changes_if_any_run_changes():
    a = [_row(1, "a"), _row(2, "b")]
    b = [_row(1, "a"), _row(2, "c")]
    assert bundle_digest(a) != bundle_digest(b)


# --- the evidence file the customer receives ----------------------------

def test_evidence_jsonl_roundtrips_with_raw_transcripts(tmp_path: Path):
    objs = [_row(1, "first raw"), _row(2, "second raw")]
    out = tmp_path / "evidence.jsonl"
    write_evidence_jsonl(out, objs)
    rows = read_jsonl(out)
    assert len(rows) == 2
    assert rows[0]["raw_response_text"] == "first raw"
    assert rows[1]["response_hash"] == _sha("second raw")
    # the bundle digest is recomputable from the evidence file alone
    joined = "\n".join(r["response_hash"] for r in rows)
    assert _sha(joined) == bundle_digest(objs)


def test_evidence_jsonl_overwrites_not_appends(tmp_path: Path):
    out = tmp_path / "evidence.jsonl"
    write_evidence_jsonl(out, [_row(1)])
    write_evidence_jsonl(out, [_row(1)])
    assert len(read_jsonl(out)) == 1   # deterministic export, not a log


# --- cli wiring ---------------------------------------------------------

def test_smoke_signature_carries_evidence_out():
    from aivis import cli
    assert "evidence_out" in inspect.signature(cli.smoke).parameters
