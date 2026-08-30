#!/usr/bin/env python3
"""kappa_compute.py — agreement between each extractor and the human labels.

Stdlib only.

WHAT IS COMPUTED, AND UNDER WHICH NAME
  Cohen's kappa here is agreement between TWO RATERS on the same items: the
  extractor and the human labeller. That is a legitimate two-rater coefficient
  and it is what "extractor accuracy (kappa)" means.

  It is NOT inter-human agreement. Krippendorff's alpha between two human
  labellers is a different number, reported separately, and printed as
  NOT YET COLLECTED until a second labeller's file is supplied.

THE UNIT
  One decision per (response x candidate name). The candidate universe for a
  response is the union of every name proposed by any extractor plus every name
  the human wrote. Both raters are then scored on that same universe, which is
  what makes the two columns comparable.

  Human SKIP cases are excluded and their count is printed.

EXTRACTORS COMPARED (both, separately)
  E1 ROSTER  fixed-list regex, word-bounded, case-insensitive
  E2 BOLD    markdown emphasis spans, the model's own formatting

USAGE
  python3 kappa_compute.py --sample kappa_sample_v1.json \
      --labels kappa_labels_rehan.jsonl \
      [--labels2 kappa_labels_other.jsonl] \
      --corpus data/pr_agency_run4.jsonl --corpus data/mattress_run2.jsonl \
      --roster roster.txt --out kappa_result_v1.md
"""
import sys, json, re, math, random, argparse, pathlib, collections

TOOL_VERSION = "kappa_compute v0.1.0"
BOLD = re.compile(r'\*\*([^*\n]{3,45}?)\*\*')


def norm(s):
    s = s.strip().rstrip(":").rstrip(".")
    s = re.sub(r'\s+', ' ', s)
    return s.lower()


def e1_roster(text, roster):
    return {norm(n) for n in roster
            if re.search(r'\b' + re.escape(n) + r'\b', text, re.I)}


def e2_bold(text):
    return {norm(m) for m in BOLD.findall(text) if norm(m)}


def cohen_kappa(a, b):
    """a, b: equal-length 0/1 sequences."""
    n = len(a)
    if n == 0:
        return None
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa1, pb1 = sum(a) / n, sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    if abs(1 - pe) < 1e-12:
        return None
    return (po - pe) / (1 - pe)


def prf(pred, gold):
    tp = sum(1 for p, g in zip(pred, gold) if p and g)
    fp = sum(1 for p, g in zip(pred, gold) if p and not g)
    fn = sum(1 for p, g in zip(pred, gold) if not p and g)
    tn = sum(1 for p, g in zip(pred, gold) if not p and not g)
    prec = tp / (tp + fp) if tp + fp else None
    rec = tp / (tp + fn) if tp + fn else None
    f1 = (2 * prec * rec / (prec + rec)) if prec and rec else None
    return tp, fp, fn, tn, prec, rec, f1


def boot_ci(pairs, stat, B=2000, seed=7):
    """Cluster bootstrap over CASES, not over decisions."""
    rng = random.Random(seed)
    cases = sorted({c for c, _, _ in pairs})
    by = collections.defaultdict(list)
    for c, p, g in pairs:
        by[c].append((p, g))
    vals = []
    for _ in range(B):
        draw = [rng.choice(cases) for _ in cases]
        a, b = [], []
        for c in draw:
            for p, g in by[c]:
                a.append(p); b.append(g)
        v = stat(a, b)
        if v is not None:
            vals.append(v)
    if len(vals) < 50:
        return None, None
    vals.sort()
    return vals[int(.025 * len(vals))], vals[int(.975 * len(vals))]


