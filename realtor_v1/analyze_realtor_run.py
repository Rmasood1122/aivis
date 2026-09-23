#!/usr/bin/env python3
"""Analyze a realtor AI-visibility run (PREREG_realtor_test_v1).

Input: one or more JSONL files, one response per line. Field names are configurable
because runner schemas differ; defaults match common aivis-style rows.

    python analyze_realtor_run.py run_*.jsonl --out results_v1

Output (in --out dir):
    summary.txt            metrics per engine + overall (M1 is PROVISIONAL until candidates verified)
    person_candidates.csv  every candidate person name -> VERIFY each against NY DOS, fill 'verified'
    brokerages.csv         brokerage mention counts per engine
    domains.csv            cited / mentioned source domains per engine
    per_response.csv       one row per response with flags

Re-run with --verified person_candidates.csv (after filling the 'verified' column with
yes/no) to compute final M1/M2/M3/M5 on verified names only.
"""
import argparse, csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

BROKERAGES = [
    "Compass", "Douglas Elliman", "Corcoran", "Coldwell Banker", "Keller Williams", "RE/MAX", "Remax",
    "Century 21", "Brown Harris Stevens", "Daniel Gale", "Sotheby's", "Signature Premier", "Howard Hanna",
    "eXp Realty", "Realty ONE", "SERHANT", "Serhant", "Nest Seekers", "EXIT Realty", "Berkshire Hathaway",
    "Laffey", "Charles Rutenberg", "Weichert", "Halstead", "Redfin Agent", "Engel & Völkers", "Engel & Volkers",
]
DIRECTORIES = {
    "zillow": "Zillow", "realtor.com": "Realtor.com", "redfin": "Redfin", "streeteasy": "StreetEasy",
    "yelp": "Yelp", "google": "Google", "homelight": "HomeLight", "fastexpert": "FastExpert",
    "trulia": "Trulia", "upnest": "UpNest", "nextdoor": "Nextdoor", "angi": "Angi",
}
# Words that look like "First Last" but are not people: places, headings, firm words.
STOP = set("""
New York Long Island Queens Astoria Garden City Great Neck Forest Hills Jackson Heights Long Beach
Port Washington Rockville Centre City Real Estate Realty Group Team Home Homes Best Top The Agent Agents
Here Some Also However Note Look Check Consider Ask Search Google Zillow Redfin Realtor Local Luxury
Market Island North South East West Street Avenue Road Manhasset Huntington Massapequa Smithtown Syosset
Flushing Bayside Ridgewood Sunnyside Whitestone Nassau Suffolk County Brooklyn Manhattan Bronx NYC
Multiple Listing Service Board Association National Estate Properties Property Sotheby International
Williams Banker Coldwell Keller Douglas Elliman Brown Harris Stevens Daniel Gale Century Compass
Signature Premier Howard Hanna Coach Realtors Modern Spaces Nest Seekers Berkshire Hathaway Integrity Leaders
Gold Coast Sands Point Kings Point Saddle Rock Munsey Park Flower Hill Cold Spring Harbor Oyster Bay
Fresh Meadows Historic District School Districts Plandome Manorhaven Village Gardens Hollis Douglaston
Little Neck Elmhurst Woodside Maspeth Glendale Middle Kew Rego Corona Jamaica Howard Beach Rockaway
Mineola Hempstead Levittown Bellmore Merrick Wantagh Seaford Lynbrook Valley Stream Floral Franklin Square
Roslyn Glen Cove Head Hicksville Plainview Jericho Woodbury Bethpage Farmingdale Babylon Islip Bay Shore
Summary Table Next Steps Track Record Key Questions Additional Notable Associate Broker Licensed Salesperson
Why Them Best For Focus Notable Strengths Client Reviews Recent Sales Price Range Sales Volume Years Experience
Pro Tip Bottom Line Final Thoughts Quick Tips How Choose What Look Red Flags Questions Interview Selling
Buying Buyer Seller Listing Listings Condo Condos Coop Co-op Coops Family Single Multi Two Three
Top Rated Highly Recommended Strong Choice Good Option Consider Also Worth Noting Other Options
Chamber Commerce Public Schools High School Middle School Elementary Central Station Railroad LIRR Penn
""".split())
FIRM_WORDS = {"Realty", "Real", "Estate", "Group", "Team", "Homes", "Properties", "Brokerage", "Associates",
              "Partners", "International", "Company", "Co", "LLC", "Inc"}
