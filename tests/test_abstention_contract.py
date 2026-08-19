"""
Contract: a response that could not be parsed must ABSTAIN, never score.

This pins defect D6. It is a refusal-to-answer contract, not a numeric
correctness check, which is why it lives beside test_parse_success_contract.py
rather than inside test_scorer.py.

The failure this prevents: a PARSE_ERROR run leaving the machine as 0.540.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from aivis.models import VisibilityObj
from aivis.parser import parse_tool_list
from aivis.scorer import INSUFFICIENT_EVIDENCE, compute_scores, is_abstained
from aivis.variance import summarize_anchor

RANK_MAP = {"1": 1.0, "2": 0.8, "3": 0.6, "default": 0.2}

SCORING_CFG = {
    "rank_map": RANK_MAP,
    "rank_spread_max": 2,
    "list_stability_threshold": 0.7,
    "weights": {"mention": 0.50, "rank": 0.40, "citation": 0.10},
    "confidence_cap": {
        "mention_unstable_cap_to_mention_rate": True,
        "rank_spread_over_max_cap": 0.6,
        "list_stability_below_threshold_cap": 0.7,
        "list_stability_below_0_50_cap": 0.5,
        "any_parse_error_cap": 0.6,
        "list_length_below_expected_min_cap": 0.6,
    },
}


def make_row(
    *,
    run_index: int,
    parse_success: bool,
    brand_mentioned: bool = True,
    brand_rank: int | None = 1,
    raw: str = "1. Asana - good",
) -> VisibilityObj:
    scores = compute_scores(
        brand_mentioned=brand_mentioned,
        brand_rank=brand_rank,
        brand_cited=False,
        rank_map=RANK_MAP,
        parse_success=parse_success,
    )
    return VisibilityObj(
        visibility_id=f"vid-{run_index}",
        client_id="demo",
        client_brand_name="Asana",
        category="Project Management Software",
        prompt_id="PM-D01",
        prompt_text="rank the tools",
        prompt_version="v1.0",
        prompt_family="discovery",
        expected_list_min=1,
        model_provider="anthropic",
        model_name="claude-sonnet-5",
        temperature=None,
        max_tokens=2048,
        run_index=run_index,
        executed_at_utc=datetime.now(timezone.utc),
        request_payload={"stub": True},
        raw_response_text=raw,
        raw_response_json=None,
        response_hash="deadbeef",
        tool_list=[],
        brand_mentioned=brand_mentioned if parse_success else False,
        brand_rank=brand_rank if parse_success else None,
        brand_cited=False,
        brand_citation_domains=[],
        parse_success=parse_success,
        parse_errors=[] if parse_success else ["PE-06"],
        list_length=1 if parse_success else 0,
        has_duplicates=False,
        output_contract_violations=[] if parse_success else ["OCV-01"],
        parse_mode="list" if parse_success else "unknown",
        mention_score=scores.mention,
        rank_score=scores.rank,
        citation_score=scores.citation,
        stability_anchor_key="demo:PM-D01:anthropic:claude-sonnet-5:na:v1.0",
        high_variance_flag=False,
        low_confidence_cap=1.0,
        cap_reasons=[],
    )


# --- row level -------------------------------------------------------------


def test_unparseable_response_abstains_on_every_score():
    s = compute_scores(
        brand_mentioned=False,
        brand_rank=None,
        brand_cited=False,
        rank_map=RANK_MAP,
        parse_success=False,
    )
    assert s.mention == INSUFFICIENT_EVIDENCE
    assert s.rank == INSUFFICIENT_EVIDENCE
    assert s.citation == INSUFFICIENT_EVIDENCE


def test_abstention_is_the_exact_token_and_not_a_number():
    s = compute_scores(False, None, False, RANK_MAP, parse_success=False)
    for value in (s.mention, s.rank, s.citation):
        assert isinstance(value, str)
        assert value == "INSUFFICIENT_EVIDENCE"
        assert not isinstance(value, (int, float))


@pytest.mark.parametrize("raw", ["", "   ", "I cannot answer that request."])
def test_real_unparseable_payloads_abstain_end_to_end(raw):
    _tools, meta = parse_tool_list(raw)
    assert meta["parse_success"] is False
    s = compute_scores(False, None, False, RANK_MAP, parse_success=meta["parse_success"])
    assert is_abstained(s.mention)


def test_absent_brand_in_a_parseable_response_still_scores_zero():
    """0.0 is a measurement. It must not be swallowed by the abstention path."""
    s = compute_scores(False, None, False, RANK_MAP, parse_success=True)
    assert s.mention == 0.0
    assert not is_abstained(s.mention)


def test_abstention_survives_the_jsonl_round_trip():
    row = make_row(run_index=1, parse_success=False)
    revived = VisibilityObj.model_validate_json(row.model_dump_json())
    assert revived.mention_score == INSUFFICIENT_EVIDENCE
    assert revived.rank_score == INSUFFICIENT_EVIDENCE
    assert revived.citation_score == INSUFFICIENT_EVIDENCE


# --- aggregate level -------------------------------------------------------


def test_all_runs_unparseable_makes_the_whole_summary_abstain():
    objs = [make_row(run_index=i, parse_success=False) for i in (1, 2, 3)]
    summ = summarize_anchor(objs, SCORING_CFG)
    assert summ["abstained"] is True
    assert summ["raw_score"] == INSUFFICIENT_EVIDENCE
    assert summ["capped_score"] == INSUFFICIENT_EVIDENCE
    assert summ["runs_scored"] == 0
    assert summ["runs_abstained"] == 3


def test_no_numeric_score_leaks_from_a_fully_abstained_batch():
    """The 0.540 regression: no field may come back as a bare number."""
    objs = [make_row(run_index=i, parse_success=False) for i in (1, 2)]
    summ = summarize_anchor(objs, SCORING_CFG)
    for key in ("raw_score", "capped_score", "confidence_cap", "mention_rate"):
        assert not isinstance(summ[key], (int, float)), f"{key} leaked a number"


def test_partial_batch_scores_only_the_parseable_runs():
    objs = [
        make_row(run_index=1, parse_success=True, brand_mentioned=True, brand_rank=1),
        make_row(run_index=2, parse_success=False),
    ]
    summ = summarize_anchor(objs, SCORING_CFG)
    assert summ["abstained"] is False
    assert summ["run_count"] == 2
    assert summ["runs_scored"] == 1
    assert summ["runs_abstained"] == 1
    # mention_rate is over the runs that parsed, not over all attempts
    assert summ["mention_rate"] == 1.0
    assert isinstance(summ["raw_score"], float)


def test_partial_batch_declares_itself_in_cap_reasons():
    objs = [
        make_row(run_index=1, parse_success=True),
        make_row(run_index=2, parse_success=False),
    ]
    summ = summarize_anchor(objs, SCORING_CFG)
    assert any(r.startswith("PARTIAL_BATCH") for r in summ["cap_reasons"])


def test_clean_batch_reports_no_abstention_and_a_real_score():
    objs = [make_row(run_index=i, parse_success=True) for i in (1, 2, 3)]
    summ = summarize_anchor(objs, SCORING_CFG)
    assert summ["abstained"] is False
    assert summ["runs_abstained"] == 0
    assert isinstance(summ["capped_score"], float)
    assert not any(r.startswith("PARTIAL_BATCH") for r in summ["cap_reasons"])
