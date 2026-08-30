#!/usr/bin/env python3
"""02 · Validate the hand-filled sampling worksheet.
Enforces exact matching on metro, size_band, founded_decade. Drops what does not match.
Refuses to invent, complete, or relax anything."""
import csv, sys, json, collections, pathlib

SRC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "config/sample_worksheet.csv")
OUT = pathlib.Path("data/sample_validated.csv")
REPORT = pathlib.Path("out/sample_report.json")
MATCH_ON = ("metro", "size_band", "founded_decade")
REQUIRED = ("brand_id", "practice_name", "website", "metro", "state",
            "size_band", "founded_decade", "size_source", "founded_source", "pair_id")

rows = []
with SRC.open() as f:
    for r in csv.DictReader(l for l in f if not l.lstrip().startswith("#") and l.strip()):
        rows.append({k: (v or "").strip() for k, v in r.items() if k})

errors, dropped, kept = [], [], []

for r in rows:
    missing = [k for k in REQUIRED if not r.get(k)]
    if missing:
        errors.append(f"{r.get('brand_id','?')}: missing {','.join(missing)}")
    for src in ("size_source", "founded_source"):
        if r.get(src, "").lower() in ("estimate", "est", "guess", "unknown", "n/a"):
            errors.append(f"{r.get('brand_id','?')}: {src} is not a source")

ids = [r["brand_id"] for r in rows]
for bid, n in collections.Counter(ids).items():
    if n > 1:
        errors.append(f"duplicate brand_id {bid} appears {n}x")

pairs = collections.defaultdict(list)
for r in rows:
    pairs[r.get("pair_id", "")].append(r)

for pid, members in sorted(pairs.items()):
    if len(members) != 2:
        dropped.append({"pair_id": pid, "reason": f"has {len(members)} rows, needs exactly 2"})
        continue
    a, b = members
    diffs = [v for v in MATCH_ON if a.get(v) != b.get(v)]
    if diffs:
        dropped.append({"pair_id": pid, "reason": "unmatched on " + ",".join(diffs),
                        "values": {v: [a.get(v), b.get(v)] for v in diffs}})
        continue
    kept.extend(members)

report = {
    "source": str(SRC),
    "rows_read": len(rows),
    "pairs_seen": len(pairs),
    "pairs_kept": len(kept) // 2,
    "pairs_dropped": len(dropped),
    "dropped_detail": dropped,
    "errors": errors,
    "minimum_pairs_required": 25,
    "meets_minimum": (len(kept) // 2) >= 25,
}

pathlib.Path("out").mkdir(exist_ok=True)
pathlib.Path("data").mkdir(exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2))

if errors:
    print("ERRORS — fix the worksheet, nothing was written:")
    for e in errors:
        print("  " + e)
    sys.exit(1)

with OUT.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=[k for k in kept[0].keys()] if kept else REQUIRED)
    w.writeheader()
    w.writerows(kept)

print(json.dumps(report, indent=2))
if not report["meets_minimum"]:
    print(f"\nABSTAIN: {report['pairs_kept']} matched pairs, minimum is 25.")
    print("The category abstains. Add pairs or drop the category. Do not lower the bar.")
    sys.exit(2)
print(f"\nOK: {report['pairs_kept']} matched pairs written to {OUT}")
