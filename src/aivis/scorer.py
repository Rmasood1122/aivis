from __future__ import annotations

from typing import Literal, NamedTuple, Union

# The exact token. Nothing else is a valid abstention: not None, not 0.0,
# not 0.5, not "n/a", not "approximately". One string, compared by equality.
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

ScoreValue = Union[float, Literal["INSUFFICIENT_EVIDENCE"]]


def is_abstained(value: object) -> bool:
    """True when a score-like value is the abstention token."""
    return value == INSUFFICIENT_EVIDENCE


class Scores(NamedTuple):
    mention: ScoreValue
    rank: ScoreValue
    citation: ScoreValue


def rank_score_from_rank(rank: int | None, rank_map: dict) -> float:
    if rank is None:
        return 0.0
    return float(rank_map.get(str(rank), rank_map.get("default", 0.0)))


def compute_scores(
    brand_mentioned: bool,
    brand_rank: int | None,
    brand_cited: bool,
    rank_map: dict,
    *,
    parse_success: bool = True,
) -> Scores:
    """
    D6 fix.

    When the response could not be parsed into a tool list at all, every score
    is the exact token INSUFFICIENT_EVIDENCE.

    The distinction that matters: 0.0 is a measurement -- it says "we read the
    model's answer and the brand was not in it". An unparseable response is not
    a measurement of anything, and scoring it 0.0 launders a failure of the
    harness into a finding about the customer's brand.

    Soft parse defects (PE-03 missing rationale, PE-04 duplicate entry) are NOT
    abstention. The list was read; it was merely imperfect. Those continue to
    flow through the confidence cap in variance.summarize_anchor.
    """
    if not parse_success:
        return Scores(
            mention=INSUFFICIENT_EVIDENCE,
            rank=INSUFFICIENT_EVIDENCE,
            citation=INSUFFICIENT_EVIDENCE,
        )

    mention_score = 1.0 if brand_mentioned else 0.0
    rank_score = rank_score_from_rank(brand_rank, rank_map) if brand_mentioned else 0.0
    citation_score = 1.0 if (brand_mentioned and brand_cited) else 0.0
    return Scores(mention=mention_score, rank=rank_score, citation=citation_score)