# a candidate counts only if an agent cue appears near it
CUE_RE = re.compile(r"(agent|broker|realtor|realty|team|compass|elliman|keller|coldwell|sotheby|corcoran|"
                    r"exp|re/max|remax|century 21|howard hanna|daniel gale|signature premier|coach realtors|"
                    r"nest seekers|modern spaces|berkshire|brown harris|serhant|laffey|weichert|top producer|"
                    r"sales volume|transactions|closed|listing|reviews?|rating|\(|–|-)", re.I)
NAME_RE = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z]\.)?\s[A-Z][a-z]+(?:-[A-Z][a-z]+)?)\b")
URL_RE = re.compile(r"https?://[^\s)\]>\"']+")


def load(paths, f):
    rows = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    print(f"WARN {p}:{i} not JSON, skipped", file=sys.stderr)
                    continue
                text = r.get(f["text"]) or ""
                if not text:
                    print(f"WARN {p}:{i} empty {f['text']}, skipped", file=sys.stderr)
                    continue
                cites = r.get(f["citations"]) or []
                if isinstance(cites, str):
                    cites = [cites]
                norm = []
                for c in cites:
                    if isinstance(c, dict):
                        u, t = c.get("url", ""), (c.get("title") or "").strip()
                        # Gemini grounding returns Google redirect URLs; the real host is in the title.
                        if "vertexaisearch" in u and t and " " not in t and "." in t:
                            u = "https://" + t
                        norm.append(u)
                    else:
                        norm.append(str(c))
                cites = norm
                rows.append({
                    "engine": str(r.get(f["engine"], "unknown")),
                    "prompt_id": str(r.get(f["prompt_id"], "unknown")),
                    "rep": str(r.get(f["rep"], "")),
                    "text": text,
                    "citations": cites,
                })
    return rows


def people(text):
    out = set()
    for m in NAME_RE.finditer(text):
        name = m.group(1)
        parts = [w for w in re.split(r"[\s-]", name) if w and not w.endswith(".")]
        if any(w in STOP for w in parts) or parts[-1] in FIRM_WORDS:
            continue
        window = text[max(0, m.start() - 60): m.end() + 80]
        if not CUE_RE.search(window):
            continue
        out.add(name)
    return out


def brokerages(text):
    low = text.lower()
    return {b for b in BROKERAGES if b.lower() in low}


