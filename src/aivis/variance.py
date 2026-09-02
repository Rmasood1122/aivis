from __future__ import annotations

import itertools
from statistics import mean

from .models import VisibilityObj
from .scorer import INSUFFICIENT_EVIDENCE


def jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity between two sets."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def compute_list_stability(objs: list[VisibilityObj]) -> float:
    """Mean pairwise Jaccard similarity of tool name_norm sets across runs."""
    sets = [{t.name_norm for t in o.tool_list} for o in objs]
    if len(sets) < 2:
        return 1.0
    sims = [jaccard(sets[i], sets[j]) for i, j in itertools.combinations(range(len(sets)), 2)]
    return float(mean(sims)) if sims else 1.0


def _abstained_summary(runs: int, abstained: int, reason: str) -> dict:
    """
    Every field a caller might format is the exact token, so there is no
    numeric field left for a downstream formatter to print as if it were a
    measurement.
    """
    return {
        "run_count": runs,
        "runs_scored": 0,
        "runs_abstained": abstained,
        "abstained": True,
        "abstain_reason": reason,
        "mention_rate": INSUFFICIENT_EVIDENCE,
        "mention_stable": INSUFFICIENT_EVIDENCE,
        "rank_values": [],
        "rank_spread": INSUFFICIENT_EVIDENCE,
        "rank_stable": INSUFFICIENT_EVIDENCE,
        "citation_rate": INSUFFICIENT_EVIDENCE,
        "list_stability_score": INSUFFICIENT_EVIDENCE,
        "list_stable": INSUFFICIENT_EVIDENCE,
        "high_variance": INSUFFICIENT_EVIDENCE,
        "confidence_cap": INSUFFICIENT_EVIDENCE,
        "cap_reasons": [reason],
        "raw_score": INSUFFICIENT_EVIDENCE,
        "capped_score": INSUFFICIENT_EVIDENCE,
    }


from .intervals import wilson  # wilson-v1


def _rates(scored: list[VisibilityObj], scoring_cfg: dict) -> dict:
    """Per-batch rates and stability flags, computed over parsed rows only."""
    n = len(scored)

    mentioned = [o.brand_mentioned for o in scored]
    mention_n = sum(1 for x in mentioned if x)
    mention_rate = mention_n / n
    _, mr_lo, mr_hi = wilson(mention_n, n)  # wilson-v1
    mention_stable = mention_rate in (0.0, 1.0)

    ranks = [o.brand_rank for o in scored if o.brand_mentioned and o.brand_rank is not None]
    rank_spread = (max(ranks) - min(ranks)) if len(ranks) >= 2 else 0
    rank_stable = rank_spread <= int(scoring_cfg["rank_spread_max"])

    list_stability = compute_list_stability(scored)
    list_stable = list_stability >= float(scoring_cfg["list_stability_threshold"])

    citation_rate = (
        sum(1 for o in scored if o.brand_mentioned and o.brand_cited) / mention_n
        if mention_n > 0
        else None
    )

    # Parse health (soft defects only; hard failures already excluded)
    any_parse_error = any(len(o.parse_errors) > 0 or not o.parse_success for o in scored)
    below_min = any(o.list_length < o.expected_list_min for o in scored)

    return {
        "n": n,
        "mention_rate": mention_rate,
        "mr_lo": mr_lo,
        "mr_hi": mr_hi,
        "mention_stable": mention_stable,
        "ranks": ranks,
        "rank_spread": rank_spread,
        "rank_stable": rank_stable,
        "list_stability": list_stability,
        "list_stable": list_stable,
        "citation_rate": citation_rate,
        "any_parse_error": any_parse_error,
        "below_min": below_min,
    }


