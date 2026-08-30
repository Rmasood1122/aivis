#!/usr/bin/env python3
"""criteria_miner.py — what the models tell buyers to look for.

Stdlib only. Reads an aivis evidence file and reports, per prompt family, which
evaluation criteria the model recites when someone asks how to choose a vendor.

WHY THIS EXISTS
  In the 2026-08-29 PR-agency run, buyer_intent responses named almost no firms.
  They returned CRITERIA: track record, case studies, media relationships,
  realistic promises, Clutch, HARO. If that holds, the leverage for a vendor is
  not being ranked -- it is visibly satisfying the criteria buyers arrive with.
  This tool measures which criteria, at what rate, against a stated denominator.

THE HONEST LIMIT, STATED BEFORE ANY OUTPUT
  The CANON map below is DECLARED, not learned. Every grouping in it is a
  judgement made by a human before the counts were seen. A different analyst
  would group differently and get different numbers. Until a labelled set and an
  agreement coefficient exist, every rate this prints is an unvalidated parse
  and must carry that sentence wherever it travels.

USAGE
  python3 criteria_miner.py <evidence.jsonl> --bank <bank.json>
  python3 criteria_miner.py <evidence.jsonl> --bank <bank.json> --families buyer_intent,problem
  python3 criteria_miner.py <evidence.jsonl> --bank <bank.json> --show track_record
"""
import sys, json, re, argparse, pathlib, collections, signal
if hasattr(signal, "SIGPIPE"):  # not present on Windows
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

TOOL_VERSION = "criteria_miner v0.1.0"
CANON_SEALED = "2026-08-29"

# ---------------------------------------------------------------------------
# DECLARED CANON. Written before counting. Each key is a criterion; each value
# is the list of surface patterns that count as it. Case-insensitive substring
# match on the response text. Add patterns only by amending this file and
# re-dating CANON_SEALED -- never mid-analysis.
# ---------------------------------------------------------------------------
CANON = {
    "track_record":       ["track record", "proven results", "past results", "results they"],
    "case_studies":       ["case study", "case studies", "portfolio of work"],
    "media_relationships":["media relationship", "journalist relationship", "editor relationship",
                           "press contacts", "media contacts", "relationships with journalists"],
    "realistic_promises": ["realistic expectation", "realistic promise", "guarantee",
                           "no one can guarantee", "beware of guarantees", "unrealistic"],
    "third_party_reviews":["clutch", "g2.com", "trustpilot", "client review", "testimonial",
                           "references from", "speak to past clients", "reviews"],
    "transparent_pricing":["transparent pricing", "clear pricing", "pricing upfront",
                           "how much", "retainer", "cost structure", "budget"],
    "beat_specialisation":["beat specialization", "beat specialisation", "industry specialization",
                           "niche expertise", "sector expertise", "specializes in your"],
    "named_team":         ["who will actually", "team assigned", "senior staff", "account manager",
                           "who works on your account"],
    "owned_media_diy":    ["haro", "help a reporter out", "qwoted", "sourcebottle",
                           "do it yourself", "pitch journalists yourself"],
    "contributor_warning":["contributor content", "contributor network", "forbes council",
                           "paid placement", "pay to play", "pay-to-play", "sponsored content"],
    "clear_contract":     ["contract term", "month-to-month", "exit clause", "lock-in",
                           "cancellation"],
    "reporting_cadence":  ["monthly report", "reporting cadence", "how they measure",
                           "kpi", "metrics they report"],
}


def load_family_map(bank_path):
    b = json.loads(pathlib.Path(bank_path).read_text(encoding="utf-8"))
    return {p["text"]: f for f, ps in b["families"].items() for p in ps}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("evidence")
    ap.add_argument("--bank", required=True)
    ap.add_argument("--families", default=None,
                    help="comma-separated; default is every family, reported separately")
    ap.add_argument("--show", default=None,
                    help="print excerpts for one criterion so you can check the parse")
    a = ap.parse_args()

    t2f = load_family_map(a.bank)
    rows = []
    for line in pathlib.Path(a.evidence).read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    clean = [r for r in rows if r.get("response_text")]
    for r in clean:
        try:
            r["_f"] = t2f[r["request_payload"]["messages"][0]["content"]]
        except (KeyError, IndexError, TypeError):
            r["_f"] = "UNMAPPED"

    unmapped = sum(1 for r in clean if r["_f"] == "UNMAPPED")
    fams = sorted({r["_f"] for r in clean})
    if a.families:
        want = [x.strip() for x in a.families.split(",")]
        fams = [f for f in fams if f in want]

    print(TOOL_VERSION + "  |  CANON sealed " + CANON_SEALED)
    print("EVIDENCE   %s" % pathlib.Path(a.evidence).name)
    print("CLEAN ROWS %d of %d   |  unmapped to a family: %d" % (len(clean), len(rows), unmapped))
    print("CANON      %d criteria, DECLARED before counting" % len(CANON))

    if a.show:
        pats = CANON.get(a.show)
        if not pats:
            print("\nno such criterion: %s" % a.show); return 2
        print("\nEXCERPTS for '%s' -- read these, the parse is unvalidated" % a.show)
        shown = 0
        for r in clean:
            if a.families and r["_f"] not in fams:
                continue
            t = r["response_text"]
            for p in pats:
                m = re.search(re.escape(p), t, re.I)
                if m:
                    i = m.start()
                    print("  [%s/%s] ...%s..." % (r["_f"], r.get("prompt_id"),
                          t[max(0, i-140):i+140].replace("\n", " ")))
                    shown += 1
                    break
            if shown >= 12:
                break
        return 0

    for f in fams:
        sub = [r for r in clean if r["_f"] == f]
        n = len(sub)
        if not n:
            continue
        print("\n=== %s   n=%d responses ===" % (f.upper(), n))
        counts = []
        for crit, pats in CANON.items():
            c = sum(1 for r in sub
                    if any(re.search(re.escape(p), r["response_text"], re.I) for p in pats))
            counts.append((c, crit))
        for c, crit in sorted(counts, reverse=True):
            if c:
                print("  %-22s %5.1f%%   %3d of %d" % (crit, c / n * 100, c, n))
        zero = [crit for c, crit in counts if c == 0]
        if zero:
            print("  ZERO in this family: %s" % ", ".join(sorted(zero)))

    print("\n" + "-" * 62)
    print("EVERY RATE ABOVE IS AN UNVALIDATED PARSE. The CANON map is a declared")
    print("judgement, not a measurement. No agreement coefficient exists for it.")
    print("Run with --show <criterion> and read the excerpts before quoting any row.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
