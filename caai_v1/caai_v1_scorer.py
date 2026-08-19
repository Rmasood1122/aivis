from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from collections import defaultdict

CAAI_VERSION = "1.0"

# Weights — versioned, never silently changed
WEIGHTS = {
    "version": CAAI_VERSION,
    "PS": 0.25,
    "DS": 0.25,
    "SS": 0.20,
    "SRS": 0.20,
    "FI": 0.10,
}

# Engine weights by market influence (adjustable per category, versioned)
ENGINE_WEIGHTS = {
    "version": CAAI_VERSION,
    "openai": 0.35,      # ChatGPT: largest consumer AI user base
    "google": 0.30,      # Gemini: integrated into search ecosystem
    "anthropic": 0.20,   # Claude: growing, strong in professional use
    "grok": 0.15,        # Grok: smallest but growing via X platform
}


@dataclass
class CAAIDimensions:
    """Individual CAAI dimension scores (0-100 scale)."""
    presence_score: float = 0.0       # PS
    dominance_score: float = 0.0      # DS
    stability_score: float = 0.0      # SS
    suppression_risk: float = 0.0     # SRS
    fragmentation_index: float = 0.0  # FI


@dataclass
class CAAIResult:
    """Complete CAAI computation result."""
    brand: str
    category: str
    caai_version: str = CAAI_VERSION
    caai_raw: float = 0.0             # 0-100
    caai_tier: str = ""               # DOMINANT / STRONG / MODERATE / WEAK / CRITICAL
    dimensions: CAAIDimensions = field(default_factory=CAAIDimensions)
    per_engine: dict = field(default_factory=dict)
    prompt_count: int = 0
    run_count: int = 0
    engine_count: int = 0
    weights_used: dict = field(default_factory=lambda: dict(WEIGHTS))
    engine_weights_used: dict = field(default_factory=lambda: dict(ENGINE_WEIGHTS))


def _engine_weight(provider: str) -> float:
    """Get engine weight, default to equal if unknown."""
    return ENGINE_WEIGHTS.get(provider.lower(), 1.0 / len(ENGINE_WEIGHTS))


