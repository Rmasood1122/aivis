#!/usr/bin/env python3
"""Bridge: bank-pipeline JSONL (response_text) -> core parser (parse_tool_list).
Root cause of months of 90/90-empty extraction: field-name drift between the
core pipeline (raw_text/raw_response_text) and the bank pipeline (response_text).
First real run 2026-09-05: 415/648 rows parsed into brand leaderboards."""
import json, sys, glob, collections
sys.path.insert(0, "src")
from aivis.parser import parse_tool_list

paths = sorted(set(glob.glob("study2/data/pr_agency_run*.jsonl") + glob.glob("data/audits/pr_agency*_v1.jsonl")))
paths = [p for p in paths if not p.endswith("_parsed.jsonl")]
for path in paths:
    try:
        rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    except Exception as ex:
        print(f"{path}: SKIP ({ex})"); continue
    if not rows:
        print(f"{path}: SKIP (empty file)"); continue
    field = "response_text" if "response_text" in rows[0] else "raw_response_text"
    ok, mentions = 0, collections.Counter()
    out = path.rsplit(".jsonl", 1)[0] + "_parsed.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            entries, meta = parse_tool_list(r.get(field) or "")
            if meta.get("parse_success") and entries:
                ok += 1
                for e in entries: mentions[e.name_norm] += 1
            f.write(json.dumps({"prompt_id": r.get("prompt_id"), "engine": r.get("engine"),
                                "n_entries": len(entries), "meta": meta,
                                "entries": [getattr(e, "__dict__", None) or str(e) for e in entries]},
                               default=str) + "\n")
    print(f"{path}: {ok}/{len(rows)} rows parsed -> {out}")
    print("   top brands:", mentions.most_common(8))
