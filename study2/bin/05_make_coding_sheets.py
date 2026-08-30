#!/usr/bin/env python3
"""05 · Generate BLINDED coding sheets. Group labels are stripped and the order shuffled
with a published seed. 20% are double-coded by a second coder for inter-coder agreement.

This is the cheapest quality control in the study and it costs one shuffle. A coder who
knows which brands are ranked will find the features that explain it."""
import json, csv, random, pathlib, sys, hashlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 20260829
N_CODERS = int(sys.argv[2]) if len(sys.argv) > 2 else 4

scores = json.loads((ROOT / "out/scores.json").read_text())
eligible = [b for b in scores["brands"] if b["group"] in ("ranked", "non_ranked")]

# THE BLIND: group is dropped here and never written to a coding sheet.
blind = [{"code_id": f"X{i:03d}", "brand_id": b["brand_id"],
          "practice_name": b["practice_name"]} for i, b in enumerate(eligible, 1)]

rng = random.Random(SEED)
rng.shuffle(blind)

# key file — the ONLY link back to group. Coders never see this.
keydir = ROOT / "data"
keydir.mkdir(exist_ok=True)
key = {b["brand_id"]: b["group"] for b in eligible}
(keydir / "BLIND_KEY_DO_NOT_SHARE.json").write_text(json.dumps(key, indent=2))

FEATURES = [f"F{i}" for i in range(1, 9)]  # 8 primaries, defined in the sealed codebook
sheetdir = ROOT / "out/coding_sheets"
sheetdir.mkdir(parents=True, exist_ok=True)

chunks = [blind[i::N_CODERS] for i in range(N_CODERS)]
double = rng.sample(blind, max(1, round(0.20 * len(blind))))

for i, chunk in enumerate(chunks, 1):
    p = sheetdir / f"coder_{i:02d}.csv"
    with p.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["code_id", "practice_name", "website_you_look_up"] + FEATURES + ["coder_notes"])
        for b in chunk:
            w.writerow([b["code_id"], b["practice_name"], ""] + [""] * len(FEATURES) + [""])

with (sheetdir / "coder_99_DOUBLE.csv").open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["code_id", "practice_name", "website_you_look_up"] + FEATURES + ["coder_notes"])
    for b in double:
        w.writerow([b["code_id"], b["practice_name"], ""] + [""] * len(FEATURES) + [""])

manifest = dict(seed=SEED, coders=N_CODERS, blinded_n=len(blind),
                double_coded_n=len(double),
                double_coded_pct=round(100 * len(double) / len(blind), 1),
                map_sha256=hashlib.sha256(json.dumps(blind, sort_keys=True).encode()).hexdigest())
(ROOT / "out/coding_manifest.json").write_text(json.dumps(manifest, indent=2))
(keydir / "code_id_map_DO_NOT_SHARE.json").write_text(json.dumps(blind, indent=2))

print(json.dumps(manifest, indent=2))
print(f"\nSheets in {sheetdir}. Hand these to coders.")
print("NEVER hand out data/BLIND_KEY_DO_NOT_SHARE.json or the code_id map.")