def _normalize_0_100(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Normalize a value to 0-100 scale."""
    if max_val == min_val:
        return 50.0
    clamped = max(min_val, min(max_val, value))
    return round(((clamped - min_val) / (max_val - min_val)) * 100, 2)


def compute_caai(
    brand: str,
    category: str,
    compare_files: dict[str, list[dict]] | None = None,
    audit_dir: str | None = None,
    providers: list[str] | None = None,
) -> CAAIResult:
    """
    Compute CAAI v1.0 for a brand from compare JSONL data.

    Args:
        brand: Brand name to score
        category: Category label
        compare_files: Dict of {provider: [records]} pre-loaded data
        audit_dir: Path to directory containing compare_*.jsonl files
        providers: List of provider names to load

    Returns:
        CAAIResult with all dimension scores and composite
    """
    brand_norm = brand.strip().lower()

    # Load data if not pre-loaded
    if compare_files is None:
        compare_files = {}
        if audit_dir:
            audit_path = Path(audit_dir)
            if providers is None:
                providers = [f.stem.replace("compare_", "")
                            for f in audit_path.glob("compare_*.jsonl")]
            for prov in providers:
                fpath = audit_path / f"compare_{prov}.jsonl"
                if fpath.exists():
                    compare_files[prov] = [
                        json.loads(line) for line in fpath.open()
                    ]

    if not compare_files:
        raise ValueError("No compare data found")

    # Collect per-engine metrics
    engines = sorted(compare_files.keys())
    prompt_ids = set()
    total_runs = 0

    engine_data = {}  # provider -> {mention_rates, ranks, top3_count, ...}

    for prov, records in compare_files.items():
        mentions = 0
        total = 0
        ranks = []
        top3 = 0

        for rec in records:
            prompt_ids.add(rec.get("prompt_id", ""))
            total += 1
            total_runs += 1

            # Check brand mention
            mentioned = rec.get("brand_mentioned", False)
            if mentioned:
                mentions += 1
            rank = rec.get("brand_rank")
            if rank is not None:
                ranks.append(rank)
                if rank <= 3:
                    top3 += 1

        mention_rate = mentions / total if total > 0 else 0
        top3_rate = top3 / total if total > 0 else 0

        # Stability: 1 - normalized variance
        if len(ranks) >= 2:
            rank_mean = sum(ranks) / len(ranks)
            variance = sum((r - rank_mean) ** 2 for r in ranks) / len(ranks)
            # Normalize: max reasonable variance is ~25 (spread of 10 over 10 items)
            stability = max(0, 1.0 - (variance / 25.0))
        elif len(ranks) == 1:
            stability = 1.0
        else:
            stability = 0.0  # No ranks = no stability data

        # Suppression: invisibility rate
        invisibility_rate = 1.0 - mention_rate

        engine_data[prov] = {
            "mention_rate": round(mention_rate, 4),
            "top3_rate": round(top3_rate, 4),
            "stability": round(stability, 4),
            "invisibility_rate": round(invisibility_rate, 4),
            "ranks": ranks,
            "runs": total,
            "avg_rank": round(sum(ranks) / len(ranks), 2) if ranks else None,
        }

    # === DIMENSION 1: PRESENCE SCORE (PS) ===
    # Weighted mean of mention_rate across engines
    ps_numerator = sum(
        engine_data[e]["mention_rate"] * _engine_weight(e)
        for e in engines
    )
    ps_denominator = sum(_engine_weight(e) for e in engines)
    ps_raw = ps_numerator / ps_denominator if ps_denominator > 0 else 0
    ps = _normalize_0_100(ps_raw)

    # === DIMENSION 2: DOMINANCE SCORE (DS) ===
    # Weighted top-3 rate across engines
    ds_numerator = sum(
        engine_data[e]["top3_rate"] * _engine_weight(e)
        for e in engines
    )
    ds_denominator = sum(_engine_weight(e) for e in engines)
    ds_raw = ds_numerator / ds_denominator if ds_denominator > 0 else 0
    ds = _normalize_0_100(ds_raw)

    # === DIMENSION 3: STABILITY SCORE (SS) ===
    # Weighted stability across engines
    ss_numerator = sum(
        engine_data[e]["stability"] * _engine_weight(e)
        for e in engines
    )
    ss_denominator = sum(_engine_weight(e) for e in engines)
    ss_raw = ss_numerator / ss_denominator if ss_denominator > 0 else 0
    ss = _normalize_0_100(ss_raw)

    # === DIMENSION 4: SUPPRESSION RISK SCORE (SRS) ===
    # Weighted invisibility rate across engines
    srs_numerator = sum(
        engine_data[e]["invisibility_rate"] * _engine_weight(e)
        for e in engines
    )
    srs_denominator = sum(_engine_weight(e) for e in engines)
    srs_raw = srs_numerator / srs_denominator if srs_denominator > 0 else 0
    srs = _normalize_0_100(srs_raw)

    # === DIMENSION 5: FRAGMENTATION INDEX (FI) ===
    # Cross-model disagreement based on rank spread + score spread
    all_avg_ranks = [
        engine_data[e]["avg_rank"] for e in engines
        if engine_data[e]["avg_rank"] is not None
    ]
    if len(all_avg_ranks) >= 2:
        rank_spread = max(all_avg_ranks) - min(all_avg_ranks)
        # Normalize: max spread of 10 (rank 1 vs rank 10+)
        fi_rank = min(1.0, rank_spread / 10.0)
    else:
        fi_rank = 0.5  # Insufficient data

    # Add mention rate disagreement
    mention_rates = [engine_data[e]["mention_rate"] for e in engines]
    mention_spread = max(mention_rates) - min(mention_rates)

    fi_raw = (fi_rank * 0.7) + (mention_spread * 0.3)
    fi = _normalize_0_100(fi_raw)

    # === COMPOSITE CAAI ===
    caai_raw = (
        (ps * WEIGHTS["PS"]) +
        (ds * WEIGHTS["DS"]) +
        (ss * WEIGHTS["SS"]) +
        ((100 - srs) * WEIGHTS["SRS"]) +
        ((100 - fi) * WEIGHTS["FI"])
    )
    caai_raw = round(caai_raw, 2)

    # Tier assignment
    if caai_raw >= 80:
        tier = "DOMINANT"
    elif caai_raw >= 65:
        tier = "STRONG"
    elif caai_raw >= 45:
        tier = "MODERATE"
    elif caai_raw >= 25:
        tier = "WEAK"
    else:
        tier = "CRITICAL"

    dims = CAAIDimensions(
        presence_score=ps,
        dominance_score=ds,
        stability_score=ss,
        suppression_risk=srs,
        fragmentation_index=fi,
    )

    return CAAIResult(
        brand=brand,
        category=category,
        caai_raw=caai_raw,
        caai_tier=tier,
        dimensions=dims,
        per_engine=engine_data,
        prompt_count=len(prompt_ids),
        run_count=total_runs,
        engine_count=len(engines),
    )


def caai_summary(result: CAAIResult) -> str:
    """Human-readable CAAI summary."""
    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"CAAI v{result.caai_version} — {result.brand}")
    lines.append(f"Category: {result.category}")
    lines.append(f"{'='*60}")
    lines.append(f"")
    lines.append(f"  CAAI Score:  {result.caai_raw:.1f} / 100  [{result.caai_tier}]")
    lines.append(f"")
    lines.append(f"  --- DIMENSIONS ---")
    d = result.dimensions
    lines.append(f"  Presence (PS):       {d.presence_score:6.1f}  (weight: {WEIGHTS['PS']})")
    lines.append(f"  Dominance (DS):      {d.dominance_score:6.1f}  (weight: {WEIGHTS['DS']})")
    lines.append(f"  Stability (SS):      {d.stability_score:6.1f}  (weight: {WEIGHTS['SS']})")
    lines.append(f"  Suppression (SRS):   {d.suppression_risk:6.1f}  (weight: {WEIGHTS['SRS']})")
    lines.append(f"  Fragmentation (FI):  {d.fragmentation_index:6.1f}  (weight: {WEIGHTS['FI']})")
    lines.append(f"")
    lines.append(f"  --- PER ENGINE ---")
    for eng, data in sorted(result.per_engine.items()):
        avg = f"#{data['avg_rank']:.1f}" if data['avg_rank'] else "INVISIBLE"
        lines.append(
            f"  {eng:12s}: mention={data['mention_rate']*100:.0f}%  "
            f"top3={data['top3_rate']*100:.0f}%  stab={data['stability']:.3f}  "
            f"avg={avg}"
        )
    lines.append(f"")
    lines.append(f"  Prompts: {result.prompt_count}  Runs: {result.run_count}  Engines: {result.engine_count}")
    lines.append(f"  Formula: CAAI v{result.caai_version}  Weights: {WEIGHTS}")
    return "\n".join(lines)


def to_json(result: CAAIResult) -> dict:
    """Export CAAI result as JSON-serializable dict."""
    d = asdict(result)
    return d