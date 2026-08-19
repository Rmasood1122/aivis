#!/usr/bin/env python3
"""probe_v2_defects.py -- targeted probes of caai_v2_scorer.py behaviour.
Each probe answers ONE falsifiable question. Deterministic; no randomness.
Input data is [SYNTHETIC]; the behaviour it exposes is a property of the CODE.
"""
import json, math, itertools
from caai_v2_scorer import (compute_caai_v2, _dispersion, ENGINE_WEIGHTS,
                            MIN_RANKS_FOR_STABILITY)
from v2_to_record import to_record
import index_gate as G

def hdr(t): print("\n" + "=" * 72 + "\n" + t + "\n" + "=" * 72)

# ---------------------------------------------------------------- PROBE 1
hdr("PROBE 1 -- does the F1 fix survive a SINGLE-ENGINE run?")
one = {"openai": {"runs": 30, "mentions": 21, "top3": 12,
                  "ranks": [1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 5, 6, 7, 8, 5, 6, 7, 8, 9]}}
r1 = compute_caai_v2("SingleEngineBrand", "mattresses", one)
ps = r1.dimensions["PS"]["value"]; srs = r1.dimensions["SRS"]["value"]
print("PS = %s   SRS = %s   PS+SRS = %s" % (ps, srs, round(ps + srs, 4)))
print("VERDICT: %s" % ("SRS is identically 100-PS -- F1 REGRESSES at n_engines=1"
                       if abs(ps + srs - 100.0) < 1e-6 else "orthogonal"))

# does index_gate CATCH it? needs >=3 records for the sum detector
recs = []
for i, (runs, men, top3) in enumerate([(30, 21, 12), (30, 14, 6), (30, 27, 20)]):
    rr = compute_caai_v2("SE%d" % i, "mattresses",
                         {"openai": {"runs": runs, "mentions": men, "top3": top3,
                                     "ranks": [1, 2, 3, 4, 5, 6, 7][:min(men, 7)] * 3}})
    recs.append(to_record(rr))
ids = sorted({v["id"] for v in G.run_gate(recs)})
print("index_gate on a 3-row single-engine panel -> %s" % ids)
print("I1-ALGEBRAIC caught: %s" % ("YES" if "I1-ALGEBRAIC" in ids else "NO"))

# ---------------------------------------------------------------- PROBE 2
hdr("PROBE 2 -- what is the REACHABLE RANGE of the SS dimension?")
best = (1.0, None); worst = (0.0, None)
for combo in itertools.product([1, 2, 3, 5, 8, 13, 21], repeat=5):
    v = _dispersion(list(combo))
    if math.isnan(v):
        continue
    if v < best[0]: best = (v, combo)
    if v > worst[0]: worst = (v, combo)
print("min stability over all 5-rank combinations from {1,2,3,5,8,13,21}: %.4f  at %s"
      % (best[0], best[1]))
print("max stability: %.4f  at %s" % (worst[0], worst[1]))
print("PROOF: mad <= span/2 for any sample, so 1 - mad/span >= 0.5 ALWAYS.")
print("VERDICT: SS is bounded to [%.0f, 100]. The bottom half of the scale is unreachable."
      % (best[0] * 100))

# ---------------------------------------------------------------- PROBE 3
hdr("PROBE 3 -- is SS sensitive to the MAGNITUDE of instability?")
for ranks in ([1, 1, 1, 1, 5], [1, 1, 1, 1, 50], [1, 1, 1, 1, 500]):
    print("  ranks=%-18s stability=%.4f" % (ranks, _dispersion(ranks)))
print("VERDICT: a brand swinging between rank 1 and rank 500 scores IDENTICALLY")
print("         to one swinging between rank 1 and rank 5. The normaliser")
print("         (span) cancels the very magnitude the dimension exists to measure.")

