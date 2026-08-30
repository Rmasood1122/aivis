#!/usr/bin/env python3
"""kappa_sample.py — draw the labelling sample BEFORE any extractor touches it.

Stdlib only.

WHY THIS IS A SEPARATE TOOL
  Sampling after seeing which responses an extractor handles well is the failure
  the sealed protocol names first. This tool takes a seed, draws the sample,
  writes it, and prints its own SHA-256. Run it once. Seal the output. Only then
  label.

  The seed is published with the result so the draw is reproducible by a
  challenger.

USAGE
  python3 kappa_sample.py --seed 20260830 --out kappa_sample_v1.json \
      --corpus data/pr_agency_run4.jsonl:config/prompts_pr_agency_v1.json \
      --corpus data/mattress_run2.jsonl:config/prompts_mattress_premium_v1.json
"""
import sys, json, random, hashlib, argparse, pathlib, collections

TOOL_VERSION = "kappa_sample v0.1.0"


def load(ev_path, bank_path):
    bank = json.loads(pathlib.Path(bank_path).read_text(encoding="utf-8"))
    t2f = {p["text"]: f for f, ps in bank["families"].items() for p in ps}
    out = []
    for i, line in enumerate(pathlib.Path(ev_path).read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        r = json.loads(line)
        if not r.get("response_text"):
            continue
        try:
            q = r["request_payload"]["messages"][0]["content"]
        except (KeyError, IndexError, TypeError):
            continue
        out.append({
            "corpus": pathlib.Path(ev_path).name,
            "line": i,
            "prompt_id": r.get("prompt_id"),
            "run": r.get("run"),
            "family": t2f.get(q, "UNMAPPED"),
            "sha256": r.get("sha256"),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--corpus", action="append", required=True,
                    help="evidence.jsonl:bank.json — repeatable")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    outp = pathlib.Path(a.out)
    if outp.exists():
        print("REFUSED: %s exists. A sample is drawn once." % outp); return 2

    units = []
    for spec in a.corpus:
        ev, bank = spec.split(":", 1)
        units += load(ev, bank)

    strata = collections.defaultdict(list)
    for u in units:
        strata[(u["corpus"], u["family"])].append(u)
    keys = sorted(strata)

    rng = random.Random(a.seed)
    for k in keys:
        strata[k].sort(key=lambda u: (u["line"],))
        rng.shuffle(strata[k])

    # proportional allocation, largest-remainder, then round-robin top-up
    total = sum(len(strata[k]) for k in keys)
    quota = {}
    rema = []
    assigned = 0
    for k in keys:
        exact = a.n * len(strata[k]) / total
        q = min(int(exact), len(strata[k]))
        quota[k] = q
        assigned += q
        rema.append((exact - int(exact), k))
    rema.sort(reverse=True)
    i = 0
    while assigned < a.n and i < len(rema) * 50:
        k = rema[i % len(rema)][1]
        if quota[k] < len(strata[k]):
            quota[k] += 1
            assigned += 1
        i += 1

    sample = []
    for k in keys:
        sample += strata[k][:quota[k]]
    rng.shuffle(sample)                      # presentation order, also seeded
    for idx, u in enumerate(sample):
        u["case_id"] = "K%03d" % idx

    doc = {
        "tool": TOOL_VERSION,
        "seed": a.seed,
        "n_requested": a.n,
        "n_drawn": len(sample),
        "population_total": total,
        "strata": {"%s|%s" % k: {"available": len(strata[k]), "drawn": quota[k]} for k in keys},
        "rule": "proportional allocation by stratum with largest-remainder top-up; "
                "shuffle and allocation both driven by the published seed; "
                "drawn BEFORE any extractor was run on these responses",
        "cases": sample,
    }
    outp.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")

    print(TOOL_VERSION)
    print("POPULATION  %d clean responses across %d strata" % (total, len(keys)))
    for k in keys:
        print("  %-34s available %3d  drawn %3d" % ("%s | %s" % k, len(strata[k]), quota[k]))
    print("DRAWN       %d" % len(sample))
    print("SEED        %d  (publish this)" % a.seed)
    print("OUT         %s" % outp)
    print("SHA-256     %s" % hashlib.sha256(outp.read_bytes()).hexdigest())
    print("\nSeal this file now. Label only after it is sealed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
