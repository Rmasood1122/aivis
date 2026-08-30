#!/usr/bin/env python3
"""04 · Score the measurement rows. Assigns ranked / middle / non-ranked PURELY from data.
Also computes the order-bias delta, which gates the whole category."""
import json, sys, csv, re, pathlib, collections, math

ROOT = pathlib.Path(__file__).resolve().parent.parent
runs_path = pathlib.Path(sys.argv[1])
sample_path = ROOT / "data/sample_validated.csv"

with open(sample_path) as f:
    brands = list(csv.DictReader(f))
names = {b["practice_name"]: b["brand_id"] for b in brands}

rows = [json.loads(l) for l in runs_path.open() if l.strip()]
rows = [r for r in rows if r.get("response_text")]

INTENT = {"comparison", "buyer_intent"}
bank = json.loads((ROOT / "config/prompts_cosmetic_tristate_v1.json").read_text())
fam_of = {p["id"]: fam for fam, ps in bank["families"].items() for p in ps}


def mentioned(text, name):
    return re.search(re.escape(name), text, re.I) is not None


def top3(text, name):
    """Position by first appearance among sample brands present in the response."""
    hits = [(m.start(), n) for n in names if (m := re.search(re.escape(n), text, re.I))]
    hits.sort()
    ordered = [n for _, n in hits]
    return name in ordered[:3]


stat = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
for r in rows:
    intent = fam_of.get(r["prompt_id"]) in INTENT
    for name in names:
        s = stat[name][r["order"]]
        if intent:
            s[1] += 1
            if top3(r["response_text"], name):
                s[0] += 1

# SEALED RULE: groups are defined by PERCENTILE of the observed top-3 rate, not by an
# absolute rate. An absolute bar cannot be pre-registered without knowing the distribution,
# and setting one after seeing the data breaks the seal. Top tertile = ranked, bottom
# tertile = non-ranked, middle discarded. Sealed 2026-08-29, before any live run.
rates_all = []
for name in names:
    h, n_ = stat[name]["open"]
    rates_all.append(h / n_ if n_ else 0.0)
rs = sorted(rates_all)
HI = rs[int(len(rs) * 2 / 3)] if rs else 1.0
LO = rs[int(len(rs) / 3)] if rs else 0.0

out = []
for name, bid in names.items():
    f_hit, f_n = stat[name]["open"]
    v_hit, v_n = (0, 0)
    tot_hit, tot_n = f_hit + v_hit, f_n + v_n
    rate = tot_hit / tot_n if tot_n else 0.0
    f_rate = f_hit / f_n if f_n else 0.0
    v_rate = v_hit / v_n if v_n else 0.0
    delta = abs(f_rate - v_rate)
    if rate >= HI and rate > 0:
        grp = "ranked"
    elif rate <= LO:
        grp = "non_ranked"
    else:
        grp = "middle_EXCLUDED"
    out.append(dict(brand_id=bid, practice_name=name, top3_rate=round(rate, 4),
                    n=tot_n, forward_rate=round(f_rate, 4), reverse_rate=round(v_rate, 4),
                    order_delta_pp=round(delta * 100, 2), group=grp))

out.sort(key=lambda d: -d["top3_rate"])
counts = collections.Counter(d["group"] for d in out)
max_delta = max((d["order_delta_pp"] for d in out), default=0.0)

# Pairs surviving: both members must land in opposite groups.
pair_of = {b["brand_id"]: b["pair_id"] for b in brands}
grp_of = {d["brand_id"]: d["group"] for d in out}
pairs = collections.defaultdict(list)
for bid, pid in pair_of.items():
    pairs[pid].append(grp_of.get(bid))
usable = sum(1 for g in pairs.values() if sorted(g) == ["non_ranked", "ranked"])

report = dict(
    source=str(runs_path),
    tertile_cut_low=round(LO, 4), tertile_cut_high=round(HI, 4), rows_scored=len(rows),
    ranked=counts["ranked"], non_ranked=counts["non_ranked"],
    middle_excluded=counts["middle_EXCLUDED"],
    usable_discordant_pairs=usable,
    max_order_delta_pp=max_delta,
    brands=out,
)

(ROOT / "out").mkdir(exist_ok=True)
(ROOT / "out/scores.json").write_text(json.dumps(report, indent=2))

print(json.dumps({k: v for k, v in report.items() if k != "brands"}, indent=2))
print()
if usable < 25:
    print(f"ABSTAIN: {usable} discordant pairs, minimum 25. Category abstains.")
print(f"Order-bias max delta: {max_delta}pp — compare against any separation you later claim.")
print("If the delta exceeds the separation, the finding is withdrawn for this category.")
print("\nFull per-brand table: out/scores.json")
