"""
Runs CAAI v1.0 and v2.0 against the SHIPPED report's own data
(ai score.pdf, CAAI v1.0, 2026-02-23) and prints the movement per brand.

HONEST LIMITATION, stated up front: the raw per-run JSONL is not available —
only the report's aggregate tables. So PS, DS, SRS and FI are recomputed
exactly, and STABILITY IS CARRIED OVER FROM v1 UNCHANGED. The F3 fix (support
floors on a self-selected subsample) therefore contributes ZERO to the deltas
below. Real v2 movement is >= what is shown here, not <=.
"""
import math
from caai_v2_scorer import wilson

W = {"chatgpt": 0.35, "claude": 0.25, "grok": 0.20}      # gemini 0.30 excluded
TW = sum(W.values())
EW = {k: v / TW for k, v in W.items()}                    # 0.4375 / 0.3125 / 0.25
RUNS = 30                                                 # 10 prompts x 3 runs

# [MEASURED: ai score.pdf, PER-ENGINE AUTHORITY BREAKDOWN tables]
D = {
 "Purple":       {"chatgpt": (.900, .600, .917, 3.6), "claude": (.900, .900, .969, 2.1), "grok": (.467, .200, .953, 3.8)},
 "Casper":       {"chatgpt": (.667, .433, .831, 3.4), "claude": (.800, .100, .976, 4.1), "grok": (.700, .533, .960, 2.6)},
 "Tempur-Pedic": {"chatgpt": (.600, .367, .675, 3.4), "claude": (.800, .767, .966, 1.9), "grok": (.400, .300, .932, 2.2)},
}
PUBLISHED = {"Purple": 76.8, "Casper": 67.8, "Tempur-Pedic": 63.8}
WT = {"PS": .25, "DS": .25, "SS": .20, "SRS": .20, "FI": .10}

def wm(f):  return sum(f(e) * EW[e] for e in EW)
def tier(x): return ("DOMINANT" if x>=80 else "STRONG" if x>=65 else
                     "MODERATE" if x>=45 else "WEAK" if x>=25 else "CRITICAL")

print("=" * 96)
print("CAAI v1.0 vs v2.0 — recomputed on the shipped report's own numbers")
print("=" * 96)
rows = []
for b, eng in D.items():
    mr  = {e: eng[e][0] for e in eng}
    t3  = {e: eng[e][1] for e in eng}
    st  = {e: eng[e][2] for e in eng}
    ar  = {e: eng[e][3] for e in eng}

    PS   = 100 * wm(lambda e: mr[e])
    DS1  = 100 * wm(lambda e: t3[e])                       # v1: top3 / ALL runs
    DS2  = 100 * wm(lambda e: t3[e] / mr[e])               # v2: top3 / MENTIONS
    SS   = 100 * wm(lambda e: st[e])                       # carried over (see docstring)
    SRS1 = 100 * wm(lambda e: 1 - mr[e])                   # v1: weighted mean  == 100-PS
    SRS2 = 100 * max(1 - mr[e] for e in eng)               # v2: worst engine
    span = max(ar.values()) - min(ar.values())
    FI1  = 100 * (0.7 * min(1, span / 10.0) + 0.3 * (max(mr.values()) - min(mr.values())))
    FI2  = 100 * (0.7 * min(1, span / max(ar.values())) + 0.3 * (max(mr.values()) - min(mr.values())))

    v1 = PS*WT["PS"] + DS1*WT["DS"] + SS*WT["SS"] + (100-SRS1)*WT["SRS"] + (100-FI1)*WT["FI"]
    v2 = PS*WT["PS"] + DS2*WT["DS"] + SS*WT["SS"] + (100-SRS2)*WT["SRS"] + (100-FI2)*WT["FI"]

    # Wilson band on the presence term (n=30 per engine)
    halfw = sum((wilson(round(mr[e]*RUNS), RUNS)[2] - wilson(round(mr[e]*RUNS), RUNS)[1]) * EW[e] for e in EW)
    band = 100 * halfw / 2 * WT["PS"]

    print(f"\n{b}")
    print(f"  PS+SRS(v1) = {PS + SRS1:6.1f}   <-- collinearity check, must be 100.0")
    print(f"  {'':14}{'v1':>9}{'v2':>9}   delta")
    for nm, a, c in (("PS", PS, PS), ("DS", DS1, DS2), ("SS", SS, SS), ("SRS", SRS1, SRS2), ("FI", FI1, FI2)):
        print(f"  {nm:<14}{a:9.1f}{c:9.1f}{c-a:+9.1f}")
    print(f"  {'CAAI':<14}{v1:9.1f}{v2:9.1f}{v2-v1:+9.1f}    (published {PUBLISHED[b]})")
    print(f"  {'tier':<14}{tier(v1):>9}{tier(v2):>9}    v2 capped by coverage 0.80 -> "
          f"{'STRONG' if tier(v2)=='DOMINANT' else tier(v2)}")
    print(f"  CAAI v2 with 95% presence band: {v2:.1f} [{v2-band:.1f} – {v2+band:.1f}]")
    rows.append((b, v1, v2, tier(v1), tier(v2)))

print("\n" + "=" * 96)
print(f"{'brand':<16}{'v1':>8}{'v2':>8}{'delta':>9}   {'v1 tier':<10}{'v2 tier':<10}  rank change")
r1 = sorted(rows, key=lambda r: -r[1]); r2 = sorted(rows, key=lambda r: -r[2])
for b, a, c, t1, t2 in rows:
    print(f"{b:<16}{a:8.1f}{c:8.1f}{c-a:+9.1f}   {t1:<10}{t2:<10}  #{r1.index(next(x for x in r1 if x[0]==b))+1}"
          f" -> #{r2.index(next(x for x in r2 if x[0]==b))+1}")
print("=" * 96)