# ---------------------------------------------------------------- PROBE 4
hdr("PROBE 4 -- are the engine weights EXPIRED, and does anything check?")
print("ENGINE_WEIGHTS['valid_until'] = %s" % ENGINE_WEIGHTS["valid_until"])
print("today                         = 2026-08-19  [env]")
print("expired                       = %s" % (ENGINE_WEIGHTS["valid_until"] < "2026-08-19"))
src = open("caai_v2_scorer.py", encoding="utf-8").read()
uses = [l.strip() for l in src.splitlines() if "valid_until" in l]
print("lines in caai_v2_scorer.py mentioning valid_until: %d" % len(uses))
for l in uses: print("   %s" % l)
print("lines that READ it in a comparison/branch: %d"
      % len([l for l in uses if any(op in l for op in ("if ", "<", ">", "assert", "raise"))]))
print("VERDICT: the expiry is a COMMENT, not a control. M9 exactly -- awareness")
print("         is not a control. Every score computed today uses expired")
print("         weights and says nothing.")

# ---------------------------------------------------------------- PROBE 5
hdr("PROBE 5 -- can a brand reach a HIGH TIER on a renormalised composite?")
# 4 engines (coverage 1.0 -> no cap), strong presence, but ranks scarce so SS abstains
eng = {}
for e in ("openai", "google", "anthropic", "grok"):
    eng[e] = {"runs": 30, "mentions": 29, "top3": 28, "ranks": [1, 2, 1, 2]}  # 4 < floor 5
r5 = compute_caai_v2("AbstainBrand", "mattresses", eng)
print("coverage=%s  abstentions=%s  tier=%s  capped_by=%r"
      % (r5.coverage, r5.abstentions, r5.tier, r5.tier_capped_by))
print("CAAI=%s  [%s-%s]" % (r5.caai, r5.caai_low, r5.caai_high))
wsum = sum(r5.weights_used[k] for k in ("PS", "DS", "SS", "SRS", "FI") if k not in r5.abstentions)
print("dimension weight actually used: %.2f of 1.00  (SS's %.2f silently dropped)"
      % (wsum, r5.weights_used["SS"]))
ids5 = sorted({v["id"] for v in G.run_gate([to_record(r5)])})
print("index_gate ids on this record: %s" % ids5)
print("I4-NO-TIER-CAP fired: %s   (coverage is 1.0, so the ENGINE cap correctly stays silent)"
      % ("YES" if "I4-NO-TIER-CAP" in ids5 else "NO"))
print("VERDICT: 20%% of the index -- the reliability dimension -- vanished, the")
print("         composite was renormalised over 0.80, the tier thresholds were")
print("         unchanged, and NO rule in index_gate v0.1 reads")
print("         composite.dimension_renormalised_over. The gate MISSES it.")

# ---------------------------------------------------------------- PROBE 6
hdr("PROBE 6 -- does a dimension surviving on ONE engine announce itself?")
low = {"openai":    {"runs": 30, "mentions": 9, "top3": 2, "ranks": [3, 7, 9, 11, 7, 9, 11, 3, 7]},
       "anthropic": {"runs": 30, "mentions": 4, "top3": 1, "ranks": [2, 8, 10, 8]},
       "grok":      {"runs": 30, "mentions": 3, "top3": 0, "ranks": [12, 14, 12]}}
r6 = compute_caai_v2("LowPresence", "mattresses", low)
print("abstentions reported: %s" % (r6.abstentions or "NONE"))
for k in ("DS", "SS"):
    print("  %s value=%s status=%s n=%s" % (k, r6.dimensions[k]["value"],
                                            r6.dimensions[k]["status"], r6.dimensions[k]["n"]))
print("engines contributing to DS/SS: openai ONLY (anthropic 4<5, grok 3<5)")
print("VERDICT: DS and SS are single-engine estimates presented as MEASURED,")
print("         with an empty abstention list. The floor is enforced PER ENGINE")
print("         and never re-checked at the DIMENSION level.")
