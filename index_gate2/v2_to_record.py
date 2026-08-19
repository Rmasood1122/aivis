#!/usr/bin/env python3
"""v2_to_record.py -- faithful adapter: CAAIv2Result -> INDEXFORGE <output_schema>.

PROVENANCE DISCIPLINE. Three classes of field, kept separate on purpose. If
this adapter invents a field v2 does not emit, the gate result is laundered and
worthless.

  [FROM v2 OUTPUT]  value, status, n, low, high, coverage, engines_present,
                    engines_missing, caai, caai_low, caai_high, tier,
                    tier_capped_by, weights_used, abstentions
  [FROM v2 SOURCE]  label, estimator, denominator, min_n, constants -- read out
                    of caai_v2_scorer.py by hand and declared here, because v2
                    does not emit them. Each is quoted against a line of code.
  [ABSENT IN v2]    pairwise_r, prescription, separation, temporal, and every
                    dimension-level ci_low/ci_high. These are emitted EMPTY,
                    not filled. That absence IS the finding.
"""
from caai_v2_scorer import (compute_caai_v2, WEIGHTS, ENGINE_WEIGHTS,
                            MIN_RANKS_FOR_STABILITY, MIN_MENTIONS_FOR_DOMINANCE,
                            MIN_ENGINES_FOR_FRAGMENTATION)

# [FROM v2 SOURCE] -- each entry cites the construct site in caai_v2_scorer.py
DIM_META = {
    "PS": dict(label="Presence Score",
               estimator="weighted_mean_e(wilson(mentions_e, runs_e).point)",
               denominator="runs",
               min_n=None,          # no MIN_RUNS_FOR_PRESENCE constant exists in v2
               constants=[]),
    "DS": dict(label="Dominance Strength",
               estimator="weighted_mean_e(wilson(top3_e, mentions_e).point)",
               denominator="mentions",
               min_n=MIN_MENTIONS_FOR_DOMINANCE,
               constants=[]),
    "SS": dict(label="Stability Score",
               estimator="weighted_mean_e(1 - mad(ranks_e) / span(ranks_e))",
               denominator="ranks",
               min_n=MIN_RANKS_FOR_STABILITY,
               constants=[{"name": "span_floor", "value": 1.0}]),   # max(range, 1.0)
    "SRS": dict(label="Suppression Risk (worst-engine invisibility)",
                estimator="max_e(1 - mention_rate_e)",
                denominator="runs",
                min_n=None,         # no floor guards the max
                constants=[]),
    "FI": dict(label="Fragmentation Index",
               estimator="0.7 * (rank_span / max_avg_rank) + 0.3 * mention_rate_spread",
               denominator="engines",
               min_n=MIN_ENGINES_FOR_FRAGMENTATION,
               constants=[{"name": "fi_rank_split", "value": 0.7},
                          {"name": "fi_mention_split", "value": 0.3},
                          {"name": "fi_rank_normaliser", "value": "max(max(avg_ranks), 1.0)"}]),
}

# [FROM v2 SOURCE] composite-level constants: the five dimension weights carry no
# derivation ("inherited verbatim from v1"); the engine weights carry a written
# per-engine rationale AND an expiry, so they map to est_basis + review_date.
def _composite_constants():
    out = [{"name": "w_%s" % k, "value": WEIGHTS[k]}
           for k in ("PS", "DS", "SS", "SRS", "FI")]
    for e in ("openai", "google", "anthropic", "grok"):
        out.append({"name": "engine_w_%s" % e, "value": ENGINE_WEIGHTS[e],
                    "est_basis": ENGINE_WEIGHTS["basis"],
                    "review_date": ENGINE_WEIGHTS["valid_until"]})
    out += [{"name": "tier_threshold_DOMINANT", "value": 80},
            {"name": "tier_threshold_STRONG", "value": 65},
            {"name": "tier_threshold_MODERATE", "value": 45},
            {"name": "tier_threshold_WEAK", "value": 25}]
    return out


def _sources(r):
    """[DERIVED FROM v2 OUTPUT] How many engines actually fed each dimension.
    v2 does not emit this; it is recomputed here from r.per_engine using v2's
    own floor constants. Without it, index_gate cannot re-check a per-engine
    floor at the dimension level (v2 probe 6)."""
    elig = len(r.per_engine)
    used = {"PS": elig, "SRS": elig}
    used["DS"] = sum(1 for e in r.per_engine.values()
                     if e["mentions"] >= MIN_MENTIONS_FOR_DOMINANCE)
    used["SS"] = sum(1 for e in r.per_engine.values() if e["stability"] != "INSUFFICIENT_CONTEXT")
    used["FI"] = sum(1 for e in r.per_engine.values() if e["avg_rank"] is not None)
    return used, elig


def to_record(r):
    used, elig = _sources(r)
    dims = []
    for name, d in r.dimensions.items():
        meta = DIM_META[name]
        dims.append({
            "name": name,
            "label": meta["label"],
            "estimator": meta["estimator"],
            "denominator": meta["denominator"],
            "min_n": meta["min_n"],
            "constants": meta["constants"],
            # [FROM v2 OUTPUT]
            "status": "OK" if d["status"] == "MEASURED" else d["status"],
            "value": d["value"],
            "ci_low": d["low"],        # v2 hardcodes None at every site
            "ci_high": d["high"],
            "n": d["n"],
            # [DERIVED FROM v2 OUTPUT] -- see _sources()
            "sources_used": used[name],
            "sources_eligible": elig,
            # [ABSENT IN v2] -- no prescription key is emitted at all
        })
    return {
        "index_version": r.caai_version,
        "supersedes": "1.0",
        "subject": r.brand,
        "dimensions": dims,
        "pairwise_r": {},                       # [ABSENT IN v2]
        "composite": {
            "value": r.caai, "ci_low": r.caai_low, "ci_high": r.caai_high,
            "weights_used": {k: v for k, v in r.weights_used.items() if k != "version"},
            "renormalised_over": r.coverage,    # engine weights normalise over present engines
            "full_denominator_value": None,     # [ABSENT IN v2]
            "constants": _composite_constants(),
            # recorded for the reader; index_gate v0.1 HAS NO RULE THAT READS THIS:
            "dimension_renormalised_over": round(
                sum(r.weights_used[k] for k in ("PS", "DS", "SS", "SRS", "FI")
                    if k not in r.abstentions), 4),
            "dimensions_abstained": r.abstentions,
        },
        "coverage": {
            "present": r.engines_present, "missing": r.engines_missing,
            "ratio": r.coverage,
            "tier_cap_applied": bool(r.tier_capped_by),
        },
        "tier": {"value": r.tier, "computed_from": "composite point estimate",
                 "capped_by": r.tier_capped_by or None},
        "separation": [],                       # [ABSENT IN v2]
        "temporal": {},                         # [ABSENT IN v2]
    }
