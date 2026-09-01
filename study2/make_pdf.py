#!/usr/bin/env python3
"""make_pdf.py — aivis PDF report, computed entirely from the evidence file.

NO number in the output is typed into this script. Rates, counts, intervals,
denominators, the digest, model ids, temperature: all read or computed from
the evidence JSONL and the bank at emit time. If the recomputed bundle digest
does not match --expect (when given), NOTHING is written.

Usage:
  python make_pdf.py EVIDENCE.jsonl --bank BANK.json \
      --names "Firm A,Firm B,..." --subject "Firm A" \
      --out report.pdf [--expect DIGEST]

Deps: reportlab (pip install reportlab). Everything else stdlib.
Matching rule mirrors study2/make_report.py: \\b re.escape(name) \\b, case-
insensitive, on response_text. If make_report.py's rule ever changes, change
this one the same session or the two emitters will disagree — and a
disagreement between them is a finding, not a formatting bug.
"""
import argparse, hashlib, json, math, pathlib, re, sys
from datetime import datetime, timezone

Z = 1.959963985

def wilson(k, n):
    if n == 0: return (float("nan"), 0.0, 1.0)
    p = k / n; d = 1 + Z*Z/n
    c = (p + Z*Z/(2*n)) / d
    h = (Z/d) * math.sqrt(p*(1-p)/n + Z*Z/(4*n*n))
    return p, max(0.0, c-h), min(1.0, c+h)

def sha(t): return hashlib.sha256(t.encode("utf-8")).hexdigest()

