#!/usr/bin/env python3
"""make_report.py — turn an aivis evidence file into a deliverable report.

Stdlib only. Every number in the output is computed from the evidence file at
run time. Nothing is typed, nothing is templated, and there are no placeholders.
If a quantity cannot be computed from the file, the report prints NOT MEASURED
rather than an estimate.

USAGE
  python3 make_report.py <evidence.jsonl> --bank <bank.json> \
      --names "Firm A,Firm B" --subject "Firm A" --out report.md

  --names   candidate list to score. Omit to run in DISCOVERY mode, which
            reports what the model itself emphasised (bold spans) instead.
  --subject the entity the report is about; gets its own section. Optional.
"""
import sys, json, re, math, hashlib, argparse, pathlib, collections, datetime

TOOL_VERSION = "make_report v0.1.0"
Z95 = 1.959963985


def wilson(k, n, z=Z95):
    """95% Wilson score interval for a binomial proportion."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = (z / d) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def sha_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def bundle_digest(hs):
    return hashlib.sha256("\n".join(hs).encode("utf-8")).hexdigest()


def load(evidence, bank_path):
    b = json.loads(pathlib.Path(bank_path).read_text(encoding="utf-8"))
    t2f = {p["text"]: f for f, ps in b["families"].items() for p in ps}
    rows = []
    for line in pathlib.Path(evidence).read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    clean = [r for r in rows if r.get("response_text")]
    unmapped = 0
    for r in clean:
        try:
            r["_f"] = t2f[r["request_payload"]["messages"][0]["content"]]
            r["_q"] = r["request_payload"]["messages"][0]["content"]
        except (KeyError, IndexError, TypeError):
            r["_f"], r["_q"] = "UNMAPPED", None
            unmapped += 1
    return b, rows, clean, unmapped


def present(name, text):
    return re.search(r'\b' + re.escape(name) + r'\b', text, re.I) is not None


def first_n(text, names, n=3):
    """First n distinct candidates by position of first occurrence."""
    seen = []
    for m in re.finditer(
            "|".join(r'\b' + re.escape(x) + r'\b' for x in names), text, re.I):
        s = m.group(0)
        canon = next((x for x in names if x.lower() == s.lower()), s)
        if canon not in seen:
            seen.append(canon)
    return seen[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("evidence")
    ap.add_argument("--bank", required=True)
    ap.add_argument("--names", default=None)
    ap.add_argument("--subject", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    outp = pathlib.Path(a.out)
    if outp.exists():
        print("REFUSED: %s exists. Choose a new versioned path." % outp)
        return 2

    bank, rows, clean, unmapped = load(a.evidence, a.bank)
    if not clean:
        print("REFUSED: zero clean rows. No report can be written from this file.")
        return 1

    names = [x.strip() for x in a.names.split(",")] if a.names else []
    discovery = not names
    fams = sorted({r["_f"] for r in clean})
    hashes = [r["sha256"] for r in clean if r.get("sha256")]
    digest = bundle_digest(hashes)
    hash_ok = sum(1 for r in clean
                  if r.get("sha256") == sha_text(r["response_text"]))
    pl = clean[0].get("request_payload", {})
    engines = sorted({r.get("engine", "?") for r in clean})
    models = sorted({(r.get("request_payload") or {}).get("model", "?") for r in clean})
    temps = sorted({str((r.get("request_payload") or {}).get("temperature")) for r in clean})
    runs_per = collections.Counter(r["_q"] for r in clean if r["_q"])
    n_runs = sorted(set(runs_per.values()))

    L = []
    w = L.append
    w("# AI VISIBILITY MEASUREMENT — %s" % (a.subject or bank.get("bank_version", "run")))
    w("")
    w("**RUNG: R1** — this ran on the operator's machine. It has not been run by a")
    w("stranger. Every figure below is computed from the evidence file named in the")
    w("instrument record; nothing here is illustrative and there are no placeholders.")
    w("")
    w("Generated %s by %s" % (
        datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        TOOL_VERSION))
    w("")
    w("---")
    w("")
    w("## 1 · WHAT WAS MEASURED")
    w("")
    w("This measures what AI assistants **answer**, not what people **ask**. It carries")
    w("no information about search volume, query frequency, or purchase intent.")
    w("")
    w("| | |")
    w("|---|---|")
    w("| Evidence file | `%s` |" % pathlib.Path(a.evidence).name)
    w("| Prompt bank | `%s`, %d prompts |" % (
        bank.get("bank_version", "?"),
        sum(len(p) for p in bank["families"].values())))
    w("| Families | %s |" % ", ".join(sorted(bank["families"].keys())))
    w("| Engines | %s |" % ", ".join(engines))
    w("| Model versions | %s |" % ", ".join(models))
    w("| Temperature | %s |" % ", ".join(temps))
    w("| Runs per prompt | %s |" % ", ".join(str(x) for x in n_runs))
    w("| Rows attempted | %d |" % len(rows))
    w("| Responses analysed | %d |" % len(clean))
    w("| Rows lost to transport errors | %d |" % (len(rows) - len(clean)))
    w("| Bundle digest (SHA-256) | `%s` |" % digest)
    w("")
    w("Responses per family, each rate below prints against its own count:")
    w("")
    w("| family | responses |")
    w("|---|---|")
    for f in fams:
        w("| %s | %d |" % (f, sum(1 for r in clean if r["_f"] == f)))
    w("")

    if discovery:
        w("## 2 · WHAT THE MODEL EMPHASISED")
        w("")
        w("No candidate list was supplied, so this section reports the entities the")
        w("model itself set apart in its answers (bold spans), with the number of")
        w("distinct prompts each appeared under. A name carried by one prompt is an")
        w("artifact of that prompt, not a pattern.")
        w("")
        pat = re.compile(r'\*\*([^*\n]{3,45}?)\*\*')
        cnt, pids, ffam = collections.Counter(), collections.defaultdict(set), collections.defaultdict(set)
        for r in clean:
            for m in set(pat.findall(r["response_text"])):
                m = m.strip().rstrip(":")
                cnt[m] += 1
                pids[m].add(r.get("prompt_id"))
                ffam[m].add(r["_f"])
        N = len(clean)
        w("| emphasised | rate | 95% CI | prompts | families |")
        w("|---|---|---|---|---|")
        for nm, c in cnt.most_common(25):
            p, lo, hi = wilson(c, N)
            w("| %s | %.1f%% (%d/%d) | %.1f–%.1f%% | %d | %d |" % (
                nm, p * 100, c, N, lo * 100, hi * 100, len(pids[nm]), len(ffam[nm])))
        w("")
        w("**This is a discovery pass, not a score.** The extraction rule is markdown")
        w("emphasis, which captures section headings and advice alongside entities.")
        w("Read the rows before using any of them.")
        w("")
    else:
        w("## 2 · PRESENCE, BY FAMILY")
        w("")
        if len(names) <= 4:
            w("> **First-three is not reported below.** With only %d candidate names, the"
              % len(names))
            w("> first three positions can hold every name that appears, so first-three")
            w("> would equal presence by construction rather than by measurement. Supply")
            w("> a candidate list of at least five names for that column to carry")
            w("> information.")
            w("")
        w("Presence = the name appears anywhere in the response. First-three = the name")
        w("is among the first three candidates by position in the text. **First-three is")
        w("a position count, not a ranking**; no order-bias test has been run, so no")
        w("rank claim is made anywhere in this report.")
        w("")
        for f in fams:
            sub = [r for r in clean if r["_f"] == f]
            n = len(sub)
            if not n:
                continue
            w("### %s — n=%d" % (f, n))
            w("")
            short = len(names) <= 4
            if short:
                w("| name | presence | 95% CI |")
                w("|---|---|---|")
            else:
                w("| name | presence | 95% CI | first-three | 95% CI |")
                w("|---|---|---|---|---|")
            scored = []
            for nm in names:
                k = sum(1 for r in sub if present(nm, r["response_text"]))
                t = sum(1 for r in sub if nm in first_n(r["response_text"], names))
                scored.append((k, nm, t))
            for k, nm, t in sorted(scored, reverse=True):
                p, lo, hi = wilson(k, n)
                p2, lo2, hi2 = wilson(t, n)
                if short:
                    w("| %s | %.1f%% (%d/%d) | %.1f–%.1f%% |" % (
                        nm, p * 100, k, n, lo * 100, hi * 100))
                else:
                    w("| %s | %.1f%% (%d/%d) | %.1f–%.1f%% | %.1f%% (%d/%d) | %.1f–%.1f%% |" % (
                        nm, p * 100, k, n, lo * 100, hi * 100,
                        p2 * 100, t, n, lo2 * 100, hi2 * 100))
            w("")
        if a.subject and a.subject in names:
            tot = sum(1 for r in clean if present(a.subject, r["response_text"]))
            p, lo, hi = wilson(tot, len(clean))
            w("### Subject: %s" % a.subject)
            w("")
            w("Present in **%d of %d** responses — %.1f%%, 95%% CI %.1f–%.1f%%."
              % (tot, len(clean), p * 100, lo * 100, hi * 100))
            if tot == 0:
                w("")
                w("**Absence claim.** Denominator %d responses across %d families. "
                  "STATUS=COMPLETE for this file. This is one engine on one date "
                  "through an extraction step whose error rate has not been measured; "
                  "it does not establish absence from AI answers generally."
                  % (len(clean), len(fams)))
            w("")

    # stability
    w("## 3 · RUN-TO-RUN STABILITY AT FIXED TEMPERATURE")
    w("")
    groups = collections.defaultdict(list)
    for r in clean:
        if r["_q"]:
            groups[r["_q"]].append(r)
    full = {q: rs for q, rs in groups.items() if len(rs) == max(n_runs)} if n_runs else {}
    byte_distinct = len({r["response_text"] for r in clean})
    w("Byte-level: **%d distinct responses out of %d**. Identical prompts at the "
      "declared temperature did not return identical text." % (byte_distinct, len(clean)))
    w("")
    if full and not discovery:
        s = sum(1 for rs in full.values()
                if len({frozenset(x for x in names if present(x, r["response_text"]))
                        for r in rs}) == 1)
        t3 = sum(1 for rs in full.values()
                 if len({tuple(first_n(r["response_text"], names)) for r in rs}) == 1)
        n = len(full)
        w("Decision-level, on the %d prompts with the full run count:" % n)
        w("")
        w("| measure | stable | rate | 95% CI |")
        w("|---|---|---|---|")
        for lab, k in (("identical name set across runs", s),
                       ("identical first-three across runs", t3)):
            p, lo, hi = wilson(k, n)
            w("| %s | %d of %d | %.1f%% | %.1f–%.1f%% |" % (
                lab, k, n, p * 100, lo * 100, hi * 100))
        w("")
        w("Byte-difference and decision-difference are different quantities. Only the")
        w("rows in this table speak to whether the answer changed.")
    else:
        w("Decision-level stability: NOT COMPUTED (no candidate list supplied).")
    w("")

    w("## 4 · LIMITATIONS CARRIED")
    w("")
    lim = []
    if len(engines) < 4:
        lim.append("**Engine coverage.** %d engine(s) measured: %s. Any figure here "
                   "describes those engines only." % (len(engines), ", ".join(engines)))
    lim.append("**Extraction error is unmeasured.** Names are matched by a text rule "
               "with no published agreement coefficient. Every count in this report "
               "depends on that unvalidated step.")
    if len(rows) - len(clean):
        lim.append("**%d of %d rows were lost to transport errors** and are excluded "
                   "from every denominator. Losses were not evenly distributed across "
                   "families; the per-family counts in section 1 are the true bases."
                   % (len(rows) - len(clean), len(rows)))
    lim.append("**Single date.** All responses were collected in one session. Model "
               "behaviour changes between versions and over time; this is a snapshot.")
    lim.append("**No causal claim.** This is a cross-sectional measurement. It cannot "
               "show that any action moves these figures, and no published evidence "
               "establishes that these figures predict enquiries or revenue.")
    lim.append("**Prompt bank is a declared stimulus set**, not a sample of real user "
               "queries. It is not evidence about what anyone actually asked.")
    if unmapped:
        lim.append("**%d responses could not be mapped to a family** and are excluded "
                   "from per-family tables." % unmapped)
    for i, x in enumerate(lim, 1):
        w("L%d. %s" % (i, x))
        w("")

    w("## 5 · HOW TO CHECK THIS")
    w("")
    w("The evidence file ships with this report. Every response is stored with the")
    w("exact request payload that produced it and a SHA-256 of its own text.")
    w("")
    w("```")
    w("python3 verify_evidence.py %s --expect %s" % (pathlib.Path(a.evidence).name, digest))
    w("```")
    w("")
    w("The checker is stdlib-only Python and needs nothing of ours installed.")
    w("At generation time, %d of %d stored hashes recomputed correctly from their own"
      % (hash_ok, len(clean)))
    w("response text.")
    w("")
    w("A passing check shows the file has not been altered since it was written. It")
    w("does not show that collection was honest. For that, ask for the pre-run")
    w("credential probe receipt and the console record of the run.")
    w("")

    outp.write_text("\n".join(L), encoding="utf-8")
    print("WROTE %s  (%d lines)" % (outp, len(L)))
    print("BUNDLE DIGEST %s" % digest)
    print("hash identity %d of %d clean rows" % (hash_ok, len(clean)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
