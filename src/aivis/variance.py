from __future__ import annotations

import itertools
from statistics import mean

from .models import VisibilityObj


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


def summarize_anchor(objs: list[VisibilityObj], scoring_cfg: dict) -> dict:
    """
    Compute variance summary for a set of runs sharing the same
    stability_anchor_key. Returns dict with all variance metrics,
    confidence cap, and cap reasons.
    """
    runs = len(objs)
    if runs == 0:
        return {"run_count": 0, "error": "no objects"}

    # --- Mention stability ---
    mentioned = [o.brand_mentioned for o in objs]
    mention_rate = sum(1 for x in mentioned if x) / runs
    mention_stable = mention_rate in (0.0, 1.0)

    # --- Rank stability ---
    ranks = [o.brand_rank for o in objs if o.brand_mentioned and o.brand_rank is not None]
    rank_spread = (max(ranks) - min(ranks)) if len(ranks) >= 2 else 0
    rank_stable = rank_spread <= int(scoring_cfg["rank_spread_max"])

    # --- List composition stability ---
    list_stability = compute_list_stability(objs)
    list_stable = list_stability >= float(scoring_cfg["list_stability_threshold"])

    # --- Citation rate ---
    mentioned_count = sum(1 for x in mentioned if x)
    citation_rate = (
        sum(1 for o in objs if o.brand_mentioned and o.brand_cited) / mentioned_count
        if mentioned_count > 0
        else None
    )

    # --- Parse health ---
    any_parse_error = any(len(o.parse_errors) > 0 or not o.parse_success for o in objs)
    below_min = any(o.list_length < o.expected_list_min for o in objs)

    # --- High variance flag ---
    high_variance = (not mention_stable) or (not rank_stable) or (not list_stable)

    # --- Confidence cap computation (rules applied in order, min wins) ---
    cap = 1.0
    reasons: list[str] = []
    caps = scoring_cfg["confidence_cap"]

    # Rule 1: mention instability
    if caps.get("mention_unstable_cap_to_mention_rate", True) and not mention_stable:
        cap = min(cap, mention_rate)
        reasons.append(f"MENTION_UNSTABLE({mention_rate:.2f})")

    # Rule 2: rank spread
    if not rank_stable:
        cap = min(cap, float(caps["rank_spread_over_max_cap"]))
        reasons.append(f"RANK_SPREAD({rank_spread})")

    # Rule 3: list stability below threshold
    if not list_stable:
        cap = min(cap, float(caps["list_stability_below_threshold_cap"]))
        reasons.append(f"LIST_STABILITY({list_stability:.2f})")

    # Rule 4: list stability hard floor
    if list_stability < 0.5:
        cap = min(cap, float(caps["list_stability_below_0_50_cap"]))
        reasons.append(f"LIST_STABILITY_HARD({list_stability:.2f})")

    # Rule 5: parse errors
    if any_parse_error:
        cap = min(cap, float(caps["any_parse_error_cap"]))
        reasons.append("PARSE_ERROR")

    # Rule 6: list length below expected minimum
    if below_min:
        cap = min(cap, float(caps["list_length_below_expected_min_cap"]))
        reasons.append("BELOW_MIN_LIST")

    # --- Composite score ---
    weights = scoring_cfg.get("weights", {"mention": 0.50, "rank": 0.40, "citation": 0.10})
    raw_score = (
        mean([o.mention_score for o in objs]) * weights["mention"]
        + mean([o.rank_score for o in objs]) * weights["rank"]
        + mean([o.citation_score for o in objs]) * weights["citation"]
    )
    capped_score = raw_score * cap

    return {
        "run_count": runs,
        "mention_rate": mention_rate,
        "mention_stable": mention_stable,
        "rank_values": ranks,
        "rank_spread": rank_spread,
        "rank_stable": rank_stable,
        "citation_rate": citation_rate,
        "list_stability_score": list_stability,
        "list_stable": list_stable,
        "high_variance": high_variance,
        "confidence_cap": cap,
        "cap_reasons": reasons,
        "raw_score": raw_score,
        "capped_score": capped_score,
    }