def _caps(r: dict, scoring_cfg: dict, runs: int) -> tuple[float, list[str]]:
    """Confidence cap: rules applied in order, min wins. Order preserved from v1."""
    cap = 1.0
    reasons: list[str] = []
    caps = scoring_cfg["confidence_cap"]

    # Rule 1: mention instability
    if caps.get("mention_unstable_cap_to_mention_rate", True) and not r["mention_stable"]:
        cap = min(cap, r["mention_rate"])
        reasons.append(f"MENTION_UNSTABLE({r['mention_rate']:.2f})")

    # Rule 2: rank spread
    if not r["rank_stable"]:
        cap = min(cap, float(caps["rank_spread_over_max_cap"]))
        reasons.append(f"RANK_SPREAD({r['rank_spread']})")

    # Rule 3: list stability below threshold
    if not r["list_stable"]:
        cap = min(cap, float(caps["list_stability_below_threshold_cap"]))
        reasons.append(f"LIST_STABILITY({r['list_stability']:.2f})")

    # Rule 4: list stability hard floor
    if r["list_stability"] < 0.5:
        cap = min(cap, float(caps["list_stability_below_0_50_cap"]))
        reasons.append(f"LIST_STABILITY_HARD({r['list_stability']:.2f})")

    # Rule 5: parse errors
    if r["any_parse_error"]:
        cap = min(cap, float(caps["any_parse_error_cap"]))
        reasons.append("PARSE_ERROR")

    # Rule 6: list length below expected minimum
    if r["below_min"]:
        cap = min(cap, float(caps["list_length_below_expected_min_cap"]))
        reasons.append("BELOW_MIN_LIST")

    # Rule 7: some runs abstained. The score that follows describes the runs
    # that parsed, not the runs that were attempted. Say so in the cap reasons
    # so it cannot be read as a clean measurement of the whole batch.
    if runs - r["n"] > 0:
        reasons.append(f"PARTIAL_BATCH({r['n']}/{runs}_scored)")

    return cap, reasons


def _composite(scored: list[VisibilityObj], scoring_cfg: dict, reasons: list[str]) -> float:
    """Weighted composite over parsed rows. Appends RANK_WITHDRAWN when it fires."""
    weights = scoring_cfg.get("weights", {"mention": 0.50, "rank": 0.40, "citation": 0.10})
    # P3 (register): rank_score is WITHDRAWN from the composite until order rotation
    # exists — position bias is unmeasured, so the rank term ships above its rung.
    # Raw rank data (rank_values, rank_spread, rank_stable) still reports: the data
    # is measured, the SCORE was the claim. Withdrawal is renormalized and labelled,
    # never silent. Revert when B3 (rotation) lands.
    if float(weights.get("rank", 0.0)) > 0.0:
        _keep = float(weights.get("mention", 0.0)) + float(weights.get("citation", 0.0))
        if _keep > 0.0:
            weights = {"mention": float(weights.get("mention", 0.0)) / _keep,
                       "rank": 0.0,
                       "citation": float(weights.get("citation", 0.0)) / _keep}
        else:
            weights = {"mention": 0.0, "rank": 0.0, "citation": 0.0}
        reasons.append("RANK_WITHDRAWN(order_rotation_absent;weights_renormalized)")
    return (
        mean([float(o.mention_score) for o in scored]) * weights["mention"]
        + mean([float(o.rank_score) for o in scored]) * weights["rank"]
        + mean([float(o.citation_score) for o in scored]) * weights["citation"]
    )


def summarize_anchor(objs: list[VisibilityObj], scoring_cfg: dict) -> dict:
    """
    Compute variance summary for a set of runs sharing the same
    stability_anchor_key.

    D6 fix, aggregate half. Rows whose response could not be parsed are
    EXCLUDED from every statistic rather than folded in as zeros. Folding them
    in is what let a PARSE_ERROR run leave the machine as a confident 0.540.

    If no row parsed, the whole summary abstains. If some rows parsed, the
    statistics are computed over those rows only and the counts are reported
    separately, so a reader can always see the denominator that was actually
    used.
    """
    runs = len(objs)
    if runs == 0:
        return {"run_count": 0, "error": "no objects"}

    scored = [o for o in objs if o.parse_success]
    n_abstained = runs - len(scored)

    if not scored:
        return _abstained_summary(runs, n_abstained, "NO_PARSEABLE_RUN")

    r = _rates(scored, scoring_cfg)
    cap, reasons = _caps(r, scoring_cfg, runs)
    raw_score = _composite(scored, scoring_cfg, reasons)
    capped_score = raw_score * cap

    high_variance = (
        (not r["mention_stable"]) or (not r["rank_stable"]) or (not r["list_stable"])
    )

    return {
        "run_count": runs,
        "runs_scored": r["n"],
        "runs_abstained": n_abstained,
        "mention_rate_ci95": [round(r["mr_lo"], 4), round(r["mr_hi"], 4)],  # wilson-v1
        "abstained": False,
        "mention_rate": r["mention_rate"],
        "mention_stable": r["mention_stable"],
        "rank_values": r["ranks"],
        "rank_spread": r["rank_spread"],
        "rank_stable": r["rank_stable"],
        "citation_rate": r["citation_rate"],
        "list_stability_score": r["list_stability"],
        "list_stable": r["list_stable"],
        "high_variance": high_variance,
        "confidence_cap": cap,
        "cap_reasons": reasons,
        "raw_score": raw_score,
        "capped_score": capped_score,
    }
