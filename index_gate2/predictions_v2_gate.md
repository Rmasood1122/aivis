# PRE-REGISTERED PREDICTIONS — index_gate v0.1 vs caai_v2_scorer.py
# Written 2026-08-19 BEFORE the gate was run. Hindsight cannot edit this file.

## P-A. INDEXFORGE's own pre-registered prediction [QUOTED: OMEGA-INDEXFORGE-v1.0,
## "HOW THIS FORGE IS FALSIFIED"]:
##   "v2 should fail I1 partially (SRS/PS now orthogonal but DS still shares
##    presence), I7 fully (no version pinning), and I9 fully (no prescriptive
##    mapping)."
P-A1  I1 fires (partially)                        -> PREDICT FIRE
P-A2  I1's stated CAUSE is "DS still shares presence" -> PREDICT WRONG.
      v2 changed DS to top3/mentions (F2 fix). The FORGE's prediction of the
      MECHANISM looks falsified even if the RULE fires.
P-A3  I7 fires fully (no model_id/snapshot/api anywhere) -> PREDICT FIRE
P-A4  I9 fires fully (no prescription field)      -> PREDICT FIRE

## P-B. My predictions, formed by READING THE SOURCE (not blind - declared).
P-B1  I5-NO-INTERVAL fires on ALL FIVE dimensions. Dimension.low/high are
      hardcoded None at every construction site in dim() and the SRS/FI
      branches. The module docstring claims "Wilson score intervals on every
      rate" (D1). PREDICT: the docstring is false about its own output.
P-B2  I1-NO-MATRIX fires on all 10 pairs. v2 emits no pairwise_r.
P-B3  I1-ALGEBRAIC fires on PS|SRS for any SINGLE-ENGINE panel, because
      max_e(1-mr) over one engine IS 1-mr. The F1 fix holds only at n_engines>=2.
P-B4  I8 fires. valid_until="2026-08-01" is 18 days PAST today's date and
      nothing in the code reads it. 0.7/0.3 in FI is unchanged from v1 and
      still underived, though the comment says "Constants published, not
      assumed (F6)".
P-B5  I4 does NOT fire on engines (v2 genuinely fixed F4: coverage computed,
      tier capped). PREDICT the engine-level fix is real.
P-B6  But the SAME failure class reappears one level up: the composite
      renormalises over ABSTAINED DIMENSIONS (wsum), with tier thresholds
      unchanged and no dimension-level tier cap. index_gate v0.1 has NO RULE
      for this. PREDICT: the gate MISSES it -> new fixture required (STAGE 0).
P-B7  SS is structurally bounded to [50,100]: MAD <= range/2, so
      1 - mad/span >= 0.5 always. Half the dimension's range is unreachable.
      index_gate v0.1 has NO RULE for this. PREDICT: MISSED.
P-B8  SS is scale-free in the wrong way: ranks [1,1,1,1,5] and [1,1,1,1,50]
      score IDENTICALLY. PREDICT: MISSED by the gate.

## SCORED 2026-08-19, after the runs. [MEASURED: container]
P-A1 I1 fires                      -> RIGHT (I1-NO-MATRIX, 10 pairs)
P-A2 cause "DS still shares presence" -> RIGHT that the FORGE was WRONG.
     I2 is the ONLY rule of nine that stays SILENT on v2. F2 is genuinely
     fixed: DS = top3/mentions. The FORGE's predicted MECHANISM is falsified;
     its predicted RULE fires for an entirely different reason (no r matrix).
P-A3 I7 fires fully                -> RIGHT (no temporal block at all)
P-A4 I9 fires fully                -> RIGHT (5 of 5 dimensions)
P-B1 I5 on all five dimensions     -> RIGHT (20 violations across 4 rows)
P-B2 I1-NO-MATRIX on all 10 pairs  -> RIGHT
P-B3 I1-ALGEBRAIC at n_engines=1   -> RIGHT (PS+SRS = 100.0 exactly; caught)
P-B4 I8 fires                      -> RIGHT, and worse than predicted: v0.1
     could NOT see the expired weights. New rule I8-CONSTANT-EXPIRED added.
P-B5 engine-level F4 fix is real   -> HALF RIGHT. tier cap works
     (I4-NO-TIER-CAP silent on v2, fires on v1). But I4-MISSING-SILENT still
     fires: no full-denominator companion is published.
P-B6 dimension renorm MISSED by gate -> RIGHT. Fixed in v0.2 (I4-DIM-RENORM).
P-B7 SS bounded to [50,100], MISSED  -> RIGHT on both. Measured floor 0.52.
     NOT gateable; logged as a construct finding, not a rule.
P-B8 SS scale-invariant, MISSED      -> RIGHT on both. ranks [1,1,1,1,5] and
     [1,1,1,1,500] both score 0.6800. NOT gateable; construct finding.

SCORE: 12 of 12 directionally right. Two (P-B7, P-B8) are predictions that the
GATE WOULD FAIL, and it did -- those are not wins for the gate.
