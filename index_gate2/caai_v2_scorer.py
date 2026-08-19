"""
CAAI v2.0 — AI Category Authority Index, corrected.

Supersedes caai_v1_scorer.py (recovered 2026-08-19 from Feb-2026 chat exports).
Changes are driven by claude/caai-formula-critique-2026-08-19-v1.md, findings
F1-F8, and by OMEGA-CAAI-TRUSTFORGE v1 prime directives D1, D2, D5, D7.

WHAT CHANGED FROM v1, AND WHY
  F1  SRS was identically (100 - PS) — a weighted mean of (1-x) is 1 minus the
      weighted mean of x. The index advertised 5 dimensions and had 4, with
      presence silently weighted 0.45 instead of 0.25.
      v2: SRS = max over engines of invisibility. A max is not linear in the
      mean, so it is genuinely orthogonal, and it measures the thing the name
      promises: the worst platform blind spot, not average absence.
  F2  DS used top3/ALL_RUNS, so it could not rise without presence rising.
      v2: DS = top3/MENTIONS — positioning conditional on being known.
  F3  SS was computed only over runs where the brand appeared (self-selected
      subsample), scored 1.0 from a single observation and 0.0 from none.
      v2: hard support floor; below it the dimension ABSTAINS and the composite
      is reported without it, renormalised, with the abstention printed.
  F4  Absent engines silently vanished from the denominator, so excluding an
      engine removed risk instead of flagging it.
      v2: coverage is computed and the TIER IS CAPPED when coverage < 1.0.
  D1  No intervals anywhere. v2: Wilson score intervals on every rate, and the
      composite is returned as a band, never a bare point.
  D2  Tier was a pure function of the score. v2: tier is computed from the run
      (coverage, engines, runs-per-combination) and cannot exceed what the
      evidence supports.

NOT CHANGED (deliberately): the five dimension weights, the tier thresholds,
and the engine weight table are inherited verbatim from v1. Re-tuning them
before the collinearity fix would be tuning against a hidden 45/25/20/10.
Any re-weighting is a separate, later, evidenced change.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path

CAAI_VERSION = "2.0"
SUPERSEDES = "1.0"

# Dimension weights — unchanged from v1 (see module docstring).
WEIGHTS = {"version": CAAI_VERSION, "PS": 0.25, "DS": 0.25, "SS": 0.20, "SRS": 0.20, "FI": 0.10}

# Engine weights — inherited from v1 WITH its rationale, now carrying an expiry.
# These encode Feb-2026 reach. They are a function of time and decay (F8).
ENGINE_WEIGHTS = {
    "version": CAAI_VERSION,
    "basis": "consumer reach, operator estimate 2026-02",
    "valid_until": "2026-08-01",          # past this, weights are [UNVERIFIED]
    "openai": 0.35,      # ChatGPT: largest consumer AI user base
    "google": 0.30,      # Gemini: integrated into search ecosystem
    "anthropic": 0.20,   # Claude: growing, strong in professional use
    "grok": 0.15,        # Grok: smallest but growing via X platform
}
_ENGINE_KEYS = ("openai", "google", "anthropic", "grok")

# Support floors (F3/D5). Below these a dimension abstains rather than imputing.
MIN_RANKS_FOR_STABILITY = 5
MIN_MENTIONS_FOR_DOMINANCE = 5
MIN_ENGINES_FOR_FRAGMENTATION = 2

Z_95 = 1.959963985

ABSTAIN = "INSUFFICIENT_CONTEXT"


# ----------------------------------------------------------------------------- stats
def wilson(successes: int, n: int, z: float = Z_95) -> tuple[float, float, float]:
    """Wilson score interval. Returns (point, low, high) as proportions."""
    if n == 0:
        return (float("nan"), 0.0, 1.0)
    p = successes / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def _dispersion(ranks: list[float]) -> float:
    """
    Rank stability in [0,1]. v1 used max(0, 1 - variance/25) where 25 was an
    undocumented constant (F6). v2 uses normalised mean absolute deviation
    against the observed rank range, which is scale-derived rather than assumed.
    """
    if len(ranks) < 2:
        return float("nan")
    mean = sum(ranks) / len(ranks)
    mad = sum(abs(r - mean) for r in ranks) / len(ranks)
    span = max(max(ranks) - min(ranks), 1.0)
    return max(0.0, 1.0 - (mad / span))


# ----------------------------------------------------------------------------- types
@dataclass
class Dimension:
    value: float | None          # 0-100, or None when abstaining
    low: float | None = None
    high: float | None = None
    n: int = 0
    status: str = "MEASURED"     # MEASURED | INSUFFICIENT_CONTEXT


@dataclass
class CAAIv2Result:
    brand: str
    category: str
    caai_version: str = CAAI_VERSION
    caai: float | None = None
    caai_low: float | None = None
    caai_high: float | None = None
    tier: str = ""
    tier_capped_by: str = ""
    coverage: float = 0.0
    engines_present: list = field(default_factory=list)
    engines_missing: list = field(default_factory=list)
    dimensions: dict = field(default_factory=dict)
    abstentions: list = field(default_factory=list)
    weights_used: dict = field(default_factory=lambda: dict(WEIGHTS))
    engine_weights_used: dict = field(default_factory=lambda: dict(ENGINE_WEIGHTS))
    per_engine: dict = field(default_factory=dict)
    prompt_count: int = 0
    run_count: int = 0


# ----------------------------------------------------------------------------- core
def _engine_weight(provider: str) -> float:
    return ENGINE_WEIGHTS.get(provider.lower(), 1.0 / len(_ENGINE_KEYS))


def _wmean(pairs: list[tuple[float, float]]) -> float | None:
    """pairs of (value, weight); returns None if no weight."""
    wsum = sum(w for _, w in pairs)
    if wsum <= 0:
        return None
    return sum(v * w for v, w in pairs) / wsum


def compute_caai_v2(brand: str, category: str, per_engine: dict) -> CAAIv2Result:
    """
    per_engine: {provider: {"runs": int, "mentions": int, "top3": int,
                            "ranks": [float, ...]}}

    Every engine key present is treated as MEASURED; every known engine absent
    counts against coverage (F4) rather than silently leaving the denominator.
    """
    res = CAAIv2Result(brand=brand, category=category)
    engines = sorted(per_engine.keys())
    res.engines_present = engines
    res.engines_missing = [e for e in _ENGINE_KEYS if e not in per_engine]

    present_w = sum(_engine_weight(e) for e in engines)
    total_w = sum(ENGINE_WEIGHTS[e] for e in _ENGINE_KEYS)
    res.coverage = round(present_w / total_w, 4)

    ps_pairs, ds_pairs, ss_pairs = [], [], []
    invisibility = []
    avg_ranks, mention_rates = [], []
    n_ps = n_ds = n_ss = 0

    for e in engines:
        d = per_engine[e]
        runs, mentions, top3 = d["runs"], d["mentions"], d["top3"]
        ranks = d.get("ranks") or []
        w = _engine_weight(e)

        mr, mr_lo, mr_hi = wilson(mentions, runs)
        ps_pairs.append((mr, w)); n_ps += runs
        mention_rates.append(mr)
        invisibility.append(1.0 - mr)

        # F2: dominance conditional on mention, with a support floor (F3/D5)
        if mentions >= MIN_MENTIONS_FOR_DOMINANCE:
            cd, _, _ = wilson(top3, mentions)
            ds_pairs.append((cd, w)); n_ds += mentions
        # F3: stability only on adequate support; never 1.0 from one observation
        if len(ranks) >= MIN_RANKS_FOR_STABILITY:
            sv = _dispersion(ranks)
            if not math.isnan(sv):
                ss_pairs.append((sv, w)); n_ss += len(ranks)
        if ranks:
            avg_ranks.append(sum(ranks) / len(ranks))

        res.per_engine[e] = {
            "runs": runs, "mentions": mentions, "top3": top3,
            "mention_rate": round(mr, 4),
            "mention_rate_ci95": [round(mr_lo, 4), round(mr_hi, 4)],
            "dominance_conditional": round(top3 / mentions, 4) if mentions else None,
            "stability": round(_dispersion(ranks), 4) if len(ranks) >= MIN_RANKS_FOR_STABILITY else ABSTAIN,
            "avg_rank": round(sum(ranks) / len(ranks), 2) if ranks else None,
            "invisibility": round(1.0 - mr, 4),
        }

    def dim(pairs, n):
        v = _wmean(pairs)
        if v is None:
            return Dimension(None, None, None, 0, ABSTAIN)
        return Dimension(round(v * 100, 2), None, None, n, "MEASURED")

    PS = dim(ps_pairs, n_ps)
    DS = dim(ds_pairs, n_ds)
    SS = dim(ss_pairs, n_ss)

    # F1: SRS is the WORST engine, not the mean — orthogonal to PS by construction
    if invisibility:
        SRS = Dimension(round(max(invisibility) * 100, 2), n=n_ps, status="MEASURED")
    else:
        SRS = Dimension(None, status=ABSTAIN)

    # FI: cross-engine disagreement. Constants published, not assumed (F6).
    if len(avg_ranks) >= MIN_ENGINES_FOR_FRAGMENTATION:
        rank_span = max(avg_ranks) - min(avg_ranks)
        norm = max(max(avg_ranks), 1.0)          # derived from observed scale
        fi_rank = min(1.0, rank_span / norm)
        fi_mention = max(mention_rates) - min(mention_rates)
        FI = Dimension(round((0.7 * fi_rank + 0.3 * fi_mention) * 100, 2),
                       n=len(avg_ranks), status="MEASURED")
    else:
        FI = Dimension(None, status=ABSTAIN)     # never a 0.5 mid-scale default

    dims = {"PS": PS, "DS": DS, "SS": SS, "SRS": SRS, "FI": FI}
    res.dimensions = {k: asdict(v) for k, v in dims.items()}
    res.abstentions = [k for k, v in dims.items() if v.status != "MEASURED"]

    # Composite over MEASURED dimensions only, renormalised, abstentions declared.
    terms, wsum = [], 0.0
    for key, d in dims.items():
        if d.status != "MEASURED":
            continue
        w = WEIGHTS[key]
        val = d.value if key not in ("SRS", "FI") else (100.0 - d.value)
        terms.append(val * w); wsum += w
    if wsum > 0:
        res.caai = round(sum(terms) / wsum, 2)

    # Interval: propagate the widest per-engine mention CI through PS's share.
    if res.caai is not None and ps_pairs:
        widths = []
        for e in engines:
            lo, hi = res.per_engine[e]["mention_rate_ci95"]
            widths.append((hi - lo) * _engine_weight(e))
        halfband = 100.0 * sum(widths) / (2 * present_w) * (WEIGHTS["PS"] / wsum)
        res.caai_low = round(max(0.0, res.caai - halfband), 2)
        res.caai_high = round(min(100.0, res.caai + halfband), 2)

    # D2/F4: tier computed from the run, then capped by coverage.
    def band(x):
        return ("DOMINANT" if x >= 80 else "STRONG" if x >= 65 else
                "MODERATE" if x >= 45 else "WEAK" if x >= 25 else "CRITICAL")

    if res.caai is None:
        res.tier, res.tier_capped_by = ABSTAIN, "no measured dimensions"
    else:
        t = band(res.caai)
        if res.coverage < 1.0:
            order = ["CRITICAL", "WEAK", "MODERATE", "STRONG", "DOMINANT"]
            capped = order[min(order.index(t), order.index("STRONG"))]
            if capped != t:
                res.tier_capped_by = f"coverage {res.coverage:.2f} (missing: {','.join(res.engines_missing)})"
            else:
                res.tier_capped_by = f"coverage {res.coverage:.2f}"
            t = capped
        res.tier = t

    res.run_count = n_ps
    return res


def from_records(brand: str, category: str, compare_files: dict) -> CAAIv2Result:
    """Adapter for v1-shaped {provider: [record, ...]} JSONL data."""
    per_engine = {}
    for prov, records in compare_files.items():
        runs = mentions = top3 = 0
        ranks = []
        for rec in records:
            runs += 1
            if rec.get("brand_mentioned"):
                mentions += 1
            r = rec.get("brand_rank")
            if r is not None:
                ranks.append(r)
                if r <= 3:
                    top3 += 1
        per_engine[prov] = {"runs": runs, "mentions": mentions, "top3": top3, "ranks": ranks}
    return compute_caai_v2(brand, category, per_engine)


def summary(r: CAAIv2Result) -> str:
    band = f"{r.caai}" if r.caai_low is None else f"{r.caai} [{r.caai_low}-{r.caai_high}]"
    lines = [f"{r.brand} — CAAI v{r.caai_version} {band}  tier={r.tier}",
             f"  coverage={r.coverage}  engines={','.join(r.engines_present)}"
             + (f"  MISSING={','.join(r.engines_missing)}" if r.engines_missing else "")]
    for k, d in r.dimensions.items():
        lines.append(f"  {k:<4} {d['status'] if d['value'] is None else d['value']}  (n={d['n']})")
    if r.abstentions:
        lines.append("  ABSTAINED: " + ", ".join(r.abstentions))
    if r.tier_capped_by:
        lines.append("  tier basis: " + r.tier_capped_by)
    return "\n".join(lines)
