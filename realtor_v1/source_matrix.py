#!/usr/bin/env python3
"""source_matrix.py - which sources do engines cite when they name each agent?

    python realtor_v1/source_matrix.py realtor_v1/verify_sheet_v1_filled.csv realtor_v1/runs/multi_*_realtor_v1_20260923.jsonl

Output: realtor_v1/results_v1_final/source_matrix.csv  (rows = verified agents, cols = domains)
        realtor_v1/results_v1_final/source_matrix_summary.txt
Two counts per agent x domain:
  co   = responses that mention the agent AND cite the domain (co-occurrence)
  attr = citations whose URL or title contains the agent's name (direct attribution: the engine
         is pointing at THAT agent's page on that site) - the stronger signal.
"""
import csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse, unquote

if len(sys.argv) < 3:
    sys.exit(__doc__)
sheet, files = sys.argv[1], sys.argv[2:]
agents = [r["name"] for r in csv.DictReader(open(sheet, encoding="utf-8")) if r["verified"] == "yes"]
pats = {a: re.compile(re.escape(a), re.I) for a in agents}
key = {a: [w.lower() for w in a.split() if len(w) > 2] for a in agents}   # for URL/title matching

def host_of(c):
    u = c.get("url", "") if isinstance(c, dict) else str(c)
    t = (c.get("title") or "") if isinstance(c, dict) else ""
    h = urlparse(u).netloc.lower().removeprefix("www.")
    if "vertexaisearch" in h and t and " " not in t and "." in t: h = t
    return h, unquote(u).lower(), t.lower()

co = defaultdict(Counter); attr = defaultdict(Counter); mentions = Counter()
dom_total = Counter(); n = 0
for f in files:
    for l in open(f, encoding="utf-8"):
        if not l.strip(): continue
        r = json.loads(l); txt = r.get("response_text") or ""
        if not txt: continue
        n += 1
        cites = [host_of(c) for c in (r.get("citations") or [])]
        for h, _, _ in set((h, "", "") for h, _, _ in cites): dom_total[h] += 1
        for a, p in pats.items():
            if not p.search(txt): continue
            mentions[a] += 1
            seen = set()
            for h, u, t in cites:
                if not h: continue
                if h not in seen: co[a][h] += 1; seen.add(h)
                if all(w in u or w in t for w in key[a]): attr[a][h] += 1

doms = [d for d, _ in dom_total.most_common(40)]
out = Path("realtor_v1/results_v1_final"); out.mkdir(parents=True, exist_ok=True)
with open(out / "source_matrix.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["agent", "mentions"] + [f"{d} co" for d in doms] + [f"{d} attr" for d in doms])
    for a in sorted(agents, key=lambda x: -mentions[x]):
        w.writerow([a, mentions[a]] + [co[a][d] for d in doms] + [attr[a][d] for d in doms])

lines = [f"responses={n}  verified agents={len(agents)}", "",
         "Domains by number of responses citing them (all responses):"]
lines += [f"  {k:4d}  {d}" for d, k in dom_total.most_common(25)]
lines += ["", "Direct attributions (citation URL/title contains the agent's name), summed over agents:"]
tot_attr = Counter()
for a in agents: tot_attr.update(attr[a])
lines += [f"  {k:4d}  {d}" for d, k in tot_attr.most_common(20)]
lines += ["", "Agents with ZERO direct attributions (named without any page of theirs being cited):"]
lines += [f"  {a} ({mentions[a]} mentions)" for a in agents if mentions[a] and not attr[a]]
lines += ["", "Per agent, top attributed sources:"]
for a in sorted(agents, key=lambda x: -mentions[x]):
    top = ", ".join(f"{d}:{k}" for d, k in attr[a].most_common(5))
    lines.append(f"  {a:22s} {mentions[a]:3d}  {top}")
(out / "source_matrix_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
