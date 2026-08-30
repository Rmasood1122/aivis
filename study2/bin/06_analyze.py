#!/usr/bin/env python3
"""06 · Analysis. Prevalence difference per feature between ranked and matched non-ranked,
with intervals, Bonferroni correction over 8 primaries, a size-proxy audit, and
inter-coder agreement from the double-coded subset. Abstains rather than softens."""
import json, csv, math, pathlib, collections, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FEATURES = [f"F{i}" for i in range(1, 9)]
ALPHA = 0.05
Z_UNCORR = 1.959964
Z_CORR = 2.734  # two-sided 0.05/8

key = json.loads((ROOT / "data/BLIND_KEY_DO_NOT_SHARE.json").read_text())
cmap = {b["code_id"]: b["brand_id"] for b in json.loads((ROOT / "data/code_id_map_DO_NOT_SHARE.json").read_text())}
with open(ROOT / "data/sample_validated.csv") as f:
    sample = {r["brand_id"]: r for r in csv.DictReader(f)}

coded, double = {}, collections.defaultdict(dict)
for p in sorted((ROOT / "out/coding_sheets").glob("coder_*.csv")):
    for r in csv.DictReader(p.open()):
        if not r.get("code_id"):
            continue
        vals = {k: r.get(k, "").strip() for k in FEATURES}
        if not any(vals.values()):
            continue
        if "DOUBLE" in p.name:
            double[r["code_id"]] = vals
        else:
            coded[r["code_id"]] = vals

def yes(v): return str(v).strip().lower() in ("1", "y", "yes", "true")

# ---- inter-coder agreement on the double-coded subset ----
agree = tot = 0
for cid, v2 in double.items():
    v1 = coded.get(cid)
    if not v1 or not isinstance(v2, dict):
        continue
    for f in FEATURES:
        if v1.get(f, "") != "" and v2.get(f, "") != "":
            tot += 1
            agree += (yes(v1[f]) == yes(v2[f]))
pct_agree = round(100 * agree / tot, 1) if tot else None

def wilson_diff(x1, n1, x2, n2, z):
    if not n1 or not n2:
        return None
    p1, p2 = x1 / n1, x2 / n2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    d = p1 - p2
    return d, d - z * se, d + z * se

results, buckets = [], collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
for cid, vals in coded.items():
    bid = cmap.get(cid)
    grp = key.get(bid)
    if grp not in ("ranked", "non_ranked"):
        continue
    band = sample.get(bid, {}).get("size_band", "?")
    for f in FEATURES:
        if vals.get(f) == "":
            continue
        buckets[f][grp][1] += 1
        buckets[f][grp][0] += yes(vals[f])
        buckets[(f, band)][grp][1] += 1
        buckets[(f, band)][grp][0] += yes(vals[f])

for f in FEATURES:
    r = buckets[f]["ranked"]; n = buckets[f]["non_ranked"]
    unc = wilson_diff(r[0], r[1], n[0], n[1], Z_UNCORR)
    cor = wilson_diff(r[0], r[1], n[0], n[1], Z_CORR)
    if not cor:
        results.append(dict(feature=f, verdict="ABSTAIN — no coded data")); continue
    d, lo, hi = cor
    _, ulo, uhi = unc
    bands = {}
    for b in set(s["size_band"] for s in sample.values()):
        rb, nb = buckets[(f, b)]["ranked"], buckets[(f, b)]["non_ranked"]
        w = wilson_diff(rb[0], rb[1], nb[0], nb[1], Z_UNCORR)
        if w:
            bands[b] = dict(diff_pp=round(w[0] * 100, 1), separates=(w[1] > 0 or w[2] < 0))
    sep_bands = [b for b, v in bands.items() if v["separates"]]
    verdict = ("SEPARATES" if (lo > 0 or hi < 0) else "DOES NOT SEPARATE")
    size_proxy = verdict == "SEPARATES" and len(bands) > 1 and len(sep_bands) == 1
    results.append(dict(
        feature=f,
        ranked=f"{r[0]}/{r[1]}", non_ranked=f"{n[0]}/{n[1]}",
        diff_pp=round(d * 100, 1),
        ci95_uncorrected_pp=[round(ulo * 100, 1), round(uhi * 100, 1)],
        ci95_bonferroni_pp=[round(lo * 100, 1), round(hi * 100, 1)],
        verdict=verdict,
        by_size_band=bands,
        size_proxy_flag=size_proxy,
        note="separates in only one size band — treat as a size proxy" if size_proxy else "",
    ))

separating = [r for r in results if r.get("verdict") == "SEPARATES" and not r.get("size_proxy_flag")]
scores = json.loads((ROOT / "out/scores.json").read_text())
max_delta = scores.get("max_order_delta_pp", 0)

report = dict(
    coded_brands=len(coded),
    double_coded_comparisons=tot,
    inter_coder_percent_agreement=pct_agree,
    features_tested=len(FEATURES),
    correction="Bonferroni over 8 primaries",
    order_bias_max_delta_pp=max_delta,
    separating_features=len(separating),
    H1_SUPPORTED=bool(separating),
    results=results,
)
(ROOT / "out/analysis.json").write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
print()
for r in results:
    print(f"  {r['feature']}: {r.get('verdict')}  diff {r.get('diff_pp')}pp  "
          f"CI(corr) {r.get('ci95_bonferroni_pp')} {r.get('note','')}")
print()
if not separating:
    print("H1 FALSIFIED. No feature separates ranked from matched non-ranked brands.")
    print("THE ACTION LIST DOES NOT EXIST. Publish the null. Do not shorten the list.")
else:
    for r in separating:
        if abs(r["diff_pp"]) < max_delta:
            print(f"WITHDRAWN {r['feature']}: separation {r['diff_pp']}pp is smaller than "
                  f"the order-bias delta {max_delta}pp.")
print("\nFull table: out/analysis.json")
