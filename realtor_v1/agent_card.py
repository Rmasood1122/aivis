#!/usr/bin/env python3
"""agent_card.py - evidence card for ONE agent name, straight from the run files.

    python realtor_v1/agent_card.py "Maureen Folan" realtor_v1/runs/multi_*_realtor_v1_20260923.jsonl

Prints: mentions per engine, per question (with rep counts), cited source domains on the
responses that mention her, and 3 verbatim excerpts. Every number is recomputed from the JSONL,
so what you tell the agent is what the file says.
"""
import json, re, sys
from collections import Counter, defaultdict
from urllib.parse import urlparse

if len(sys.argv) < 3:
    sys.exit(__doc__)
name = sys.argv[1]
pat = re.compile(re.escape(name), re.I)

PROMPT_AREA = {}
try:
    for l in open("realtor_v1/queens_li_prompts_v1.jsonl", encoding="utf-8"):
        if l.strip():
            r = json.loads(l); PROMPT_AREA[r["prompt_id"]] = (r["area"], r["intent"], r["text"])
except FileNotFoundError:
    pass

per_engine = Counter(); n_engine = Counter()
per_prompt = defaultdict(set); per_prompt_engine = defaultdict(set)
domains = Counter(); excerpts = []; total = 0
for path in sys.argv[2:]:
    for l in open(path, encoding="utf-8"):
        if not l.strip(): continue
        r = json.loads(l); txt = r.get("response_text") or ""
        if not txt: continue
        e = r["engine"]; n_engine[e] += 1; total += 1
        if not pat.search(txt): continue
        per_engine[e] += 1
        per_prompt[r["prompt_id"]].add((e, r.get("rep")))
        per_prompt_engine[(r["prompt_id"], e)].add(r.get("rep"))
        for c in r.get("citations") or []:
            u = c.get("url", "") if isinstance(c, dict) else str(c)
            t = (c.get("title") or "") if isinstance(c, dict) else ""
            host = urlparse(u).netloc.lower().removeprefix("www.")
            if "vertexaisearch" in host and t and " " not in t and "." in t: host = t
            if host: domains[host] += 1
        if len(excerpts) < 3:
            m = pat.search(txt); excerpts.append((e, r["prompt_id"], txt[max(0, m.start()-120): m.end()+200].replace("\n", " ")))

hits = sum(per_engine.values())
print(f"=== {name} ===  run files: {len(sys.argv)-2}, responses scanned: {total}")
print(f"Responses mentioning the name: {hits} of {total} ({hits/total:.0%})")
print("\nPer engine (mentions / responses):")
for e in sorted(n_engine): print(f"  {e:11s} {per_engine[e]:3d} / {n_engine[e]}")
print(f"Engines naming this agent: {sum(1 for e in per_engine if per_engine[e])} of {len(n_engine)}")
print("\nPer question (mentions / 5 reps, by engine):")
for pid in sorted(per_prompt):
    area, intent, text = PROMPT_AREA.get(pid, ("?", "?", ""))
    cells = "  ".join(f"{e}:{len(per_prompt_engine[(pid, e)])}/5" for e in sorted(n_engine) if per_prompt_engine[(pid, e)])
    print(f"  {pid} {area:17s} {intent:16s} {cells}")
    if text: print(f"      \"{text}\"")
print("\nCited source domains on responses that mention the name:")
for d, k in domains.most_common(12): print(f"  {k:3d}  {d}")
print("\nExcerpts:")
for e, pid, x in excerpts: print(f"  [{e} {pid}] ...{x}...")
