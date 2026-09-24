#!/usr/bin/env python3
"""build_agent_package.py - one agent's complete, reviewable data package from the v1 run.

    pip install openpyxl
    python realtor_v1/build_agent_package.py "Maureen Folan" realtor_v1/runs/multi_*_realtor_v1_20260923.jsonl

Writes realtor_v1/packages/<Agent_Name>_AI_visibility_2026-09-23.xlsx with tabs:
  Summary · Questions · Your Mentions · Gaps · Method
Other agents' names are redacted to [Agent] (PREREG publication rule: each agent sees only their own
results). Every row carries the SHA-256 of the ORIGINAL unedited response; redacted text will not
hash to it - the originals stay in the evidence files and can be shown unredacted on request.
"""
import csv, glob, json, re, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
except ImportError:
    sys.exit("openpyxl missing: run  pip install openpyxl")

if len(sys.argv) < 3:
    sys.exit(__doc__)
target, files = sys.argv[1], sys.argv[2:]
tpat = re.compile(re.escape(target), re.I)
ET = timezone(timedelta(hours=-4))

# ---- names to redact: every candidate + verified name except the target
names = set()
for p in ("realtor_v1/results_v1c/person_candidates.csv", "realtor_v1/verify_sheet_v1_filled.csv"):
    if Path(p).exists():
        for r in csv.DictReader(open(p, encoding="utf-8")):
            n = (r.get("name") or "").strip()
            if n and " " in n and n.lower() != target.lower() and n.lower() not in target.lower():
                names.add(n)
names = sorted(names, key=len, reverse=True)
red_pat = re.compile("|".join(re.escape(n) for n in names), re.I) if names else None
red_tokens = {w.lower() for n in names for w in n.split() if len(w) > 3}
tgt_tokens = {w.lower() for w in target.split()}

# Words that are firms/places/generic, never redacted on their own
KEEP = set("""Keller Williams Realty Real Estate Group Team Home Homes Queens Long Island New York Douglas Elliman
Compass Corcoran Coldwell Banker Century Exit Realty Signature Premier Coach Daniel Gale Sotheby Sotheby's
International Brown Harris Stevens Howard Hanna Berkshire Hathaway Serhant SERHANT Redfin Zillow Landmark
Square American Broker Real Luxury Top Best Agent Agents Local Metro North South East West Flushing Bayside
Whitestone Ridgewood Astoria Sunnyside Forest Hills Jackson Heights Manhasset Syosset Smithtown Garden City
Great Neck Port Washington Rockville Centre Massapequa Huntington Long Beach Northeast The Associates Partners
Properties Property Brokerage Winzone Werba Trademarko Nest Seekers Modern Spaces Laffey Weichert Halstead
Rutenberg Charles Integrity Leaders Island Advisors Estates Choice Premier Village Bay Terrace Downtown
""".split())
surnames = {n.split()[-1] for n in names if len(n.split()[-1]) > 2} - KEEP - tgt_tokens - {w.title() for w in tgt_tokens}
sur_pat = re.compile(r"\b(" + "|".join(re.escape(s) for s in sorted(surnames, key=len, reverse=True)) + r")\b") if surnames else None
team_pat = re.compile(r"\b(?:(The\s+)?([A-Z][a-z]+)\s+(Team|Group)|Team\s+([A-Z][a-z]+))\b")

def _team(m):
    w = m.group(2) or m.group(4)
    if w in KEEP or w.lower() in tgt_tokens: return m.group(0)
    return "[Agent] " + (m.group(3) or "Team")

def redact(t):
    if red_pat: t = red_pat.sub("[Agent]", t)
    t = re.sub(r"\[Agent\](?:\s(?!Team\b|Group\b|Real\b|Realty\b)[A-Z][a-z]+)+", "[Agent]", t)  # leftover 3rd name parts
    t = team_pat.sub(_team, t)                                                                  # "The Braswell Team", "Team Barone"
    if sur_pat: t = sur_pat.sub("[Agent]", t)                                                   # standalone surnames
    t = re.sub(r"Cooper\s*&\s*Cooper", "[Agent]", t)
    return t

