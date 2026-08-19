#!/usr/bin/env python3
"""build_v2_panel.py -- run caai_v2_scorer on a panel and emit INDEXFORGE records.

THE INPUT DATA IS [SYNTHETIC]. It is constructed to exercise caai_v2_scorer.py,
not to describe any brand. Two consequences, stated so neither is inferred:
  - Any DEFECT the gate finds is a real defect in the CODE (the code is the
    thing under test, and it is real).
  - Any NUMBER produced is a property of this fixture, not of Purple, Casper,
    Tempur-Pedic or Saatva. No score here may be quoted about a brand.

Panel shape mirrors the real Feb-2026 run: google/Gemini absent (rate-limited),
3 runs per prompt-brand-engine x 10 prompts = 30 runs per engine.
"""
import json
from caai_v2_scorer import compute_caai_v2, summary
from v2_to_record import to_record


def ranks_for(mentions, top3, lo_pool, hi_pool):
    """Deterministic rank list: `top3` ranks drawn from lo_pool (all <=3), the
    rest from hi_pool (all >3). No randomness -- the panel must replay."""
    out = []
    for i in range(top3):
        out.append(lo_pool[i % len(lo_pool)])
    for i in range(mentions - top3):
        out.append(hi_pool[i % len(hi_pool)])
    return out


# brand -> engine -> (runs, mentions, top3, lo_pool, hi_pool)
PANEL = {
    "Purple": {
        "openai":    (30, 26, 18, [1, 2, 3], [4, 5]),
        "anthropic": (30, 24, 14, [1, 2, 3], [4, 6, 7]),
        "grok":      (30, 14, 8,  [2, 3],    [5, 9]),
    },
    "Casper": {
        "openai":    (30, 24, 9,  [2, 3],    [4, 5, 6]),
        "anthropic": (30, 24, 3,  [3],       [5, 6, 7, 8]),   # 80% mention, 12.5% top-3
        "grok":      (30, 12, 4,  [1, 3],    [6, 7]),
    },
    "Tempur-Pedic": {
        "openai":    (30, 20, 10, [1, 3],    [4, 8]),
        "anthropic": (30, 18, 8,  [2, 3],    [5, 9]),
        "grok":      (30, 12, 9,  [1, 2, 3], [4]),            # high conditional top-3
    },
    "Saatva": {                                               # low-presence brand
        "openai":    (30, 9, 2,  [3],        [7, 9, 11]),
        "anthropic": (30, 4, 1,  [2],        [8, 10]),        # below DS floor (5)
        "grok":      (30, 3, 0,  [1],        [12, 14]),       # below DS and SS floors
    },
}

records, results = [], []
for brand, engines in PANEL.items():
    per_engine = {}
    for e, (runs, mentions, top3, lo, hi) in engines.items():
        per_engine[e] = {"runs": runs, "mentions": mentions, "top3": top3,
                         "ranks": ranks_for(mentions, top3, lo, hi)}
    r = compute_caai_v2(brand, "mattresses", per_engine)
    results.append(r)
    rec = to_record(r)
    path = "caai_v2_%s.json" % brand.lower().replace("-", "_")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=2)
    records.append(path)

print("=== caai_v2_scorer.py OUTPUT (input data is SYNTHETIC) ===")
for r in results:
    print(summary(r))
    print()
print("records written: %s" % " ".join(records))