def krippendorff_binary(units):
    """units: list of (v1, v2) from two coders. Nominal alpha, 2 coders."""
    n = len(units)
    if n == 0:
        return None
    do = sum(1 for x, y in units if x != y) / n
    vals = [v for u in units for v in u]
    p1 = sum(vals) / len(vals)
    de = 2 * p1 * (1 - p1) * (len(vals) / (len(vals) - 1)) if len(vals) > 1 else 0
    if de == 0:
        return None
    return 1 - do / de


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--labels2", default=None)
    ap.add_argument("--corpus", action="append", required=True)
    ap.add_argument("--roster", required=True, help="one name per line")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    outp = pathlib.Path(a.out)
    if outp.exists():
        print("REFUSED: %s exists." % outp); return 2

    sample = json.loads(pathlib.Path(a.sample).read_text(encoding="utf-8"))
    roster = [l.strip() for l in pathlib.Path(a.roster).read_text(encoding="utf-8").splitlines()
              if l.strip() and not l.startswith("#")]
    corpora = {}
    for p in a.corpus:
        nm = pathlib.Path(p).name
        for i, line in enumerate(pathlib.Path(p).read_text(encoding="utf-8").splitlines()):
            if line.strip():
                corpora[(nm, i)] = json.loads(line)

    labels = {}
    for line in pathlib.Path(a.labels).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            labels[r["case_id"]] = r

    pairs = {"E1_ROSTER": [], "E2_BOLD": []}
    skipped = unlabelled = 0
    fam_of = {}
    for c in sample["cases"]:
        lab = labels.get(c["case_id"])
        if lab is None:
            unlabelled += 1
            continue
        if lab.get("skipped"):
            skipped += 1
            continue
        row = corpora.get((c["corpus"], c["line"]))
        if row is None:
            unlabelled += 1
            continue
        t = row["response_text"]
        gold = {norm(x) for x in lab["names"]}
        p1, p2 = e1_roster(t, roster), e2_bold(t)
        universe = sorted(gold | p1 | p2)
        fam_of[c["case_id"]] = c["family"]
        for u in universe:
            pairs["E1_ROSTER"].append((c["case_id"], 1 if u in p1 else 0, 1 if u in gold else 0))
            pairs["E2_BOLD"].append((c["case_id"], 1 if u in p2 else 0, 1 if u in gold else 0))

    L = []
    w = L.append
    w("# EXTRACTOR AGREEMENT — kappa against a human gold standard")
    w("")
    w("**%s** · sample seed `%s` · n requested %d, drawn %d"
      % (TOOL_VERSION, sample["seed"], sample["n_requested"], sample["n_drawn"]))
    w("")
    w("Cases labelled and used: **%d**. Human abstentions (SKIP): **%d**. "
      "Unlabelled or unresolvable: **%d**." % (len(fam_of), skipped, unlabelled))
    w("")
    w("## Unit and universe")
    w("")
    w("One decision per (response x candidate name). For each response the candidate")
    w("universe is the union of every name proposed by either extractor and every name")
    w("the human wrote. Both raters are scored on that same universe.")
    w("")
    w("Cohen's kappa below is agreement between **two raters** — the extractor and the")
    w("human labeller — on identical items. It is not inter-human agreement.")
    w("")
    w("## Results")
    w("")
    w("| extractor | decisions | kappa | 95% CI | precision | recall | F1 |")
    w("|---|---|---|---|---|---|---|")
    verdicts = {}
    for name, pr in pairs.items():
        if not pr:
            w("| %s | 0 | — | — | — | — | — |" % name)
            continue
        pred = [p for _, p, _ in pr]
        gold = [g for _, _, g in pr]
        k = cohen_kappa(pred, gold)
        lo, hi = boot_ci(pr, cohen_kappa)
        tp, fp, fn, tn, prec, rec, f1 = prf(pred, gold)
        verdicts[name] = k
        fmt = lambda v: "—" if v is None else "%.3f" % v
        w("| %s | %d | %s | %s–%s | %s | %s | %s |" % (
            name, len(pr), fmt(k), fmt(lo), fmt(hi), fmt(prec), fmt(rec), fmt(f1)))
    w("")
    w("Confusion counts (extractor as prediction, human as gold):")
    w("")
    w("| extractor | TP | FP | FN | TN |")
    w("|---|---|---|---|---|")
    for name, pr in pairs.items():
        if not pr:
            continue
        tp, fp, fn, tn, *_ = prf([p for _, p, _ in pr], [g for _, _, g in pr])
        w("| %s | %d | %d | %d | %d |" % (name, tp, fp, fn, tn))
    w("")
    w("Intervals are a **cluster bootstrap over cases**, not over decisions. Decisions")
    w("within one response are not independent and treating them as such would give an")
    w("interval narrower than the truth.")
    w("")

    w("## Inter-human agreement")
    w("")
    if a.labels2:
        l2 = {}
        for line in pathlib.Path(a.labels2).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                l2[r["case_id"]] = r
        shared = [c for c in labels if c in l2
                  and not labels[c].get("skipped") and not l2[c].get("skipped")]
        units = []
        for c in shared:
            row = corpora.get((labels[c]["corpus"], labels[c]["line"]))
            if row is None:
                continue
            g1 = {norm(x) for x in labels[c]["names"]}
            g2 = {norm(x) for x in l2[c]["names"]}
            for u in sorted(g1 | g2):
                units.append((1 if u in g1 else 0, 1 if u in g2 else 0))
        al = krippendorff_binary(units)
        w("Second labeller: `%s`. Shared cases: **%d**. Decisions: **%d**."
          % (pathlib.Path(a.labels2).name, len(shared), len(units)))
        w("")
        w("Krippendorff's alpha (nominal, 2 coders): **%s**"
          % ("—" if al is None else "%.3f" % al))
    else:
        w("**NOT YET COLLECTED.** No second labeller file was supplied, so no")
        w("inter-human agreement figure exists. The kappa above is extractor-versus-one-")
        w("human and carries the limitation that the gold standard has not been checked")
        w("by anyone else. Supplying `--labels2` fills this section.")
    w("")

    w("## What these numbers do and do not support")
    w("")
    w("- Recall is measured against **free recall** by the human, not against an")
    w("  adjudicated candidate list, so names both extractors missed are counted as")
    w("  false negatives rather than being invisible.")
    w("- The labelled set is published in full alongside this result. A challenger who")
    w("  re-labels it and gets a different number is producing a finding, not a dispute.")
    w("- One human labeller produced the gold standard. Until a second one covers a")
    w("  subset, the gold standard itself carries no error bar.")
    w("- These figures describe the corpora sampled. They do not transfer to a different")
    w("  category, engine, or bank version without re-measurement.")
    w("")
    w("## Pre-registered thresholds")
    w("")
    w("Sealed before any labelling: below 0.60 nothing ships and the parser is the")
    w("product; 0.60 to 0.75 is provisional, reports may ship carrying the figure and")
    w("the label \"Directional, not Decision-grade\", and no public index launches;")
    w("0.75 and above is shippable.")
    w("")
    for name, k in verdicts.items():
        if k is None:
            band = "not computable"
        elif k < 0.60:
            band = "BELOW 0.60 — nothing ships on this extractor"
        elif k < 0.75:
            band = "PROVISIONAL — Directional, not Decision-grade"
        else:
            band = "AT OR ABOVE 0.75 — shippable"
        w("- **%s**: %s" % (name, band))
    w("")

    outp.write_text("\n".join(L), encoding="utf-8")
    print(TOOL_VERSION)
    print("cases used %d · skipped %d · unlabelled %d" % (len(fam_of), skipped, unlabelled))
    for name, k in verdicts.items():
        print("  %-10s kappa %s" % (name, "—" if k is None else "%.3f" % k))
    print("WROTE %s" % outp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
