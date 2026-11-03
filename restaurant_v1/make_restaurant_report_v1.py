#!/usr/bin/env python3
"""make_restaurant_report_v1.py - PDF report for one market of the restaurant_v1 test.

Report layer only. It measures nothing itself: every name count comes from analyse() in
analyze_restaurant_run_v1.py, run here on the same run files, and the result is cross-checked against
the committed analysis directory - if the two disagree the report is refused. Row counts and bundle
digests are recomputed from the run files with the verifier's own bundle_digest().

Whether the report is PRELIMINARY or VERIFIED is decided by the inputs, not by a flag:
no --verified sheet = preliminary, and the first page says so in a box.

Usage (repo root):
  python restaurant_v1/make_restaurant_report_v1.py \\
      --runs restaurant_v1/runs/multi_*_nyc_restaurant_v1_20261006.jsonl \\
      --results restaurant_v1/results_nyc_v1 \\
      --out restaurant_v1/reports/aivis_restaurant_nyc_prelim_20261006_v1.pdf
  add --verified <filled sheet> and/or --merges <merge list> exactly as given to the analyzer.

Refuses: an existing --out; a results directory that does not match the run files.
Needs reportlab (already a dependency of this repo).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ENGINE_NAMES = {"openai": "ChatGPT", "anthropic": "Claude", "gemini": "Gemini", "perplexity": "Perplexity"}
INK, MUTED, RULE, WARN_BG, WARN_EDGE, OK_BG, OK_EDGE, HEAD_BG = (
    colors.HexColor("#1b1f24"), colors.HexColor("#5b6470"), colors.HexColor("#c9d0d8"), colors.HexColor("#fdf1e7"),
    colors.HexColor("#b4530a"), colors.HexColor("#eaf5ee"), colors.HexColor("#1f7a45"), colors.HexColor("#eef1f4"))


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ar = _load(HERE / "analyze_restaurant_run_v1.py", "restaurant_analyzer_for_report")
bundle_digest = _load(ROOT / "study2" / "zenodo_v1" / "verify_evidence.py", "verify_evidence_for_report").bundle_digest

REPLACED = Counter()


def safe(text) -> str:
    """Text the built-in PDF fonts can draw. Anything outside cp1252 is reduced to its base letters and
    counted, so a changed character is reported on the last page instead of silently becoming '?'."""
    s = str(text).replace("≥", ">=").replace("≤", "<=").replace("→", "->")
    out = []
    for ch in s:
        try:
            ch.encode("cp1252")
            out.append(ch)
        except UnicodeEncodeError:
            base = "".join(c for c in unicodedata.normalize("NFKD", ch) if not unicodedata.combining(c))
            try:
                base.encode("cp1252")
            except UnicodeEncodeError:
                base = "?"
            REPLACED[ch] += 1
            out.append(base or "?")
    return "".join(out).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def styles():
    base = dict(fontName="Helvetica", textColor=INK, leading=14, fontSize=10)
    return {
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=INK, spaceAfter=4),
        "sub": ParagraphStyle("sub", fontName="Helvetica", fontSize=11, leading=15, textColor=MUTED, spaceAfter=10),
        "h": ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=INK, spaceBefore=10, spaceAfter=6),
        "p": ParagraphStyle("p", spaceAfter=6, **base),
        "li": ParagraphStyle("li", leftIndent=12, bulletIndent=2, spaceAfter=4, **base),
        "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=MUTED, spaceAfter=4),
        "mono": ParagraphStyle("mono", fontName="Courier", fontSize=8, leading=10.5, textColor=INK),
        "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=9, leading=11.5, textColor=INK),
        "cellb": ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=9, leading=11.5, textColor=INK),
        "box": ParagraphStyle("box", fontName="Helvetica", fontSize=10, leading=14, textColor=INK),
    }


def table(rows, widths, st, header=True, align_right=()):
    data = [[Paragraph(safe(c), st["cellb"] if (header and i == 0) else st["cell"]) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    cmds = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
            ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if header:
        cmds.append(("BACKGROUND", (0, 0), (-1, 0), HEAD_BG))
    t.setStyle(TableStyle(cmds))
    return t


def box(text, st, bg, edge):
    t = Table([[Paragraph(text, st["box"])]], colWidths=[7.0 * inch])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("BOX", (0, 0), (-1, -1), 1.0, edge),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return t


def wilson_pct(k, n):
    _, lo, hi = ar.wilson(k, n)
    return "%.0f-%.0f%%" % (100 * lo, 100 * hi)


def evidence_facts(paths):
    out = []
    for p in paths:
        rows = [json.loads(line) for line in Path(p).read_text(encoding="utf-8").splitlines() if line.strip()]
        clean = [r for r in rows if r.get("response_text")]
        ok = sum(hashlib.sha256(r["response_text"].encode("utf-8")).hexdigest() == r.get("sha256") for r in clean)
        ts = sorted(r["ts"] for r in rows if r.get("ts"))
        out.append({
            "file": Path(p).name, "engine": rows[0].get("engine", "?"), "rows": len(rows), "clean": len(clean),
            "hash_match": ok, "digest": bundle_digest([r["sha256"] for r in clean if r.get("sha256")]),
            "model": ", ".join(sorted({str((r.get("request_payload") or {}).get("model")) for r in clean})),
            "tools": sum(bool((r.get("request_payload") or {}).get("tools")) for r in clean),
            "ts": (ts[0], ts[-1]) if ts else ("", ""),
        })
    return out


def cross_check(res, results_dir: Path):
    """The analysis recomputed here must equal the committed one, name for name and count for count."""
    path = results_dir / "candidates.csv"
    with path.open(encoding="utf-8", newline="") as f:
        committed = {r["key"]: int(r["responses"]) for r in csv.DictReader(f)}
    mine = dict(res["resp_count"])
    if committed != mine:
        diff = sorted(set(committed.items()) ^ set(mine.items()))[:5]
        sys.exit("REFUSE: %s does not match the run files given (first differences: %s). "
                 "Use the run files, --merges and --verified that produced it." % (path, diff))
    return len(committed)


def variant_pairs(res):
    """Counted names where one is a longer spelling of another in the same neighbourhood."""
    rc, areas = res["resp_count"], res["areas_of"]
    keys = sorted(k for k in rc if rc[k] >= ar.TIER_B_MIN)
    return [(s, l) for s in keys for l in keys
            if l != s and (l.startswith(s + " ") or l.endswith(" " + s)) and areas[s] & areas[l]]


def predictions(prereg: Path):
    out, on = [], False
    for line in prereg.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Predictions"):
            on = True
        elif on and line.startswith("## "):
            break
        elif on and line.startswith("- "):
            out.append(line[2:].strip())
    return out


def build(a):
    out = Path(a.out)
    if out.exists():
        sys.exit("REFUSE: %s exists. Versioned new paths only." % out)
    rows, errors, versions = ar.load_rows(a.runs)
    if len(versions) != 1 or not rows:
        sys.exit("REFUSE: need clean rows from exactly one bank; got %s" % dict(versions))
    merges = ar.read_merges(a.merges) if a.merges else None
    base = ar.analyse(rows, merges=merges)
    sheet, n_a, n_b = ar.verification_sheet(base)
    verified = ar.read_verified(a.verified, sheet) if a.verified else None
    res = ar.analyse(rows, verified, merges) if verified is not None else base
    n_names = cross_check(res, Path(a.results))
    ev = evidence_facts(a.runs)
    st = styles()
    n = res["n_total"]
    engines = sorted(res["by_engine"])
    disp = res["display"]
    prelim = verified is None
    bank = sorted(versions)[0]
    market = bank.split("_")[0].upper()
    t0, t1 = min(e["ts"][0] for e in ev), max(e["ts"][1] for e in ev)
    run_id = hashlib.sha256("\n".join(e["digest"] for e in ev).encode("utf-8")).hexdigest()

    # per-neighbourhood counts, straight from the analysis
    area_n, area_cnt, area_eng, first_cnt = Counter(), defaultdict(Counter), defaultdict(lambda: defaultdict(set)), Counter()
    cite, cut, names_per, eng_names = Counter(), Counter(), Counter(), defaultdict(set)
    domains = defaultdict(Counter)
    for r, m in zip(rows, res["mentions"]):
        area = r.get("area") or "?"
        area_n[area] += 1
        for k in m["counted"]:
            area_cnt[area][k] += 1
            area_eng[area][k].add(r["engine"])
            eng_names[r["engine"]].add(k)
        names_per[r["engine"]] += len(m["counted"])
        cites = r.get("citations") or []
        cite[r["engine"]] += bool(cites)
        cut[r["engine"]] += not ar.TERMINAL.search(r["response_text"].rstrip())
        for d in sorted({ar.domain_of(c) for c in cites}):
            domains[r["engine"]][d] += 1
        if m["first"]:
            first_cnt[(area, m["first"])] += 1
    areas = sorted(area_n, key=lambda x: (-max(area_cnt[x].values() or [0]), x))
    strong = sorted(((area_cnt[x][k], disp[k], x) for x in areas for k in area_cnt[x] if area_cnt[x][k] * 4 >= area_n[x] * 3),
                    key=lambda t: (-t[0], t[1]))
    suspects = sorted((k for k in res["resp_count"] if res["resp_count"][k] >= ar.TIER_A_MIN
                       and res["prose_only"][k] > res["struct_count"][k]), key=lambda k: (-res["resp_count"][k], k))
    pairs = variant_pairs(res)
    cited_total = sum(cite.values())

    S = []
    S.append(Paragraph("Which restaurants AI assistants name: %s" % safe(rows[0].get("family") or market), st["title"]))
    S.append(Paragraph("%d neighbourhoods, %d assistants, %d answers. Collected %s to %s UTC." % (
        len(area_n), len(engines), n, t0[:16].replace("T", " "), t1[:16].replace("T", " ")), st["sub"]))
    if prelim:
        S.append(box("<b>PRELIMINARY - NAMES NOT CHECKED.</b> Every name in this report was pulled out of the answers by "
                     "software. None has been checked against the real world, some entries are not restaurants, and "
                     "some restaurants appear under two spellings. The decision rule has not been evaluated. "
                     "Not for sending to any restaurant.", st, WARN_BG, WARN_EDGE))
    else:
        verdict, _ = ar.decision(res, sheet, verified)
        S.append(box("<b>CHECKED NAMES ONLY.</b> This report counts only names a person confirmed as an open restaurant "
                     "in the neighbourhood asked about. Decision rule: <b>%s</b>." % safe(verdict), st, OK_BG, OK_EDGE))
    S.append(Spacer(1, 8))
    face = ["ASSISTANTS %d | PROMPTS %d | RUNS PER PROMPT 5 | CLEAN ANSWERS %d of %d | ERROR ROWS %d" % (
                len(engines), len({r["prompt_id"] for r in rows}), n, n + sum(errors.values()), sum(errors.values())),
            "MODELS " + " | ".join("%s: %s" % (ENGINE_NAMES.get(e["engine"], e["engine"]), e["model"]) for e in ev),
            "SEARCH TOOL OFFERED on %d of %d answers | ANSWERS CITING A SOURCE %d of %d | OUTPUT CAP 8192 tokens" % (
                sum(e["tools"] for e in ev), n, cited_total, n),
            "PROMPT BANK %s | SURFACE developer API, not the consumer apps" % bank,
            "RUNG R1 (ran once on the operator's machine) | NAME EXTRACTION %s" % ar.PARSE_STATUS,
            "RUN ID %s" % run_id[:16]]
    S.append(Table([[Paragraph(safe(x), st["mono"])] for x in face], colWidths=[7.0 * inch],
                   style=TableStyle([("BOX", (0, 0), (-1, -1), 0.6, RULE), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                                     ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)])))
    S.append(Paragraph("What was asked", st["h"]))
    S.append(Paragraph("Twenty everyday questions about where to eat (best overall, date night, brunch, a group dinner, "
                       "cheap eats and so on), two for each of %d neighbourhoods. No question names a restaurant. Each "
                       "question was put to each assistant five times." % len(area_n), st["p"]))
    S.append(Paragraph("What came back", st["h"]))
    bullets = [
        "%d name%s appeared in at least three quarters of the answers for its own neighbourhood%s" % (
            len(strong), "" if len(strong) == 1 else "s",
            ": " + "; ".join("%s (%d of %d, %s)" % (nm, c, area_n[x], x) for c, nm, x in strong[:8]) + "." if strong else "."),
        "%d names were given by at least %d of the %d assistants for the same neighbourhood%s." % (
            len(res["r3"]), ar.ENGINES_REQUIRED_FOR_R3, len(engines),
            " - before checking, so the figure includes second spellings and some entries that are not restaurants" if prelim else ""),
        "The ten most-named account for %s of all mentions: no single restaurant dominates across neighbourhoods." % ar.pct(*res["r4"]),
        "Answers that cite at least one source: " + ", ".join(
            "%s %d of %d" % (ENGINE_NAMES.get(e, e), cite[e], res["by_engine"][e]) for e in engines)
        + ". An answer with no citation shows no sign of a live search.",
    ]
    for b in bullets:
        S.append(Paragraph(safe(b), st["li"], bulletText="-"))
    S.append(PageBreak())

    S.append(Paragraph("Most frequently named, by neighbourhood", st["h"]))
    S.append(Paragraph("Each neighbourhood has %s answers. The interval is a 95%% Wilson interval on the share of those "
                       "answers. This is not an ordering: two names whose intervals overlap are not placed one above the "
                       "other, here or anywhere." % "/".join(str(v) for v in sorted(set(area_n.values()))), st["small"]))
    widths = [1.25 * inch, 2.55 * inch, 0.8 * inch, 0.9 * inch, 0.8 * inch, 0.7 * inch]
    S.append(table([["Neighbourhood", "Name as written by the assistants", "Answers", "95% interval", "Assistants",
                     "Named first"]], widths, st))
    flagged = 0
    for x in areas:                                            # one block per neighbourhood, never split across pages
        block = []
        for i, (k, c) in enumerate(sorted(area_cnt[x].items(), key=lambda kv: (-kv[1], kv[0]))[:4]):
            mark = " *" if res["prose_only"][k] > res["struct_count"][k] else ""
            flagged += bool(mark)
            block.append([x if i == 0 else "", disp[k] + mark, "%d of %d" % (c, area_n[x]), wilson_pct(c, area_n[x]),
                          "%d of %d" % (len(area_eng[x][k]), len(engines)), str(first_cnt[(x, k)])])
        S.append(KeepTogether(table(block, widths, st, header=False)))
    S.append(Spacer(1, 6))
    S.append(Paragraph("* %d of the names above were matched in running text more often than they were written as a list "
                       "entry. Treat them as doubtful until checked: some are neighbourhoods or cuisines, some are the "
                       "short form of a longer name on the same list." % flagged, st["small"]))
    S.append(PageBreak())

    S.append(Paragraph("How the four assistants differ", st["h"]))
    rows_e = [["Assistant", "Answers", "Cite a source", "Names per answer", "Distinct names", "End mid-sentence"]]
    for e in engines:
        ne = res["by_engine"][e]
        rows_e.append([ENGINE_NAMES.get(e, e), str(ne), "%d of %d" % (cite[e], ne), "%.1f" % (names_per[e] / ne),
                       str(len(eng_names[e])), "%d of %d" % (cut[e], ne)])
    S.append(table(rows_e, [1.3 * inch, 0.8 * inch, 1.1 * inch, 1.3 * inch, 1.2 * inch, 1.3 * inch], st))
    S.append(Paragraph("Names are counted only if they occur in at least %d of the %d answers. \"End mid-sentence\" is a "
                       "check on the last character of the answer, a sign it may have been cut off." % (ar.TIER_B_MIN, n), st["small"]))
    S.append(Paragraph("Sites the assistants cite", st["h"]))
    rows_d = [["Assistant", "Most-cited sites (answers citing, of that assistant's answers)"]]
    for e in engines:
        top = sorted(domains[e].items(), key=lambda kv: (-kv[1], kv[0]))[:6]
        rows_d.append([ENGINE_NAMES.get(e, e), ", ".join("%s %d" % (d, c) for d, c in top) or "none"])
    S.append(table(rows_d, [1.3 * inch, 5.7 * inch], st))
    S.append(Paragraph("A cited site is one the assistant returned with its answer. This report does not show that a "
                       "citation is where a given name came from.", st["small"]))
    S.append(PageBreak())

    S.append(Paragraph("Read this before using any name", st["h"]))
    S.append(Paragraph("Name extraction is a heuristic and its error rate has not been measured. Three things are known "
                       "about this list:", st["p"]))
    S.append(Paragraph(safe("%d of the %d names with %d or more answers were matched in running text more often than they "
                            "were written as a list entry. These are the first to distrust: %s." % (
                                len(suspects), sum(1 for k in res["resp_count"] if res["resp_count"][k] >= ar.TIER_A_MIN),
                                ar.TIER_A_MIN, ", ".join(disp[k] for k in suspects) or "none")), st["li"], bulletText="-"))
    S.append(Paragraph(safe("%d pairs of counted names are a short and a long spelling of what may be one place in the same "
                            "neighbourhood (for example %s). Each pair inflates the number of names; the short "
                            "spelling's count already includes answers that used the long one." % (
                                len(pairs), "; ".join("%s / %s" % (disp[s], disp[l]) for s, l in pairs[:3]) or "none")),
                       st["li"], bulletText="-"))
    filled = sum(1 for k, _ in sheet if (verified or {}).get(k))
    S.append(Paragraph(safe("Checking sheet: %d rows (all %d names with %d or more answers, plus %d sampled from the %d "
                            "names with %d to %d). Rows with a verdict: %d of %d." % (
                                len(sheet), n_a, ar.TIER_A_MIN, len(sheet) - n_a, n_b, ar.TIER_B_MIN, ar.TIER_A_MIN - 1,
                                filled, len(sheet))), st["li"], bulletText="-"))
    S.append(Paragraph("Decision rule", st["h"]))
    if prelim:
        S.append(Paragraph("NOT EVALUATED. The rule set before the run needs a verdict on every row of the checking sheet "
                           "(open, closed, not found, wrong area, or not a place). Until then there is no finding about "
                           "whether a stable set of most-named restaurants exists in this market.", st["p"]))
    else:
        verdict, r5 = ar.decision(res, sheet, verified)
        S.append(Paragraph(safe(verdict), st["p"]))
        for line in r5:
            S.append(Paragraph(safe(line), st["small"]))
    preds = predictions(HERE / "PREREG_restaurant_test_v1.md")
    S.append(Paragraph("Predictions written down before the run", st["h"]))
    for line in preds:
        S.append(Paragraph(safe(line), st["li"], bulletText="-"))
    S.append(Paragraph("They are defined on checked names%s." % (", so they cannot be scored yet" if prelim else ""), st["small"]))
    S.append(Paragraph("What this report does not say", st["h"]))
    for b in ["Nothing about how many diners any restaurant gets, or what share of its business comes from AI assistants. "
              "That needs each restaurant's own records.",
              "Nothing about which restaurant is better. A name given often is a name given often.",
              "Nothing about the consumer apps. These answers came from the developer API with a search tool offered; "
              "the apps add their own search, location and memory.",
              "Nothing beyond these %d neighbourhoods, these twenty questions, and this one evening." % len(area_n)]:
        S.append(Paragraph(safe(b), st["li"], bulletText="-"))
    S.append(PageBreak())

    S.append(Paragraph("Check this yourself", st["h"]))
    S.append(Paragraph("Every answer is stored with the request that produced it and a SHA-256 hash of its text. The four "
                       "evidence files sit in the repository beside this report. The checker is one Python file that "
                       "needs nothing installed.", st["p"]))
    rows_v = [["Evidence file", "Clean rows", "Hash match", "Model as returned"]]
    for e in ev:
        rows_v.append([e["file"], "%d of %d" % (e["clean"], e["rows"]), "%d of %d" % (e["hash_match"], e["clean"]), e["model"]])
    S.append(table(rows_v, [3.5 * inch, 0.9 * inch, 0.9 * inch, 1.7 * inch], st))
    S.append(Paragraph("To check a file, run the line for it. The long value is the bundle digest of that file as this "
                       "report computed it.", st["small"]))
    S.append(Spacer(1, 6))
    for e in ev:
        S.append(Paragraph(safe("python verify_evidence.py %s --expect %s" % (e["file"], e["digest"])), st["mono"]))
        S.append(Spacer(1, 3))
    S.append(Spacer(1, 4))
    S.append(Paragraph("A match shows the stored text and the stored hashes agree with each other and with this report. It "
                       "does not show that the answers came from the assistants named, or when: that rests on the "
                       "operator's run record.", st["small"]))
    seal = HERE / "PREREG_SEALED_v1.txt"
    if seal.is_file():
        meta = dict(line[2:].split(" ", 1) for line in seal.read_text(encoding="utf-8").replace("\r", "").splitlines()
                    if line.startswith("# ") and " " in line[2:])
        S.append(Paragraph("Design fixed before the run", st["h"]))
        S.append(Paragraph(safe("The questions, the counting rules, the decision rule and the analysis code were hashed and "
                                "committed before the first answer was collected. Seal time as recorded in the seal file: "
                                "%s UTC; commit %s. First answer collected: %s UTC." % (
                                    meta.get("sealed_at_utc", "?").replace("T", " ").replace("Z", ""),
                                    meta.get("head_commit", "?")[:12], t0[:19].replace("T", " "))), st["p"]))
    S.append(Paragraph(safe("Analysis cross-check: the %d name counts in this report were recomputed from the evidence files "
                            "and equal the committed analysis in %s." % (n_names, Path(a.results).name)), st["small"]))
    if REPLACED:
        chars = " ".join(sorted("U+%04X" % ord(c) for c in REPLACED))
        S.append(Paragraph("%d character(s) outside the report font were reduced to their base letters: %s." % (
            sum(REPLACED.values()), chars), st["small"]))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(0.75 * inch, 0.5 * inch, "aivis restaurant_v1 | %s | %s | run %s" % (
            market, "PRELIMINARY - names not checked" if prelim else "checked names only", run_id[:16]))
        canvas.drawRightString(7.75 * inch, 0.5 * inch, "page %d" % doc.page)
        canvas.restoreState()

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".partial")
    doc = SimpleDocTemplate(str(tmp), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.7 * inch, bottomMargin=0.8 * inch, invariant=1,
                            title="aivis restaurant_v1 %s" % market, author="aivis")
    doc.build(S, onFirstPage=footer, onLaterPages=footer)
    tmp.rename(out)
    print("WROTE %s | %s | answers %d | names in cross-check %d | run id %s | sha256 %s" % (
        out, "PRELIMINARY" if prelim else "VERIFIED", n, n_names, run_id[:16],
        hashlib.sha256(out.read_bytes()).hexdigest()))


def main(argv=None):
    ap = argparse.ArgumentParser(description="restaurant_v1: PDF report for one market")
    ap.add_argument("--runs", nargs="+", required=True, help="the market's run .jsonl files")
    ap.add_argument("--results", required=True, help="the analysis directory those run files produced")
    ap.add_argument("--out", required=True, help="new PDF path (must not exist)")
    ap.add_argument("--verified", help="filled checking sheet, as given to the analyzer")
    ap.add_argument("--merges", help="merge list, as given to the analyzer")
    build(ap.parse_args(argv))


if __name__ == "__main__":
    main()