def domains(text, cites):
    found = set()
    for u in list(cites) + URL_RE.findall(text):
        host = urlparse(u).netloc.lower().removeprefix("www.").split("?")[0]
        if host:
            found.add(host)
    low = text.lower()
    for key, name in DIRECTORIES.items():
        if key in low:
            found.add(name + " (mentioned)")
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", default="results_v1")
    ap.add_argument("--min-responses", type=int, default=1, help="only list candidates seen in >= N responses")
    ap.add_argument("--verified", help="person_candidates.csv with 'verified' column filled yes/no")
    ap.add_argument("--f-engine", default="engine")
    ap.add_argument("--f-prompt", default="prompt_id")
    ap.add_argument("--f-rep", default="rep")
    ap.add_argument("--f-text", default="response_text")
    ap.add_argument("--f-citations", default="citations")
    a = ap.parse_args()
    f = {"engine": a.f_engine, "prompt_id": a.f_prompt, "rep": a.f_rep,
         "text": a.f_text, "citations": a.f_citations}

    rows = load(a.files, f)
    if not rows:
        sys.exit("No usable rows. Check --f-text and other field names against your JSONL.")

    verified = None
    if a.verified:
        verified = {}
        with open(a.verified, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                v = (r.get("verified") or "").strip().lower()
                if v not in ("yes", "no"):
                    sys.exit(f"Unverified row for '{r['name']}': fill verified=yes/no for EVERY candidate.")
                verified[r["name"]] = v == "yes"

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    per_engine = defaultdict(lambda: Counter())
    cand = defaultdict(lambda: {"responses": 0, "engines": set(), "areas": set(), "example": ""})
    reps_by_key = defaultdict(set)     # (name, prompt, engine) -> reps
    brok = defaultdict(Counter)
    dom = defaultdict(Counter)
    per_resp = []

    for r in rows:
        e = r["engine"]
        ppl = people(r["text"])
        vppl = {p for p in ppl if verified.get(p)} if verified is not None else ppl
        unv = {p for p in ppl if verified is not None and not verified.get(p)}
        bks = brokerages(r["text"])
        dms = domains(r["text"], r["citations"])
        deflect = not ppl and not bks and any(d.endswith("(mentioned)") for d in dms)

        c = per_engine[e]
        c["n"] += 1
        c["named_person"] += bool(vppl)
        c["unverified_person_mentions"] += len(unv)
        c["person_mentions"] += len(ppl)
        c["named_brokerage"] += bool(bks)
        c["pure_deflection"] += deflect
        c["has_citations"] += bool(r["citations"])
        for p in ppl:
            d = cand[p]; d["responses"] += 1; d["engines"].add(e); d["areas"].add(r["prompt_id"])
            if not d["example"]:
                i = r["text"].find(p); d["example"] = r["text"][max(0, i-60): i+80].replace("\n", " ")
        for p in vppl:
            reps_by_key[(p, r["prompt_id"], e)].add(r["rep"])
        for b in bks: brok[e][b] += 1
        for d in dms: dom[e][d] += 1
        per_resp.append([e, r["prompt_id"], r["rep"], len(ppl), len(vppl), ";".join(sorted(bks)), int(deflect),
                         len(r["citations"])])

    with open(out / "per_response.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["engine", "prompt_id", "rep", "person_candidates", "persons_counted", "brokerages",
                    "pure_deflection", "n_citations"])
        w.writerows(per_resp)

    if verified is None:
        with open(out / "person_candidates.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["name", "responses", "engines", "prompts", "example_context", "verified"])
            for n, d in sorted(cand.items(), key=lambda kv: -kv[1]["responses"]):
                if d["responses"] < a.min_responses:
                    continue
                w.writerow([n, d["responses"], ";".join(sorted(d["engines"])), ";".join(sorted(d["areas"])),
                            d["example"], ""])

    with open(out / "brokerages.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["engine", "brokerage", "responses"])
        for e, c in sorted(brok.items()):
            for b, k in c.most_common(): w.writerow([e, b, k])
    with open(out / "domains.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["engine", "domain", "responses"])
        for e, c in sorted(dom.items()):
            for d, k in c.most_common(): w.writerow([e, d, k])

    # M2 consistency (>=3 of 5 reps same prompt+engine), M3 cross-engine (>=2 engines same prompt)
    consistent = {p for (p, _, _), reps in reps_by_key.items() if len(reps) >= 3}
    by_prompt = defaultdict(set)
    for (p, pid, e) in reps_by_key: by_prompt[(p, pid)].add(e)
    cross = {p for (p, _), es in by_prompt.items() if len(es) >= 2}

    tot = Counter()
    for c in per_engine.values(): tot.update(c)
    status = "FINAL (verified names only)" if verified is not None else \
        "PROVISIONAL — person counts are UNVERIFIED regex candidates; verify person_candidates.csv, re-run with --verified"
    lines = [f"Realtor AI-visibility run — {status}", f"Responses: {tot['n']}", ""]
    for e, c in sorted(per_engine.items()) + [("OVERALL", tot)]:
        n = c["n"] or 1
        lines.append(f"[{e}] n={c['n']}  M1 named-person={c['named_person']/n:.0%}  "
                     f"brokerage={c['named_brokerage']/n:.0%}  M4 deflection={c['pure_deflection']/n:.0%}  "
                     f"with-citations={c['has_citations']/n:.0%}")
    lines += ["", f"M2 agents named in >=3/5 reps (same prompt+engine): {len(consistent)}",
              f"M3 agents named by >=2 engines (same prompt): {len(cross)}"]
    if verified is not None and tot["person_mentions"]:
        lines.append(f"M5 unverified share of person mentions: {tot['unverified_person_mentions']/tot['person_mentions']:.0%}")
    if verified is not None:
        m1 = tot["named_person"] / (tot["n"] or 1)
        bk = tot["named_brokerage"] / (tot["n"] or 1)
        m5 = tot["unverified_person_mentions"] / tot["person_mentions"] if tot["person_mentions"] else 0
        if m1 >= 0.30 and len(consistent) >= 10 and m5 <= 0.25: verdict = "GO — solo-agent product"
        elif m1 < 0.10 and bk < 0.50: verdict = "KILL for realtors"
        elif m1 < 0.30 and bk >= 0.50: verdict = "PIVOT — brokerage product"
        else: verdict = "INCONCLUSIVE — re-run with web search ON for all engines"
        lines += ["", f"PREREG v1 verdict: {verdict}"]
    (out / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
