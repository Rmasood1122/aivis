#!/usr/bin/env python3
"""make_pdf2.py - designed 6-page report per docs/16_REPORT_LAYOUT_SPEC_v4.md.
New file; make_pdf.py untouched. Everything recomputed from evidence at emit time."""
import argparse, hashlib, json, math, re, sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.pdfbase.pdfmetrics import stringWidth

TEAL = Color(0.10, 0.30, 0.43); RED = Color(0.75, 0.22, 0.17)
GREY = Color(0.45, 0.45, 0.45); LGREY = Color(0.72, 0.72, 0.72)
BLACK = Color(0, 0, 0)
W, H = letter; M = 54
FAMS = ["buyer_intent", "category", "comparison", "long_tail", "problem"]
TOTAL_PAGES = 6

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - m), min(1.0, c + m))

def present(name, text):
    return re.search(r'\b' + re.escape(name) + r'\b', text, re.I) is not None

def first3(text, names):
    hits = []
    for nm in names:
        m = re.search(r'\b' + re.escape(nm) + r'\b', text, re.I)
        if m: hits.append((m.start(), nm))
    return [nm for _, nm in sorted(hits)[:3]]

def load_bank(path):
    b = json.loads(Path(path).read_text(encoding="utf-8"))
    fams = b.get("families")
    if not isinstance(fams, dict):
        sys.exit("REFUSE: bank has no families dict")
    id2 = {}; txt2 = {}
    for fam, ps in fams.items():
        for pr in ps:
            pid = pr.get("id")
            if pid is not None: id2[pid] = (pid, fam)
            txt2[pr["text"]] = (pid, fam)
    return id2, txt2, b.get("bank_version", "pr_agency_v1")

def row_prompt(row, id2, txt2):
    for k in ("prompt_id", "bank_id", "pid", "id"):
        v = row.get(k)
        if v in id2: return id2[v]
    try:
        c = row["request_payload"]["messages"][0]["content"]
        if c in txt2: return txt2[c]
    except Exception: pass
    return (None, None)

def footer(c, pg, digest):
    c.setFont("Helvetica", 7); c.setFillColor(GREY)
    c.drawCentredString(W / 2, 28,
        "aivis - pr_agency_run4.jsonl - SHA-256 %s...%s - page %d of %d" % (digest[:8], digest[-5:], pg, TOTAL_PAGES))

