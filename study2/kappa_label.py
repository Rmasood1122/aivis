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

HOW TO ENTER
  Type the names. You may put several on one line separated by commas, or one per
  line, or both. Press Enter on an empty line when the case is done.

  If the response names NO organisations at all, type NONE. An empty first line is
  NOT accepted -- a blank and a genuine "no organisations here" are different
  answers and this tool will not let them look the same.

  Type SKIP alone to abstain on a case you cannot judge.
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
    try:
        input("Press Enter to begin. Ctrl-C exits cleanly; finished cases are kept. ")
    except (EOFError, KeyboardInterrupt):
        print("\nNot started."); return 0

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
        names, skipped, none_declared = [], False, False
        while True:
            try:
                v = input("  > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nStopped. %d cases written to %s" % (len(done) + n - 1, outp))
                return 0
            if v.upper() == "SKIP":
                skipped = True
                break
            if v.upper() == "NONE":
                none_declared = True
                break
            if not v:
                if names:
                    break
                print("     Nothing entered. Type the names, or NONE if this response")
                print("     names no organisations, or SKIP to abstain.")
                continue
            for part in v.split(","):
                part = part.strip()
                if part and part not in names:
                    names.append(part)
            print("     [%d so far] %s" % (len(names), ", ".join(names)))
        rec = {
            "case_id": c["case_id"], "corpus": c["corpus"], "line": c["line"],
            "prompt_id": c["prompt_id"], "family": c["family"],
            "labeller": a.labeller,
            "skipped": skipped,
            "none_declared": none_declared,
            "names": names,
            "ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        with outp.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
        print("  recorded: %s" % ("SKIP" if skipped else
              ("NONE (explicit)" if none_declared else ", ".join(names))))
        total_done = len(done) + n
        print("  progress: %d of %d" % (total_done, sample["n_drawn"]))
        if n < len(todo) and total_done % 20 == 0:
            print("\n--- %d done. Good point to stop; it resumes here. ---" % total_done)
            try:
                if input("    Enter to continue, or type STOP: ").strip().upper() == "STOP":
                    print("Stopped at %d. Re-run the same command to resume." % total_done)
                    return 0
            except (EOFError, KeyboardInterrupt):
                return 0

    allrec = [json.loads(l) for l in outp.read_text(encoding="utf-8").splitlines() if l.strip()]
    named = sum(1 for r in allrec if r.get("names"))
    nones = sum(1 for r in allrec if r.get("none_declared"))
    skips = sum(1 for r in allrec if r.get("skipped"))
    print("\nComplete. %s" % outp)
    print("  cases %d | with names %d | explicit NONE %d | SKIP %d"
          % (len(allrec), named, nones, skips))
    if named == 0:
        print("\n  WARNING: not one case recorded a name. Do NOT compute kappa from")
        print("  this file -- it would measure an empty gold standard and return a")
        print("  number that looks real. Rename it VOID_ and relabel.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
