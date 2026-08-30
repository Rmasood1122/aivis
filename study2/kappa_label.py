#!/usr/bin/env python3
"""kappa_label.py — blind labelling harness. Free recall, one case at a time.

Stdlib only. Interactive.

THE BLINDING, AND WHY IT IS THE WHOLE POINT
  This tool NEVER shows you what any extractor found. It shows the response text
  and asks you to list the organisations named in it. If you could see the
  extractor's answer you would be grading a suggestion, not producing a gold
  standard, and the resulting number would measure agreement with the thing it
  audits.

  It also asks for FREE RECALL rather than adjudicating a candidate list. That is
  slower, and it is the only way recall can be measured. If you only judged the
  extractor's proposals, every name it missed would be invisible and recall would
  be an upper bound rather than a measurement.

NO MODEL ASSISTANCE. Not for a hard case, not for a borderline one. A gold set
labelled with help from a language model measures agreement with a language
model. If a case is genuinely ambiguous, mark it SKIP and it is reported as an
abstention with its count.

USAGE
  python3 kappa_label.py --sample kappa_sample_v1.json --labeller rehan \
      --corpus data/pr_agency_run4.jsonl --corpus data/mattress_run2.jsonl

  Resumes automatically. Ctrl-C is safe; completed cases are already written.
"""
import sys, json, argparse, pathlib, datetime

TOOL_VERSION = "kappa_label v0.1.0"

RULES = """
LABELLING RULES — read once, apply identically to every case. Written 2026-08-30,
before the first label.

You are listing ORGANISATIONS PRESENTED AS PROVIDERS in the response: companies a
reader could hire or buy from, in the category the question is about.

COUNT IT:
  - a named agency, firm, or brand offered as an option, example, or recommendation
  - a named provider inside a warning ("avoid X") — presence is presence; tone is
    a separate question this sample does not ask
  - a parent and a subsidiary named separately count as two

DO NOT COUNT:
  - section headings, advice, criteria ("Track record", "Red Flags")
  - publications and outlets (Forbes, USA Today) unless offered as a provider
  - tools, platforms, and directories (HARO, Clutch, Muck Rack) — they are not
    providers in the category being asked about
  - the person asking, generic roles ("a publicist"), or unnamed firms
  - a provider named only inside the question text echoed back

WRITE NAMES AS THEY APPEAR, one per line. Do not normalise spelling, do not expand
abbreviations, do not merge variants. Normalisation is the extractor's job and
merging here would hide the errors this exercise exists to find.

Enter an empty line to finish a case. Type SKIP alone to abstain on a case.
"""


def load_corpora(paths):
    idx = {}
    for p in paths:
        name = pathlib.Path(p).name
        for i, line in enumerate(pathlib.Path(p).read_text(encoding="utf-8").splitlines()):
            if line.strip():
                idx[(name, i)] = json.loads(line)
    return idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--labeller", required=True, help="your name; goes in the output filename")
    ap.add_argument("--corpus", action="append", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    sample = json.loads(pathlib.Path(a.sample).read_text(encoding="utf-8"))
    corpora = load_corpora(a.corpus)
    outp = pathlib.Path(a.out or ("kappa_labels_%s.jsonl" % a.labeller))

    done = set()
    if outp.exists():
        for line in outp.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["case_id"])

    todo = [c for c in sample["cases"] if c["case_id"] not in done]
    print(TOOL_VERSION)
    print("SAMPLE    %s  (seed %s, n=%d)" % (a.sample, sample["seed"], sample["n_drawn"]))
    print("LABELLER  %s" % a.labeller)
    print("DONE      %d   REMAINING %d" % (len(done), len(todo)))
    if not todo:
        print("\nAll cases labelled. Run kappa_compute.py next.")
        return 0
    print(RULES)
    input("Press Enter to begin. Ctrl-C is safe at any point. ")

    for n, c in enumerate(todo, 1):
        row = corpora.get((c["corpus"], c["line"]))
        if row is None:
            print("SKIP %s: not found in the supplied corpora" % c["case_id"])
            continue
        q = row["request_payload"]["messages"][0]["content"]
        print("\n" + "=" * 70)
        print("CASE %s   (%d of %d this session)" % (c["case_id"], n, len(todo)))
        print("=" * 70)
        print("QUESTION ASKED:\n  %s\n" % q)
        print("-" * 70)
        print(row["response_text"])
        print("-" * 70)
        print("List the organisations presented as providers. Empty line ends. SKIP to abstain.")
        names, skipped = [], False
        while True:
            try:
                v = input("  > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nStopped. %d cases written to %s" % (len(done) + n - 1, outp))
                return 0
            if v.upper() == "SKIP":
                skipped = True
                break
            if not v:
                break
            names.append(v)
        rec = {
            "case_id": c["case_id"], "corpus": c["corpus"], "line": c["line"],
            "prompt_id": c["prompt_id"], "family": c["family"],
            "labeller": a.labeller,
            "skipped": skipped,
            "names": names,
            "ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        with outp.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
        print("  recorded: %s" % ("SKIP" if skipped else (", ".join(names) or "none")))

    print("\nComplete. %s" % outp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