def cite_view(c):
    u = c.get("url", "") if isinstance(c, dict) else str(c)
    t = (c.get("title") or "") if isinstance(c, dict) else ""
    host = urlparse(u).netloc.lower().removeprefix("www.")
    if "vertexaisearch" in host and t and " " not in t and "." in t:
        return t, t                                     # Gemini redirect: title is the real domain
    low = (unquote(u) + " " + t).lower()
    squashed = low.replace(" ", "").replace("-", "").replace("_", "")
    mine = all(w in low for w in tgt_tokens) or target.lower().replace(" ", "") in squashed
    other = any(n.lower() in low or n.lower().replace(" ", "") in squashed for n in names)
    profile = re.search(r"/(profile|agents?|advisor|realestateagents?|real-estate-agents|agent-profile)/", u.lower())
    if not mine and (other or profile):
        return host, host                                  # someone else's profile -> site name only
    return host, u.split("?utm_source")[0]

prompts = {}
for l in open("realtor_v1/queens_li_prompts_v1.jsonl", encoding="utf-8"):
    if l.strip():
        r = json.loads(l); prompts[r["prompt_id"]] = r

rows = []
for f in files:
    for l in open(f, encoding="utf-8"):
        if not l.strip(): continue
        r = json.loads(l)
        if not r.get("response_text"): continue
        rows.append(r)

def ts_et(r):
    try: return datetime.fromisoformat(r["ts"]).astimezone(ET)
    except Exception: return None

mine = [r for r in rows if tpat.search(r["response_text"])]
market = sorted({r["prompt_id"] for r in mine})
gaps = [r for r in rows if r["prompt_id"] in market and not tpat.search(r["response_text"])]
engines = sorted({r["engine"] for r in rows})
times = [t for t in (ts_et(r) for r in rows) if t]
t0, t1 = min(times), max(times)

wb = Workbook()
H = Font(bold=True, color="FFFFFF"); HF = PatternFill("solid", fgColor="1F3A5F"); WR = Alignment(wrap_text=True, vertical="top")

def sheet(ws, header, data, widths):
    ws.append(header)
    for c in ws[1]: c.font = H; c.fill = HF; c.alignment = WR
    for d in data: ws.append(d)
    for i, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment = WR
    ws.freeze_panes = "A2"

# Summary
ws = wb.active; ws.title = "Summary"
per_eng = Counter(r["engine"] for r in mine); n_eng = Counter(r["engine"] for r in rows)
grid = defaultdict(set)
for r in mine: grid[(r["prompt_id"], r["engine"])].add(r.get("rep"))
summ = [
    ["Agent", target],
    ["Test date", t0.strftime("%B %d, %Y")],
    ["Test window (Eastern Time)", f"{t0:%I:%M %p} – {t1:%I:%M %p} ET"],
    ["Engines", ", ".join(engines) + " (all with live web search enabled)"],
    ["Design", f"{len(prompts)} questions × {len(engines)} engines × 5 repetitions = {len(rows)} answers"],
    ["Answers naming you or your group", f"{len(mine)} of {len(rows)}"],
    ["Engines that named you", f"{sum(1 for e in engines if per_eng[e])} of {len(engines)}"],
    [], ["Per engine", "Named you / answers"],
] + [[e, f"{per_eng[e]} / {n_eng[e]}"] for e in engines] + [
    [], ["Your market questions", "Times named out of 5, by engine"],
] + [[f'{p} {prompts[p]["area"]} — "{prompts[p]["text"]}"',
      "   ".join(f"{e}: {len(grid[(p, e)])}/5" for e in engines)] for p in market] + [
    [], ["Gaps", f"{len(gaps)} answers to your market questions did not name you (see Gaps tab)"],
]
for s in summ: ws.append(s)
ws.column_dimensions["A"].width = 70; ws.column_dimensions["B"].width = 70
for row in ws.iter_rows():
    for c in row: c.alignment = WR
for c in ws["A"]: c.font = Font(bold=True)

# Questions
sheet(wb.create_sheet("Questions"), ["ID", "Area", "Intent", "Question (exact wording)"],
      [[p, prompts[p]["area"], prompts[p]["intent"], prompts[p]["text"]] for p in sorted(prompts)],
      [8, 18, 16, 90])