def load_rows(path):
    rows = []
    for ln in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        if ln.strip(): rows.append(json.loads(ln))
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("evidence")
    ap.add_argument("--bank", required=True)
    ap.add_argument("--names", required=True, help="comma-separated candidate list")
    ap.add_argument("--subject", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect", default=None, help="bundle digest; mismatch = refuse")
    a = ap.parse_args()

    names = [x.strip() for x in a.names.split(",") if x.strip()]
    if len(names) < 5:
        sys.exit("REFUSE: fewer than 5 candidates — first-N and low-rate columns "
                 "collapse below this floor (defect D1). Add candidates or use "
                 "the markdown reporter in discovery mode.")

    rows = load_rows(a.evidence)
    clean = [r for r in rows if r.get("response_text")]
    errored = len(rows) - len(clean)

    # ---- integrity gate: recompute BOTH digests before trusting anything
    stored = [r.get("sha256", "") for r in clean]
    from_stored = sha("\n".join(stored))
    from_text = sha("\n".join(sha(r["response_text"]) for r in clean))
    mism = sum(1 for r in clean if sha(r["response_text"]) != r.get("sha256"))
    print(f"ROWS {len(rows)}  CLEAN {len(clean)}  ERRORED {errored}")
    print(f"hash identity {len(clean)-mism} of {len(clean)} clean rows")
    print(f"digest FROM STORED {from_stored}")
    print(f"digest FROM TEXT   {from_text}")
    if mism or from_stored != from_text:
        sys.exit("REFUSE: stored hashes do not describe the stored text. No PDF.")
    if a.expect and from_stored != a.expect:
        sys.exit(f"REFUSE: digest != --expect {a.expect}. No PDF.")

    # ---- family mapping via prompt TEXT (immune to the duplicate-id defect)
    bank = json.loads(pathlib.Path(a.bank).read_text(encoding="utf-8"))
    t2f = {p["text"]: fam for fam, ps in bank["families"].items() for p in ps}
    bank_name = bank.get("bank_version") or bank.get("name") or pathlib.Path(a.bank).stem
    fams = sorted(set(t2f.values()))

    unmapped = 0
    for r in clean:
        txt = r.get("request_payload", {}).get("messages", [{}])[0].get("content", "")
        r["_fam"] = t2f.get(txt)
        if r["_fam"] is None: unmapped += 1
    if unmapped:
        sys.exit(f"REFUSE: {unmapped} clean rows have prompts not in this bank. "
                 "Wrong bank file, or bank edited since the run. No PDF.")

    # ---- surface, read from the rows themselves, must be uniform
    models = sorted({r["request_payload"].get("model", "?") for r in clean})
    temps  = sorted({str(r["request_payload"].get("temperature", "?")) for r in clean})

    # ---- per-family, per-candidate mention counts (make_report.py's rule)
    pats = {nm: re.compile(r"\b" + re.escape(nm) + r"\b", re.I) for nm in names}
    per_fam_n = {f: 0 for f in fams}
    counts = {f: {nm: 0 for nm in names} for f in fams}
    overall = {nm: 0 for nm in names}
    for r in clean:
        f = r["_fam"]; per_fam_n[f] += 1
        for nm, pat in pats.items():
            if pat.search(r["response_text"]):
                counts[f][nm] += 1; overall[nm] += 1

    # ---- runs-per-prompt spread (from prompt text occurrences)
    from collections import Counter
    runs_per = Counter()
    for r in clean:
        runs_per[r["request_payload"]["messages"][0]["content"]] += 1
    spread = sorted(set(runs_per.values()))

    # ---- reconciliation print BEFORE any PDF exists
    print("\nRECONCILE — compare these to the markdown reporter before trusting the PDF")
    for f in fams:
        n = per_fam_n[f]
        line = " · ".join(f"{nm} {counts[f][nm]}/{n}" for nm in names)
        print(f"  {f:<13} n={n:<4} {line}")
    print("  overall       " + " · ".join(
        f"{nm} {overall[nm]}/{len(clean)}" for nm in names))

    # ---- build the PDF
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.lib.colors import HexColor, white
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate,
                                        Paragraph, Spacer, Table, TableStyle,
                                        PageBreak)
    except ImportError:
        sys.exit("reportlab missing: pip install reportlab")

    NAVY = HexColor("#122A3F"); RED = HexColor("#B3402A"); GREY = HexColor("#5A6672")
    LIGHT = HexColor("#F2F5F7"); RULE = HexColor("#C9D3DA")
    ss = getSampleStyleSheet()
    def st(nm, **kw):
        b = kw.pop("base", "Normal"); return ParagraphStyle(nm, parent=ss[b], **kw)
    H1 = st("H1", base="Title", fontName="Helvetica-Bold", fontSize=20, leading=24,
            textColor=NAVY, alignment=0, spaceAfter=2)
    SUB = st("SUB", fontSize=10.5, leading=14, textColor=GREY)
    H2 = st("H2", fontName="Helvetica-Bold", fontSize=12.5, leading=16,
            textColor=NAVY, spaceBefore=13, spaceAfter=5)
    BODY = st("BODY", fontSize=9.6, leading=13.4)
    SMALL = st("SMALL", fontSize=8.2, leading=11, textColor=GREY)
    CELL = st("CELL", fontSize=9.2, leading=12)
    CELLB = st("CELLB", fontName="Helvetica-Bold", fontSize=9.2, leading=12)
    MONO = st("MONO", fontName="Courier", fontSize=7.6, leading=10, textColor=GREY)
    FIND = st("FIND", fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=white)
    FINDS = st("FINDS", fontSize=9.4, leading=13, textColor=HexColor("#E8EEF2"))

    def footer(canv, doc):
        canv.saveState(); canv.setStrokeColor(RULE); canv.setLineWidth(0.5)
        canv.line(0.75*inch, 0.62*inch, letter[0]-0.75*inch, 0.62*inch)
        canv.setFont("Helvetica", 7); canv.setFillColor(GREY)
        canv.drawString(0.75*inch, 0.46*inch,
            f"aivis · bank {bank_name} · {pathlib.Path(a.evidence).name} · RUNG R1")
        canv.drawRightString(letter[0]-0.75*inch, 0.46*inch,
            f"bundle digest {from_stored[:16]}...  ·  page {doc.page}")
        canv.restoreState()

    doc = BaseDocTemplate(a.out, pagesize=letter, leftMargin=0.75*inch,
                          rightMargin=0.75*inch, topMargin=0.7*inch,
                          bottomMargin=0.85*inch,
                          title=f"AI Visibility Measurement - {a.subject}",
                          author="aivis")
    fr = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="p", frames=[fr], onPage=footer)])
    E = []

    face = Table([
        [Paragraph("<b>ENGINE</b>", SMALL), Paragraph(", ".join(models), SMALL)],
        [Paragraph("<b>TEMPERATURE</b>", SMALL), Paragraph(", ".join(temps), SMALL)],
        [Paragraph("<b>PROMPTS</b>", SMALL),
         Paragraph(f"{len(runs_per)} · {len(fams)} families", SMALL)],
        [Paragraph("<b>RUNS / PROMPT</b>", SMALL),
         Paragraph("-".join(str(x) for x in (spread[:1]+spread[-1:])) if len(spread) > 1
                   else str(spread[0]), SMALL)],
        [Paragraph("<b>CLEAN</b>", SMALL),
         Paragraph(f"{len(clean)} of {len(rows)} attempted", SMALL)],
        [Paragraph("<b>RUNG</b>", SMALL),
         Paragraph("R1 - ran on the operator's machine", SMALL)],
    ], colWidths=[1.05*inch, 2.05*inch])
    face.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),LIGHT),("BOX",(0,0),(-1,-1),0.75,RULE),
        ("INNERGRID",(0,0),(-1,-1),0.25,RULE),("TOPPADDING",(0,0),(-1,-1),3),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),("LEFTPADDING",(0,0),(-1,-1),6)]))
    gen = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    head = Table([[[Paragraph("AI VISIBILITY MEASUREMENT", H1),
        Paragraph(f"Subject: <b>{a.subject}</b> · generated {gen} · make_pdf v0.1", SUB),
        Spacer(1,4),
        Paragraph("This measures what AI assistants <b>answer</b>, not what people ask. "
                  "It carries no information about search volume or purchase intent. "
                  "Every figure is computed from the named evidence file at generation "
                  "time; this document contains no typed numbers and no placeholders.",
                  BODY)], face]], colWidths=[3.85*inch, 3.25*inch])
    head.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP")]))
    E += [head, Spacer(1,14)]

    subj_total = overall.get(a.subject, 0)
    _, lo, hi = wilson(subj_total, len(clean))
    fb = Table([[Paragraph(
        f"{a.subject} appears in {subj_total} of {len(clean)} responses.", FIND)],
        [Paragraph(
        f"95% Wilson interval on the overall rate: {lo*100:.1f}% - {hi*100:.1f}%. "
        "STATUS = COMPLETE for this evidence file. Per-family tables below print "
        "each rate against its own denominator; the bound travels with every zero "
        "so no claim can outrun the data.", FINDS)]], colWidths=[7.1*inch])
    fb.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),NAVY),
        ("TOPPADDING",(0,0),(0,0),10),("BOTTOMPADDING",(0,1),(0,1),10),
        ("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12)]))
    E += [fb, Spacer(1,10)]

    for f in fams:
        n = per_fam_n[f]
        ordered = sorted(names, key=lambda nm: -counts[f][nm])
        data = [[Paragraph(f"<b>{f.upper()} - n = {n} responses</b>", CELLB),
                 Paragraph("<b>Mention rate</b>", CELLB),
                 Paragraph("<b>95% CI</b>", CELLB)]]
        sty = [("BACKGROUND",(0,0),(-1,0),LIGHT),("BOX",(0,0),(-1,-1),0.75,RULE),
               ("LINEBELOW",(0,0),(-1,0),0.75,RULE),
               ("ROWBACKGROUNDS",(0,1),(-1,-1),[white,HexColor("#FAFBFC")]),
               ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
               ("LEFTPADDING",(0,0),(-1,-1),8)]
        for i, nm in enumerate(ordered, 1):
            k = counts[f][nm]; p, l, h = wilson(k, n)
            s = CELLB if nm == a.subject else CELL
            data.append([Paragraph(nm, s),
                         Paragraph(f"{p*100:.1f}%  ({k}/{n})", s),
                         Paragraph(f"{l*100:.1f}% - {h*100:.1f}%", s)])
            if nm == a.subject:
                sty += [("BACKGROUND",(0,i),(-1,i),HexColor("#FBEDE9")),
                        ("TEXTCOLOR",(0,i),(-1,i),RED)]
        t = Table(data, colWidths=[3.4*inch,1.9*inch,1.8*inch])
        t.setStyle(TableStyle(sty))
        E += [t, Spacer(1,8)]
    E.append(Paragraph(
        f"Candidate list declared: {', '.join(names)}. Nothing was scored off-list; "
        "entities outside this list are not measured by this document.", SMALL))
    E.append(PageBreak())

    E.append(Paragraph("INSTRUMENT RECORD", H2))
    inst = [("Evidence file", f"{pathlib.Path(a.evidence).name} - one row per response: "
             "raw text, request payload, SHA-256"),
            ("Prompt bank", f"{bank_name} · {len(runs_per)} prompts · families: "
             + ", ".join(fams)),
            ("Responses per family", " · ".join(str(per_fam_n[f]) for f in fams)
             + " - every rate prints against its own count"),
            ("Rows attempted / clean / lost",
             f"{len(rows)} / {len(clean)} / {errored} (transport errors)"),
            ("Runs per prompt", ", ".join(str(x) for x in spread)
             + (" - uneven; per-family tables are the primary view" if len(spread)>1 else "")),
            ("Surface declared", f"developer API · model {', '.join(models)} · "
             f"temperature {', '.join(temps)}. Not the consumer app surface; "
             "the gap is a stated limit, not pooled away."),
            ("Interval method", "Wilson score, 95%, computed per rate at its own n"),
            ("Bundle digest (SHA-256)", from_stored)]
    t = Table([[Paragraph(f"<b>{k}</b>", CELL), Paragraph(v, CELL)] for k,v in inst],
              colWidths=[2.0*inch, 5.1*inch])
    t.setStyle(TableStyle([("BOX",(0,0),(-1,-1),0.75,RULE),
        ("INNERGRID",(0,0),(-1,-1),0.25,RULE),("BACKGROUND",(0,0),(0,-1),LIGHT),
        ("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),8)]))
    E.append(t)

    E.append(Paragraph("LIMITS - printed here, not discovered later", H2))
    for x in [
        f"One engine per model listed above ({', '.join(models)}). No claim is made "
        "about other engines or any consumer surface; adding them changes these numbers.",
        "Extraction error is unmeasured. Names are matched by a text rule with no "
        "published agreement coefficient yet. Every count depends on that unvalidated "
        "step; its measurement (an inter-labeller study on a sealed sample) is a "
        "prerequisite for any stronger language.",
        "One point in time. Models update; these rates decay. This file re-quoted "
        "next quarter without a re-run is a misquote.",
        "No link to revenue is claimed. Whether AI mention rates move sales is the "
        "open question this instrument is built to test - not one it has answered."]:
        E += [Paragraph("- " + x, BODY), Spacer(1,4)]

    E.append(Paragraph("CHECK THIS YOURSELF", H2))
    E.append(Paragraph(
        "The evidence file ships with this report. The checker is public, standard "
        "library only, installs nothing:", BODY))
    E += [Spacer(1,5),
          Paragraph("git clone https://github.com/Rmasood1122/aivis-method.git", MONO),
          Paragraph(f"python3 aivis-method/verify_evidence.py "
                    f"{pathlib.Path(a.evidence).name} \\", MONO),
          Paragraph(f"        --expect {from_stored}", MONO), Spacer(1,6),
          Paragraph("A PASS means the file was not altered after it was written - the "
                    "record is tamper-evident and hash-verified. It does not mean "
                    "collection was honest, or that these responses are what a consumer "
                    "would see today. A hash cannot establish either, and this report "
                    "says so rather than implying otherwise.", BODY)]
    doc.build(E)
    print(f"\nWROTE {a.out}")
    print("Reconcile the table above against the markdown reporter before this "
          "leaves the machine.")

if __name__ == "__main__":
    main()