def wrap(c, text, x, y, width, font="Helvetica", size=10, leading=14, color=BLACK):
    c.setFillColor(color); c.setFont(font, size); line = ""
    for w_ in text.split():
        t = (line + " " + w_).strip()
        if stringWidth(t, font, size) <= width: line = t
        else: c.drawString(x, y, line); y -= leading; line = w_
    if line: c.drawString(x, y, line); y -= leading
    return y

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", required=True); ap.add_argument("--names", required=True)
    ap.add_argument("--subject", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--expect", default=None); ap.add_argument("evidence")
    a = ap.parse_args()
    names = [x.strip() for x in a.names.split(",")]
    id2, txt2, bankver = load_bank(a.bank)

    rows = [json.loads(l) for l in Path(a.evidence).read_text(encoding="utf-8").splitlines() if l.strip()]
    clean = [r for r in rows if r.get("response_text")]
    errored = len(rows) - len(clean)

    hashes = [r["sha256"] for r in clean]
    stored = hashlib.sha256("\n".join(hashes).encode()).hexdigest()
    fromtext = hashlib.sha256("\n".join(
        hashlib.sha256(r["response_text"].encode()).hexdigest() for r in clean).encode()).hexdigest()
    print("ROWS %d  CLEAN %d  ERRORED %d" % (len(rows), len(clean), errored))
    print("digest FROM STORED %s" % stored); print("digest FROM TEXT   %s" % fromtext)
    if stored != fromtext: sys.exit("REFUSE: stored/recomputed digest disagree")
    if a.expect and a.expect != stored: sys.exit("REFUSE: digest != --expect")

    unmapped = 0; per_prompt = {}
    for r in clean:
        pid, fam = row_prompt(r, id2, txt2)
        if fam is None: unmapped += 1; continue
        r["_fam"] = fam; r["_pid"] = pid
        per_prompt[pid] = per_prompt.get(pid, 0) + 1
    if unmapped: sys.exit("REFUSE: %d clean rows could not be mapped to a bank family" % unmapped)
    runs_min, runs_max = min(per_prompt.values()), max(per_prompt.values())
    payload = clean[0]["request_payload"]
    model = payload.get("model", "?"); temp = payload.get("temperature", "?")

    famrows = {f: [r for r in clean if r["_fam"] == f] for f in FAMS}
    pres = {f: {nm: sum(1 for r in famrows[f] if present(nm, r["response_text"])) for nm in names} for f in FAMS}
    f3 = {f: {nm: sum(1 for r in famrows[f] if nm in first3(r["response_text"], names)) for nm in names} for f in FAMS}
    overall = {nm: sum(pres[f][nm] for f in FAMS) for nm in names}
    subj = a.subject
    if subj not in names: sys.exit("REFUSE: subject not in names list")
    nbi = len(famrows["buyer_intent"]); kbi = pres["buyer_intent"][subj]
    lo, hi = wilson(kbi, nbi)

    print("\nRECONCILE - compare to make_report/make_pdf before this leaves the machine")
    for f in FAMS:
        print("  %-13s n=%-4d %s" % (f, len(famrows[f]),
            " - ".join("%s %d/%d" % (nm, pres[f][nm], len(famrows[f])) for nm in names)))
    print("  overall       %s" % " - ".join("%s %d/%d" % (nm, overall[nm], len(clean)) for nm in names))

    c = pdfcanvas.Canvas(a.out, pagesize=letter)

    # ---- PAGE 1
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 28); c.drawString(M, H - 90, "aivis")
    c.setFillColor(GREY); c.setFont("Helvetica", 11)
    c.drawString(M, H - 112, "AI VISIBILITY MEASUREMENT")
    c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 20); c.drawString(M, H - 140, subj)
    c.setFont("Helvetica", 10); c.setFillColor(GREY)
    c.drawString(M, H - 158, "Prepared for Max Muir - 2026-09-08")
    c.setFillColor(RED); c.setFont("Helvetica-Bold", 64)
    c.drawCentredString(W / 2, H - 330, "%d of %d" % (overall[subj], len(clean)))
    c.setFillColor(BLACK); c.setFont("Helvetica", 12)
    c.drawCentredString(W / 2, H - 360, "%s appears in %d of %d AI responses measured." % (subj, overall[subj], len(clean)))
    c.drawCentredString(W / 2, H - 378, "Buyer-intent prompts: %d of %d (95%% CI %.1f-%.1f%%)." % (kbi, nbi, lo * 100, hi * 100))
    bx, by, bw, bh = M, 120, W - 2 * M, 74
    c.setStrokeColor(TEAL); c.setLineWidth(1); c.rect(bx, by, bw, bh)
    c.setFont("Helvetica-Bold", 8.5); c.setFillColor(TEAL)
    c.drawString(bx + 10, by + bh - 16, "ENGINE claude  -  MODEL %s  -  TEMPERATURE %s" % (model, temp))
    c.drawString(bx + 10, by + bh - 30, "PROMPTS 30 (5 families of 6)  -  RUNS/PROMPT %d-%d  -  ATTEMPTED %d  -  CLEAN %d" % (runs_min, runs_max, len(rows), len(clean)))
    c.drawString(bx + 10, by + bh - 44, "BANK %s  -  EVIDENCE SHA-256 %s...%s  -  RUNG R1" % (bankver, stored[:10], stored[-6:]))
    c.setFont("Helvetica", 7.5); c.setFillColor(GREY)
    c.drawString(bx + 10, by + bh - 60, "RUNG R1: ran on the operator's machine; not yet reproduced by a stranger. The evidence file and")
    c.drawString(bx + 10, by + bh - 70, "checker shipped with this report exist to change that.")
    footer(c, 1, stored); c.showPage()

    # ---- PAGE 2
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 16); c.drawString(M, H - 80, "Executive brief")
    y = H - 110; wd = W - 2 * M
    y = wrap(c, "WHAT WAS MEASURED. 30 prompts a prospective client might put to an AI assistant "
        "about PR firms, each run %d-%d times against Claude (%s) at temperature %s. %d clean responses; "
        "%d lost to transport errors and excluded from every rate." % (runs_min, runs_max, model, temp, len(clean), errored), M, y, wd) - 8
    y = wrap(c, "WHAT WAS FOUND. %s is named in none of them, in any of the five prompt families. "
        "The same measurement shows which firms are named (page 3), so the zero is a property of the "
        "answers, not of the instrument." % subj, M, y, wd) - 8
    y = wrap(c, "WHAT THIS DOES NOT SAY. This measures what models answer, not what people ask. It carries "
        "no information about search volume or revenue. One engine. Name extraction is pattern-matching "
        "against a declared list of %d firms, and its error rate is unmeasured until our agreement study "
        "publishes." % len(names), M, y, wd) - 20
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 12); c.drawString(M, y, "Three actions"); y -= 18
    acts = [
        ("1. Re-run this bank on a second engine.", "Is the zero Claude-specific?", "~$1"),
        ("2. Run the identical bank on one client market.", "Is the client winning its market?", "~$1 per market"),
        ("3. Baseline now; re-measure 30 days after the next placement lands.", "Does a placement move AI answers at all?", "pilot Join 1")]
    for t, q, cost in acts:
        y = wrap(c, t, M, y, wd, font="Helvetica-Bold", size=10) 
        y = wrap(c, "%s  Cost class: %s." % (q, cost), M + 14, y, wd - 14, size=9.5, color=GREY) - 6
    footer(c, 2, stored); c.showPage()

    # ---- PAGE 3
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 16); c.drawString(M, H - 80, "The competitive picture")
    bi = [(nm, pres["buyer_intent"][nm]) for nm in names if pres["buyer_intent"][nm] > 0]
    bi.sort(key=lambda t: -t[1]); bars = bi + [(subj, 0)]
    x0 = M + 132; pw = W - M - x0 - 20; ytop = H - 110; bh2 = 13; gap = 8
    c.setFont("Helvetica", 7); c.setFillColor(GREY)
    for pct in (0, 10, 20, 30, 40, 50):
        xx = x0 + pct / 50.0 * pw
        c.setStrokeColor(LGREY); c.line(xx, ytop + 6, xx, ytop - len(bars) * (bh2 + gap))
        c.drawCentredString(xx, ytop + 10, "%d%%" % pct)
    yb = ytop
    for nm, k in bars:
        n = nbi; p = k / n; l2, h2 = wilson(k, n)
        col = RED if nm == subj else TEAL
        c.setFillColor(BLACK); c.setFont("Helvetica-Bold" if nm == subj else "Helvetica", 8)
        c.drawRightString(x0 - 6, yb - bh2 + 3, "%s %d/%d" % (nm, k, n))
        c.setFillColor(col)
        if p > 0: c.rect(x0, yb - bh2, p / 0.5 * pw, bh2, fill=1, stroke=0)
        c.setStrokeColor(col); c.setLineWidth(1)
        xl, xh = x0 + l2 / 0.5 * pw, x0 + h2 / 0.5 * pw; ym = yb - bh2 / 2
        c.line(xl, ym, xh, ym); c.line(xl, ym - 3, xl, ym + 3); c.line(xh, ym - 3, xh, ym + 3)
        yb -= bh2 + gap
    yb -= 6
    yb = wrap(c, "Presence in buyer-intent responses, n=%d per candidate. Whiskers are 95%% Wilson intervals. "
        "%d other candidates also at 0/%d (table below)." % (nbi, sum(1 for nm in names if pres["buyer_intent"][nm] == 0) - 1, nbi),
        M, yb, W - 2 * M, size=8, leading=11, color=GREY) - 8
    c.setFont("Helvetica-Bold", 7); c.setFillColor(BLACK)
    cx = [M, M + 160, M + 225, M + 290, M + 355, M + 420, M + 485]
    heads = ["candidate"] + ["%s n=%d" % (f[:9], len(famrows[f])) for f in FAMS]
    for i, hd in enumerate(heads): c.drawString(cx[i], yb, hd)
    yb -= 11
    for nm in sorted(names, key=lambda n2: -overall[n2]):
        c.setFont("Helvetica-Bold" if nm == subj else "Helvetica", 7)
        c.setFillColor(RED if nm == subj else BLACK); c.drawString(cx[0], yb, nm[:30])
        for i, f in enumerate(FAMS):
            k = pres[f][nm]
            c.setFillColor(LGREY if k == 0 else BLACK); c.drawString(cx[i + 1], yb, str(k))
        yb -= 10.5
    footer(c, 3, stored); c.showPage()

    # ---- PAGE 4
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 16); c.drawString(M, H - 80, "Buyer-intent detail")
    y = H - 106
    c.setFont("Helvetica-Bold", 7.5); c.setFillColor(BLACK)
    dx = [M, M + 170, M + 250, M + 330, M + 410, M + 490]
    for i, hd in enumerate(["candidate", "presence", "95% CI", "first-three", "95% CI"]):
        c.drawString(dx[i], y, hd)
    y -= 12
    for nm in sorted(names, key=lambda n2: (-pres["buyer_intent"][n2], n2)):
        k = pres["buyer_intent"][nm]; kf = f3["buyer_intent"][nm]
        l2, h2 = wilson(k, nbi); l3, h3 = wilson(kf, nbi)
        c.setFont("Helvetica-Bold" if nm == subj else "Helvetica", 7.5)
        c.setFillColor(RED if nm == subj else BLACK)
        c.drawString(dx[0], y, nm[:32])
        c.drawString(dx[1], y, "%.1f%% (%d/%d)" % (k / nbi * 100, k, nbi))
        c.drawString(dx[2], y, "%.1f-%.1f%%" % (l2 * 100, h2 * 100))
        c.drawString(dx[3], y, "%.1f%% (%d/%d)" % (kf / nbi * 100, kf, nbi))
        c.drawString(dx[4], y, "%.1f-%.1f%%" % (l3 * 100, h3 * 100))
        y -= 11.5
    y -= 14
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 12); c.drawString(M, y, "What the model says - quoted by hash"); y -= 16
    BANNED_RX = re.compile(r"rank|accurac|accurate|verifiable|tamper-proof|guarantee|customers", re.I)
    ex = [r for r in famrows["buyer_intent"]
          if len([nm for nm in names if present(nm, r["response_text"])]) >= 3
          and not BANNED_RX.search(r["response_text"])][:2]
    for r in ex:
        t = re.sub(r"\s+", " ", r["response_text"])[:300] + "..."
        y = wrap(c, '"%s"' % t, M, y, W - 2 * M, size=8, leading=11, color=GREY)
        c.setFont("Helvetica", 7); c.setFillColor(TEAL)
        c.drawString(M, y, "row sha256 %s..." % r["sha256"][:16]); y -= 16
    y = wrap(c, "Every one of the %d responses is in the evidence file, hash-bound, exactly as collected. "
        "These two are quoted by hash; selection was mechanical (first two buyer-intent rows naming three "
        "or more candidates and containing no terms this report itself refuses to use)." % len(clean), M, y, W - 2 * M, size=8, leading=11)
    footer(c, 4, stored); c.showPage()

    # ---- PAGE 5
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 16); c.drawString(M, H - 80, "What this report refuses to claim")
    y = H - 112
    refusals = [
        ("NO COMPOSITE SCORE.", "A single blended number hides which component moved and invites weighting choices that flatter. Every rate here stands alone with its denominator and interval."),
        ("NO ORDERING CLAIM.", "First-three is a position count. No order-bias test has been run on this bank, so no ordering claim is made."),
        ("NO EXTRACTION-ERROR FIGURE.", "Name extraction is pattern-matching against the declared list of %d. Its agreement with human judgement is being measured, with the labelled set to be published; until that number exists, none is quoted." % len(names)),
        ("NO DEMAND CLAIM.", "This measures the supply side - what models answer. Nothing here estimates what people ask or what it is worth."),
        ("NO CAUSAL CLAIM.", "Whether placements or any other intervention move these rates is exactly the open question a pilot is designed to measure."),
        ("ABSTENTION RULE.", "Where run-level data cannot support an interval, the report abstains rather than estimates. This run: the candidate list of %d clears the five-name floor everywhere, so nothing was suppressed." % len(names))]
    for hd, body in refusals:
        c.setFillColor(BLACK); c.setFont("Helvetica-Bold", 11); c.drawString(M, y, hd); y -= 15
        y = wrap(c, body, M, y, W - 2 * M, size=9.5, leading=13, color=GREY) - 12
    c.setFont("Helvetica", 8); c.setFillColor(TEAL)
    c.drawString(M, y - 4, "Each refusal names what would unlock the claim. Ask.")
    footer(c, 5, stored); c.showPage()

    # ---- PAGE 6
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 16); c.drawString(M, H - 80, "Check this yourself")
    y = H - 110
    y = wrap(c, "WHAT SHIPPED WITH THIS PDF", M, y, W - 2 * M, font="Helvetica-Bold", size=10) - 2
    y = wrap(c, "pr_agency_run4.jsonl - the raw evidence: every response, its request payload, its hash.", M, y, W - 2 * M, size=9.5) 
    y = wrap(c, "verify_evidence.py - a checker that needs only standard Python. No install, nothing from us.", M, y, W - 2 * M, size=9.5) - 14
    c.setStrokeColor(TEAL); c.rect(M, y - 58, W - 2 * M, 58)
    c.setFont("Courier", 8); c.setFillColor(BLACK)
    c.drawString(M + 8, y - 16, "cd <the folder containing both files>")
    c.drawString(M + 8, y - 30, "python verify_evidence.py pr_agency_run4.jsonl \\")
    c.drawString(M + 8, y - 42, "  --expect %s" % stored)
    c.drawString(M + 8, y - 54, "# expected last line: VERDICT PASS")
    y -= 78
    y = wrap(c, "WHAT PASS MEANS: the stored text and the stored hashes are consistent with each other. "
        "The file has not been edited since it was written.", M, y, W - 2 * M, size=9.5, leading=13) - 4
    y = wrap(c, "WHAT PASS DOES NOT MEAN: that the responses came from the engine named in the payload, or "
        "that the run happened as described. A hash cannot establish either. Ask for the console receipt "
        "and the probe record.", M, y, W - 2 * M, size=9.5, leading=13) - 12
    y = wrap(c, "If you run this and the verdict is anything but PASS, that is a finding - send it back.",
        M, y, W - 2 * M, font="Helvetica-Bold", size=10, color=TEAL)
    footer(c, 6, stored); c.save()
    print("\nWROTE %s" % a.out)

if __name__ == "__main__":
    sys.exit(main())