# Your Mentions
def row_out(r, full=True):
    t = ts_et(r); cites = [cite_view(c) for c in (r.get("citations") or [])]
    seen = []; [seen.append(v) for _, v in cites if v not in seen]
    base = [r["engine"], (r.get("request_payload") or {}).get("model", ""), r["prompt_id"],
            prompts.get(r["prompt_id"], {}).get("area", ""), r.get("rep"),
            t.strftime("%Y-%m-%d %I:%M:%S %p ET") if t else r.get("ts")]
    if full:
        return base + [redact(r["response_text"]), "\n".join(seen), r.get("sha256", "")]
    others = len(set(m.group(0).lower() for m in red_pat.finditer(r["response_text"]))) if red_pat else 0
    doms = []; [doms.append(h) for h, _ in cites if h and h not in doms]
    return base + [others, "\n".join(doms), r.get("sha256", "")]

key = lambda r: (r["prompt_id"], r["engine"], r.get("rep") or 0)
sheet(wb.create_sheet("Your Mentions"),
      ["Engine", "Model", "Q", "Area", "Rep", "Date/time", "Full answer (other agents redacted)", "Sources cited", "SHA-256 of original"],
      [row_out(r) for r in sorted(mine, key=key)], [11, 18, 5, 14, 5, 22, 90, 50, 20])
sheet(wb.create_sheet("Gaps"),
      ["Engine", "Model", "Q", "Area", "Rep", "Date/time", "Other agents named", "Sources the engine relied on", "SHA-256 of original"],
      [row_out(r, full=False) for r in sorted(gaps, key=key)], [11, 18, 5, 14, 5, 22, 12, 50, 20])

# Method
m = [
 ["How it was run", "Each question was sent fresh (no memory, no prior conversation) to each engine's official API, 5 times, with live web search enabled, on the date above. Answers were stored exactly as returned."],
 ["Engines", "ChatGPT: OpenAI Responses API with web search. Gemini: Google Gemini API with Google Search grounding. Claude: Anthropic API with web search. Perplexity: Perplexity Agent API with web search. API answers can differ from the consumer apps, which add personalization."],
 ["What counts as 'named you'", f"The answer text contains \"{target}\" (this also matches your group name)."],
 ["Integrity", "Every answer is fingerprinted with SHA-256 at collection time. The fingerprint is of the ORIGINAL answer; the redacted text in this file will not reproduce it. Originals are archived and can be shown unredacted for your own entries."],
 ["Redaction", "Other agents' names are replaced with [Agent]; profile links for other agents are reduced to the site name. Each agent in the study receives only their own results."],
 ["Limitations", "One date, 20 questions, API surfaces. AI answers vary run to run, which is why each question was asked 5 times. Being named is a measure of visibility, not a ranking of quality."],
 ["Prepared by", "Rehan Masood · aivis"],
]
wsm = wb.create_sheet("Method")
for r in m: wsm.append(r)
wsm.column_dimensions["A"].width = 26; wsm.column_dimensions["B"].width = 110
for row in wsm.iter_rows():
    for c in row: c.alignment = WR
for c in wsm["A"]: c.font = Font(bold=True)

out = Path("realtor_v1/packages"); out.mkdir(parents=True, exist_ok=True)
fn = out / f"{target.replace(' ', '_')}_AI_visibility_{t0:%Y-%m-%d}.xlsx"
wb.save(fn)
print(f"wrote {fn}")
print(f"mentions={len(mine)}  gaps={len(gaps)}  market={market}  window={t0:%I:%M %p}-{t1:%I:%M %p} ET")
gap_eng = Counter(r["engine"] for r in gaps); print("gaps by engine:", dict(gap_eng))
gap_q = Counter(r["prompt_id"] for r in gaps); print("gaps by question:", dict(gap_q))
# Leak check: capitalized "First Last" pairs still present after redaction, for a human to eyeball.
pair = re.compile(r"\b[A-Z][a-z]+(?:\s[A-Z]\.)?\s[A-Z][a-z]+\b")
left = Counter()
for r in mine:
    for m in pair.findall(redact(r["response_text"])):
        if not tpat.search(m): left[m] += 1
print("\nNames-like pairs still visible after redaction (review; most will be places/firms/headings):")
for k, v in left.most_common(40): print(f"  {v:3d}  {k}")
