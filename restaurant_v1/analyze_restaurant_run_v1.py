#!/usr/bin/env python3
"""analyze_restaurant_run_v1.py - restaurant-name extraction and PREREG metrics for restaurant_v1.

Stdlib only. Reads run files written by run_bank_multi_v2.py, writes a NEW output directory.
Every count this prints is computed here; nothing is typed. Extraction is a heuristic parse and
carries UNVALIDATED_PARSE_PENDING_KAPPA until an agreement study exists.

Two passes per market:
  1. DISCOVERY (structural). A name is taken from where engines put names: the bold or plain head of
     a list item, a line-leading bold span, the name column of a table, a heading with no names under
     it, or (weakest) a bold span inside a sentence. Headings and list items with names beneath them
     are categories ("Greek Food"), not names. Labels ("Vibe:", "What to order:") are rejected by a
     stoplist, by a sentence-case test ("Go early"), and by repetition (a colon-terminated head that
     occurs three times or more in one response is a label - twice for a one-word head; a multi-word
     head seen twice is a name plus its recap).
     A bare bold head ending in a colon, or a head ending in a list word ("Picks"), hands its place to
     the names nested under it. Names written together ("A, B, C") are split when the market's own
     answers show the parts are places.
  2. MATCHING (lexicon). A name discovered structurally somewhere in the market is then searched for
     in every response, case-sensitively and on word boundaries, so a restaurant named only in
     running prose is still counted. One-word names need structural support in three responses first.
     Names never discovered structurally in any response are missed: all counts are LOWER bounds.

Usage (from the repo root):
  python restaurant_v1/analyze_restaurant_run_v1.py restaurant_v1/runs/multi_*_nyc_restaurant_v1_20261007.jsonl \\
      --out restaurant_v1/results_nyc_v1
  add --verified <filled verify sheet> (and a new --out) for the verified metrics and the decision rule.
  add --merges restaurant_v1/merges_v1.csv to fold spelling variants together (from_key,to_key).

Refuses: an existing --out path; run files from more than one bank_version; the same
(engine, prompt, rep) cell twice; zero clean rows.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

PARSE_STATUS = "UNVALIDATED_PARSE_PENDING_KAPPA"
SAMPLE_SEED = 20261006          # PREREG: verification sample seed
TIER_A_MIN = 10                 # PREREG: verify ALL candidates named in >= 10 responses
TIER_B_MIN = 3                  # PREREG: sample 40 from the 3-9 band; <= 2 excluded from every metric
TIER_B_SAMPLE = 40
VERDICTS = ("open", "closed", "not_found", "wrong_area", "noise")
ENGINES_REQUIRED_FOR_R3 = 3
REPS_REQUIRED_FOR_R2 = 3
R5_MAX = 0.15
LABEL_REPEATS = 3               # a colon-terminated head this many times in one answer is a label (one-word heads: 2)
STRUCTURAL = ("list_bold", "line_bold", "table", "list_plain", "heading_leaf")   # strongest first


def _load_wilson():
    """Import the product's Wilson interval instead of re-implementing it (the B7 lesson)."""
    path = Path(__file__).resolve().parents[1] / "src" / "aivis" / "intervals.py"
    spec = importlib.util.spec_from_file_location("aivis_intervals_for_restaurant_v1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load %s" % path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.wilson


wilson = _load_wilson()

# ----------------------------------------------------------------------------- text helpers

LINK_IN_PARENS = re.compile(r"\(\s*\[[^\]]*\]\([^)]*\)(?:\s*[,;]?\s*\[[^\]]*\]\([^)]*\))*\s*\)")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
CITE_MARK = re.compile(r"\[\d+(?:\s*,\s*\d+)*\]|【[^】]*】|\[\^\d+\]")
LIST_RE = re.compile(r"^(\s*)([-*•–·]|\d{1,2}[.)])\s+(.*)$")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
LEAD_BOLD = re.compile(r"^[^\w*_]*(?:\*\*|__)(.+?)(?:\*\*|__)(.*)$")
ANY_BOLD = re.compile(r"(?:\*\*|__)(.+?)(?:\*\*|__)")
SEPARATOR = re.compile(r"\s[–—-]\s|\s[–—]|[–—]\s|:(?=\s|$)")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
LEAD_NUM = re.compile(r"^\s*#?\d{1,2}[.):]\s+")
TRAIL_PAREN = re.compile(r"\s*[\(\[（][^\)\]）]*[\)\]）]?\s*$")
INNER_SPLIT = re.compile(r"\s[–—|-]\s|\s[–—]|[–—]\s")
TERMINAL = re.compile(r"[.!?)\]*_`|:\"'”’]\s*$")
SENTENCE_BREAK = re.compile(r"[a-z]{3,}[.!?]\s+\S")      # "great food. Try" - but not "St. Anselm"
NAME_HEADER_EXACT = re.compile(r"(restaurant|name|spot|place|venue|eatery|pick)s?", re.I)
NAME_HEADER_LOOSE = re.compile(r"restaurant|name|venue|eatery", re.I)

# Structure words: a head made only of these (plus place words) is scaffolding, not a place.
GENERIC = frozenset("""
a also an and at best bottom choice choices conclusion eat eats favorite favorites favourite
favourites final for go guide here honorable in line list mention mentions more my notable note
notes of option options other our overall overview pick picks place places quick rated
recommendation recommendations restaurant restaurants runner runners spot spots standout standouts
summary takeaway takeaways the thought thoughts tip tips to top up verdict what where why worth your
alternative alternatives based compare comparison consider contact faq key know needs next on questions
step steps suggestion suggestions table things
""".split())

# Place words that appear in the prompts but not in the rows' `area` field.
GEO = frozenset("""
bronx brooklyn city connecticut ct de delaware island ma manhattan massachusetts new ny nyc queens
staten york boston area neighborhood neighbourhood district downtown
""".split())

LABELS = frozenset(p.strip() for p in """
address|ambiance|ambience|atmosphere|average price|best for|bonus|book|booking|bottom line|budget|
capacity|cash only|caveat|closed|cons|cost|cuisine|details|dishes|distance|downside|drawback|
drawbacks|dress code|drinks|food|getting there|good for|good to know|great for|group size|heads up|
highlight|highlights|hours|how to book|ideal for|important|kid friendly|kids menu|known for|location|
menu|must order|must try|neighborhood|note|open|order|parking|perfect for|phone|price|price point|
price range|private dining|pro tip|pros|rating|reservation|reservations|seating|service|
signature dish|signature dishes|specialties|specialty|style|the food|the move|the vibe|tip|try|
try the|type|upside|verdict|vibe|wait|wait time|warning|website|what to expect|what to get|
what to know|what to order|what to try|when to go|where|why|why go|why it works|why visit|why we love it|dont miss|menu highlights|must try dishes|popular dishes|price level|recommended dishes|standout dishes|the draw|the scene|top dishes
""".replace("\n", "").split("|") if p.strip())

# A head ending in one of these introduces a list of places; it is not a place ("Wanderlog's Picks").
LISTWORDS = frozenset("awards choices favorites favourites mentions picks recommendations selections standouts winners".split())

# A line that opens with one of these is describing food, so a bold span on it is a dish, not a place.
DISH_LABELS = frozenset(p.strip() for p in """
dishes|dont miss|drinks|food|highlight|highlights|known for|menu|menu highlights|must order|must try|
must try dishes|order|popular dishes|recommended dishes|signature dish|signature dishes|specialties|
specialty|standout dishes|top dishes|try|try the|what to get|what to order|what to try
""".replace("\n", "").split("|") if p.strip())
LINE_LABEL = re.compile(r"^\s*(?:[-*•–·]\s+|\d{1,2}[.)]\s+)?[*_]{0,3}([^:*_]{2,40}?):[*_]{0,3}(?=\s|$)")
JOINED = re.compile(r",\s+|\s+&\s+|\s+and\s+")

CONNECTORS = frozenset("""a al and at au aux by con da das de del des di do dos du e el et i il la las le lo los
n of on the und van von y""".split())


def clean_text(text: str) -> str:
    """Drop citation links and markers; keep the visible words."""
    text = LINK_IN_PARENS.sub("", text)
    text = LINK.sub(lambda m: m.group(1), text)
    return CITE_MARK.sub("", text)


def strip_marks(s: str) -> str:
    return re.sub(r"[*_`]+", "", s).strip()


def _fold(s: str, keep_case: bool = False) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("’", "'").replace("‘", "'").replace("`", "'")
    if not keep_case:
        s = s.casefold()
    s = s.replace("&", " and ").replace("'", "")
    s = re.sub(r"[^\w]+|_+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_key(name: str) -> str:
    """Deterministic comparison key. Same input, same output, on any machine and any hash seed."""
    s = _fold(name)
    if s.startswith("the ") and len(s) > 4:
        s = s[4:]
    for tail in (" restaurant", " pizzeria", " and co"):          # PREREG name-merging rule
        if s.endswith(tail) and len(s) > len(tail):
            s = s[: -len(tail)]
    return s


def cased_needles(name: str):
    """How the name would be written in a sentence: folded like a key, capitals kept. "The" and a trailing
    "Restaurant"/"Pizzeria" are dropped only while two or more words remain: "The Smith" must not become
    " Smith " (which is also in "Smith Street"), so it is searched as "The Smith" and "the Smith"."""
    full = _fold(name, keep_case=True)
    core = full
    if core[:4].casefold() == "the " and len(core) > 4:
        core = core[4:]
    for tail in (" restaurant", " pizzeria", " and co"):
        if core.casefold().endswith(tail) and len(core) > len(tail):
            core = core[: -len(tail)]
    if len(core.split()) >= 2 or core == full:
        return [" " + core + " "]
    forms = {full}
    if full[:4] == "The ":
        forms.add("the " + full[4:])
    return [" " + f + " " for f in sorted(forms)]


def cased_text(text: str) -> str:
    """The response, folded like cased_needles and space-padded for word-boundary search."""
    return " " + _fold(strip_marks(clean_text(text)), keep_case=True) + " "


def tidy_name(raw: str) -> str:
    """Surface form of a head: no markdown, no leading rank, no trailing bracket or colon."""
    s = strip_marks(raw)
    s = LEAD_NUM.sub("", s)
    s = INNER_SPLIT.split(s, maxsplit=1)[0]                   # "Via Vai – Italian" -> "Via Vai"
    for _ in range(2):
        s = TRAIL_PAREN.sub("", s.rstrip(" \t:;,"))            # "Via Vai (Astoria):" -> "Via Vai"
    return s.strip(" \t:–—-.,;\"'“”").strip()


def sentence_case(name: str) -> bool:
    """True when a word after the first starts lowercase and is not a connector: reads as a phrase."""
    words = name.split()
    if words and words[-1].casefold() in CONNECTORS | {"for", "to", "in", "with"}:
        return True
    return any(w[:1].islower() and w.casefold() not in CONNECTORS for w in words[1:])


def is_label(raw_head: str) -> bool:
    """Scaffolding heads: 'Vibe:', 'What to order:', 'Signature dish:'."""
    name = tidy_name(raw_head)
    key = norm_key(name)
    return not key or key in LABELS


def plausible_name(name: str, place_tokens: frozenset, strict_case: bool) -> bool:
    if not (2 <= len(name) <= 60):
        return False
    words = name.split()
    if not (1 <= len(words) <= 7) or not any(c.isalpha() for c in name):
        return False
    low = name.casefold()
    if "http" in low or name.rstrip().endswith(("?", "!")) or SENTENCE_BREAK.search(name):
        return False
    if sentence_case(name):                                   # "Interview 2-3 agents", "Go early"
        return False
    if strict_case:
        first = next((c for c in name if c.isalnum()), "")
        if not first or (first.isascii() and first.islower()):
            return False
    toks = norm_key(name).split()
    if not toks or toks[-1] in LISTWORDS:
        return False
    return not all(t in GENERIC or t in place_tokens for t in toks)


# ----------------------------------------------------------------------------- pass 1: discovery

def _table_cells(line: str):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _table_rows(lines):
    """{line index: header cells or None}. A table is a header row, a |---|---| row, then data rows.
    Leading and trailing pipes are optional, so 'Name | Notes' tables are found too."""
    role = {}
    for j, line in enumerate(lines):
        if "|" not in line or not TABLE_SEP.match(line) or j == 0 or "|" not in lines[j - 1]:
            continue
        header = _table_cells(lines[j - 1])
        role[j - 1], role[j] = None, None
        k = j + 1
        while k < len(lines) and lines[k].strip() and "|" in lines[k]:
            role[k] = header
            k += 1
    return role


def _parse_nodes(lines):
    """Lines -> structural nodes. Paragraph lines produce no node."""
    nodes, tables = [], _table_rows(lines)
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        if i in tables:
            header = tables[i]
            if header is None:                                 # the header row or the separator row
                continue
            cells = _table_cells(line)
            heads = [strip_marks(h) for h in header]
            col = next((j for j, h in enumerate(heads) if NAME_HEADER_EXACT.fullmatch(h)), None)
            if col is None:
                col = next((j for j, h in enumerate(heads) if NAME_HEADER_LOOSE.search(h)), None)
            if col is None or col >= len(cells):
                col = next((j for j, c in enumerate(cells)
                            if c and not re.fullmatch(r"[#\d.\s)]*", strip_marks(c))), None)
            if col is not None and cells[col]:
                parts = [c.strip() for c in strip_marks(cells[col]).split(",")]
                for raw in (parts if len(parts) >= 3 else [cells[col]]):   # "A, B, C" is three places
                    if raw:
                        nodes.append({"kind": "item", "indent": 0, "raw": raw, "colon": False, "bare": True,
                                      "klass": "table", "line": i, "bold_head": False, "weak": False})
            continue
        hm = HEADING_RE.match(line)
        if hm:
            nodes.append({"kind": "heading", "level": len(hm.group(1)), "raw": hm.group(2), "line": i,
                          "bold_head": bool(LEAD_BOLD.match(hm.group(2)))})
            continue
        lm = LIST_RE.match(line)
        if lm:
            indent, ordered, body = len(lm.group(1).expandtabs(4)), lm.group(2)[0].isdigit(), lm.group(3)
            bm = LEAD_BOLD.match(body)
            if bm:
                colon = strip_marks(bm.group(1)).endswith(":") or bm.group(2).lstrip().startswith(":")
                bare = not strip_marks(TRAIL_PAREN.sub("", bm.group(2))).strip(" :–—-")
                nodes.append({"kind": "item", "indent": indent, "raw": bm.group(1), "colon": colon, "bare": bare,
                              "klass": "list_bold", "line": i, "bold_head": True, "weak": False})
                continue
            plain = strip_marks(body)
            sm = SEPARATOR.search(plain)
            head = plain[: sm.start()] if sm else plain
            weak = not (sm or ordered)
            if (2 if weak else 1) <= len(head.split()) <= 6 and not head.rstrip().endswith((".", "!", "?")):
                # "weak": an unordered bullet with no separator ("- Sweet Afton"). Too little structure to
                # trust on its own; it counts only when it sits under a category head, and a one-word
                # weak bullet ("- Reviews") is never taken.
                nodes.append({"kind": "item", "indent": indent, "raw": head, "klass": "list_plain", "bare": not sm,
                              "colon": bool(sm and sm.group(0).startswith(":")), "line": i, "bold_head": False,
                              "weak": weak})
            continue
        bm = LEAD_BOLD.match(line)
        if bm:
            rest = strip_marks(bm.group(2))
            colon = strip_marks(bm.group(1)).endswith(":") or rest.startswith(":")
            if not rest.strip(" :–—-"):                        # the whole line is one bold span
                if not colon:                                  # "**Highlights:**" alone is a label, not a section
                    nodes.append({"kind": "heading", "level": 7, "raw": bm.group(1), "line": i, "bold_head": True})
            else:
                nodes.append({"kind": "item", "indent": 0, "raw": bm.group(1), "colon": colon, "bare": False,
                              "klass": "line_bold", "line": i, "bold_head": True, "weak": False})
    return nodes


def discover(text: str, place_tokens: frozenset = frozenset()):
    """Return [(surface_name, key, klass)], unique by key, in document order."""
    lines = clean_text(text).splitlines()
    nodes = _parse_nodes(lines)
    items = [n for n in nodes if n["kind"] == "item"]

    repeated = Counter(norm_key(tidy_name(n["raw"])) for n in items if n["colon"])
    for n in items:
        n["name"] = tidy_name(n["raw"])
        key = norm_key(n["name"])
        label = is_label(n["raw"]) or repeated[key] >= (2 if len(key.split()) == 1 else LABEL_REPEATS)
        strict = n["klass"] == "list_plain"
        n["ok"] = (not label) and plausible_name(n["name"], place_tokens, strict)
        n["listword"] = (norm_key(n["name"]).split() or [""])[-1] in LISTWORDS

    # Nesting.
    #  - A head that is a category by its own text - a bare bold head ending in a colon ("- **Best Deli**:")
    #    or a head ending in a list word ("Wanderlog's Picks") - hands its place to the names under it.
    #  - A bare or colon-terminated head with bold or numbered names under it is a category ("- **Greek:**").
    #  - A head that carries its own description is a name; heads nested under it are details
    #    ("- **Taverna Kyclades** - seafood" / "  - **Grilled Octopus** - order it").
    #  - A weak bullet counts only when a category head adopted it.
    for idx, n in enumerate(nodes):
        if n["kind"] != "item" or n["klass"] not in ("list_bold", "list_plain") or n["weak"]:
            continue
        children = []
        for later in nodes[idx + 1:]:
            if later["kind"] == "heading" or later["indent"] <= n["indent"]:
                break
            if later["ok"]:
                children.append(later)
        if not children:
            continue
        strong = [c for c in children if not c["weak"]]
        category_by_text = (n["klass"] == "list_bold" and n["colon"] and n["bare"]) or n["listword"]
        if category_by_text or (n["ok"] and (n["colon"] or n["bare"]) and strong):
            n["ok"] = False
            for c in children:
                c["adopted"] = True
        elif n["ok"]:
            for c in children:
                c["ok"] = False
    for n in items:
        if n["weak"] and not n.get("adopted"):
            n["ok"] = False

    # Bold spans inside sentences: weakest class. On a line whose head IS a bold span, that span is skipped.
    head_span_lines = {n["line"] for n in nodes if n.get("bold_head")}
    inline = []
    for i, line in enumerate(lines):
        spans = ANY_BOLD.findall(line)
        lead = LINE_LABEL.match(line)
        if spans and lead and norm_key(lead.group(1)) in DISH_LABELS:     # "*What to get:* **The Bomb**"
            continue
        for raw in (spans[1:] if i in head_span_lines else spans):
            if strip_marks(raw).endswith(":") or is_label(raw):
                continue
            name = tidy_name(raw)
            if plausible_name(name, place_tokens, True):
                inline.append((i, name))
    inline_lines = {i for i, _ in inline}
    for n in items:                                            # "- Greek: **Taverna Kyclades**": the head is a category
        if n["ok"] and n["klass"] == "list_plain" and n["line"] in inline_lines:
            n["ok"] = False

    found = [(n["line"], 0, n["name"], n["klass"]) for n in items if n["ok"]]
    found += [(i, 1, name, "bold_inline") for i, name in inline]

    # A heading is a category if any name sits on it or in its section; otherwise it may itself be a name.
    named_lines = sorted(f[0] for f in found)
    headings = [n for n in nodes if n["kind"] == "heading"]
    for idx, h in enumerate(headings):
        end, has_sub = len(lines), False
        for later in headings[idx + 1:]:
            if later["level"] <= h["level"]:
                end = later["line"]
                break
            if not is_label(later["raw"]):
                has_sub = True
        if has_sub or any(h["line"] <= ln < end for ln in named_lines):
            continue
        raw = strip_marks(h["raw"])
        name = tidy_name(h["raw"])
        if raw.endswith(":") or is_label(h["raw"]):
            continue
        if plausible_name(name, place_tokens, True):
            found.append((h["line"], 0, name, "heading_leaf"))

    # One entry per key: position of its EARLIEST mention, class of its STRONGEST mention.
    found.sort(key=lambda f: (f[0], f[1], norm_key(f[2])))
    order, best = [], {}
    for _, _, name, klass in found:
        key = norm_key(name)
        if not key:
            continue
        if key not in best:
            best[key] = [name, klass]
            order.append(key)
        elif best[key][1] == "bold_inline" and klass != "bold_inline":
            best[key] = [name, klass]
    return [(best[k][0], k, best[k][1]) for k in order]


# ----------------------------------------------------------------------------- loading

def load_rows(paths):
    rows, errors, versions = [], Counter(), Counter()
    for p in paths:
        for ln, line in enumerate(Path(p).read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError as ex:
                sys.exit("REFUSE: %s line %d is not valid JSON (%s). A truncated run file is not analysed." % (p, ln, ex.msg))
            versions[r.get("bank_version", "unknown")] += 1
            if r.get("error") or not r.get("response_text"):
                errors[r.get("engine", "unknown")] += 1
                continue
            r["_src"] = "%s:%d" % (Path(p).name, ln)
            r["_rep"] = str(r["rep"] if r.get("rep") is not None else r.get("run_index", ""))
            rows.append(r)
    seen = Counter((r.get("engine"), r.get("prompt_id"), r["_rep"]) for r in rows)
    dupes = sorted(str(k) for k, c in seen.items() if c > 1)
    if dupes:
        sys.exit("REFUSE: %d (engine, prompt, rep) cells appear more than once, e.g. %s. Pass one run file per "
                 "engine; a re-run replaces the earlier file, it is not added to it." % (len(dupes), dupes[:3]))
    return rows, errors, versions


def place_token_set(rows) -> frozenset:
    toks = set(GEO)
    for r in rows:
        for field in ("area", "family"):
            toks.update(norm_key(str(r.get(field) or "")).split())
    return frozenset(toks)


def domain_of(cite: dict) -> str:
    host = (urlparse(cite.get("url", "")).hostname or "").lower()
    if "vertexaisearch" in host or not host:                 # Gemini redirect: the title carries the site
        title = (cite.get("title") or "").strip().lower()
        host = title if re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", title) else (host or "unknown")
    return host[4:] if host.startswith("www.") else host


def prose_eligible(key: str, structural_support: int) -> bool:
    """May this name be counted from running prose? A one-word name needs more support, because one
    stray structural hit on a word like 'Reviews' would otherwise be matched in hundreds of answers."""
    if len(key.split()) >= 2:
        return structural_support >= 1
    return structural_support >= 3 and len(key) >= 4


# ----------------------------------------------------------------------------- analysis

def joined_parts(discovered, place_tokens):
    """{surface name: [part names]} for names that are really several places written together.
    "Queen's Room, Sanfords, Sweet Afton" is split when the market itself shows the parts are places:
    two parts need BOTH named alone somewhere; three or more may carry ONE part not seen alone, if that
    part is at least two words (it becomes known, and the pass repeats). "Sal, Kris & Charlie's Deli" and "Tootles & French" have no such parts
    and stay whole."""
    known = {key for disc in discovered for name, key, _ in disc if not JOINED.search(name)}
    joined = sorted({name for disc in discovered for name, _, _ in disc if JOINED.search(name)})
    out, changed = {}, True
    while changed:
        changed = False
        for name in joined:
            if name in out:
                continue
            parts = [x.strip() for x in JOINED.split(name) if x.strip()]
            if len(parts) < 2 or not all(plausible_name(x, place_tokens, True) for x in parts):
                continue
            unknown = [x for x in parts if norm_key(x) not in known]
            n_known = len(parts) - len(unknown)
            if any(len(norm_key(x).split()) < 2 for x in unknown):    # a one-word part must be known already
                continue
            if (len(parts) == 2 and n_known == 2) or (len(parts) >= 3 and n_known >= len(parts) - 1):
                out[name] = parts
                known.update(norm_key(x) for x in parts)
                changed = True
    return out


def split_joined(disc, parts_of):
    out, seen = [], set()
    for name, key, klass in disc:
        for nm in parts_of.get(name, [name]):
            k = norm_key(nm) if name in parts_of else key
            if k not in seen:
                seen.add(k)
                out.append((nm, k, klass))
    return out


def apply_merges(disc, merges):
    """Re-key discovered names through the hand-written merge list; first occurrence wins."""
    seen, out = set(), []
    for name, key, klass in disc:
        key = merges.get(key, key)
        if key not in seen:
            seen.add(key)
            out.append((name, key, klass))
    return out


def analyse(rows, verified=None, merges=None):
    """Everything the outputs need. `verified`: {key: verdict} or None (= all candidates).
    `merges`: {from_key: to_key} from merges_v1.csv, or None.

    PREREG: a name in <= 2 responses is excluded from EVERY metric, so R1 and first-named are
    computed on names in >= 3 responses, exactly like R2, R3 and R4."""
    merges = merges or {}
    place_tokens = place_token_set(rows)
    per_row, surface, support, merge_hits = [], defaultdict(Counter), Counter(), Counter()
    discovered = [discover(r["response_text"], place_tokens) for r in rows]
    parts_of = joined_parts(discovered, place_tokens)
    for raw in discovered:
        raw = split_joined(raw, parts_of)
        for _, key, _ in raw:
            if key in merges:
                merge_hits[key] += 1
        disc = apply_merges(raw, merges)
        for name, key, klass in disc:
            surface[key][name] += 1
            support[key] += klass in STRUCTURAL
        per_row.append(disc)
    lexicon = sorted(surface)                                 # sorted: no set-order dependence
    display = {k: sorted(surface[k].items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for k in lexicon}
    needles = [(k, sorted({f for n in surface[k] for f in cased_needles(n)}))
               for k in lexicon if prose_eligible(k, support[k])]

    mentions = []                                             # one dict per response
    for r, disc in zip(rows, per_row):
        m = {key: klass for _, key, klass in disc}
        padded = cased_text(r["response_text"])
        for key, forms in needles:
            if key not in m and any(f in padded for f in forms):
                m[key] = "prose"
        ordered = [key for _, key, klass in disc if klass != "bold_inline"] or [key for _, key, _ in disc]
        mentions.append({"all": m, "ordered": ordered})

    keep = (lambda k: verified.get(k) == "open") if verified is not None else (lambda k: True)
    resp_count, struct_count, prose_only = Counter(), Counter(), Counter()
    engines_of, areas_of = defaultdict(set), defaultdict(set)
    per_cell = defaultdict(Counter)                           # (prompt, engine) -> key -> reps naming it
    per_area = defaultdict(lambda: defaultdict(set))          # area -> key -> engines
    cell_reps = Counter()
    for r, m in zip(rows, mentions):
        cell_reps[(r["prompt_id"], r["engine"])] += 1
        for k in sorted(k for k in m["all"] if keep(k)):
            resp_count[k] += 1
            (prose_only if m["all"][k] == "prose" else struct_count)[k] += 1
            engines_of[k].add(r["engine"])
            areas_of[k].add(r.get("area") or "")
            per_cell[(r["prompt_id"], r["engine"])][k] += 1
            per_area[r.get("area") or ""][k].add(r["engine"])

    elig = {k for k in resp_count if resp_count[k] >= TIER_B_MIN}            # <= 2 excluded from metrics
    named_rows, first_count = Counter(), Counter()
    for r, m in zip(rows, mentions):
        m["counted"] = sorted(k for k in m["all"] if k in elig)
        m["first"] = next((k for k in m["ordered"] if k in elig), "")       # first structurally placed counted name
        named_rows[r["engine"]] += bool(m["counted"])
        if m["first"]:
            first_count[m["first"]] += 1
    r2 = sorted({k for c in per_cell.values() for k, n in c.items() if n >= REPS_REQUIRED_FOR_R2 and k in elig})
    r3 = sorted({k for a in per_area.values() for k, e in a.items()
                 if len(e) >= ENGINES_REQUIRED_FOR_R3 and k in elig})
    top10 = sorted(elig, key=lambda k: (-resp_count[k], k))[:10]
    return {
        "rows": rows, "mentions": mentions, "display": display,
        "n_total": len(rows), "by_engine": Counter(r["engine"] for r in rows), "named_rows": named_rows,
        "resp_count": resp_count, "struct_count": struct_count, "prose_only": prose_only,
        "first_count": first_count, "engines_of": engines_of, "areas_of": areas_of,
        "r2": r2, "r3": r3, "r4": (sum(resp_count[k] for k in top10), sum(resp_count[k] for k in elig)),
        "cells": (sum(1 for c in cell_reps.values() if c == 5), len(cell_reps)),
        "merge_hits": merge_hits, "verified_mode": verified is not None,
    }


def tier_of(n: int) -> str:
    return "A" if n >= TIER_A_MIN else ("B" if n >= TIER_B_MIN else "excluded")


def verification_sheet(res):
    """All of tier A; a seeded random 40 of tier B. Reproducible: sorted keys + fixed seed."""
    a = sorted(k for k in res["resp_count"] if res["resp_count"][k] >= TIER_A_MIN)
    b = sorted(k for k in res["resp_count"] if TIER_B_MIN <= res["resp_count"][k] < TIER_A_MIN)
    sample = sorted(random.Random(SAMPLE_SEED).sample(b, min(TIER_B_SAMPLE, len(b))))
    return [(k, "A") for k in a] + [(k, "B") for k in sample], len(a), len(b)


def read_verified(path, sheet):
    """Filled sheet -> {key: verdict}. Every verdict must belong to a row of the CURRENT sheet: if the
    merge list or the run files changed after checking, the sample changed and old verdicts do not carry."""
    out, bad = {}, []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not {"key", "verdict"} <= set(reader.fieldnames or []):
            sys.exit("REFUSE: %s needs columns 'key' and 'verdict'; found %s" % (path, reader.fieldnames))
        for row in reader:
            k, v = (row.get("key") or "").strip(), (row.get("verdict") or "").strip().lower()
            if not k or not v:
                continue
            if v not in VERDICTS:
                bad.append((k, v))
            elif out.get(k, v) != v:
                sys.exit("REFUSE: %r has two different verdicts in %s" % (k, path))
            else:
                out[k] = v
    if bad:
        sys.exit("REFUSE: unknown verdicts %s; allowed: %s" % (bad[:5], ", ".join(VERDICTS)))
    on_sheet = {k for k, _ in sheet}
    stray = sorted(k for k in out if k not in on_sheet)
    if stray:
        sys.exit("REFUSE: %d verdict(s) are for names not on the current verification sheet, e.g. %s. The sheet "
                 "changes when run files or the merge list change; re-check against the sheet this run writes."
                 % (len(stray), stray[:3]))
    return out


def read_merges(path):
    """merges_v1.csv: columns from_key,to_key (both as printed in candidates.csv). Chains are refused."""
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not {"from_key", "to_key"} <= set(reader.fieldnames or []):
            sys.exit("REFUSE: %s needs columns 'from_key' and 'to_key'; found %s" % (path, reader.fieldnames))
        for row in reader:
            a, b = (row.get("from_key") or "").strip(), (row.get("to_key") or "").strip()
            if a and b and a != b:
                out[a] = b
    chained = sorted(a for a, b in out.items() if b in out)
    if chained:
        sys.exit("REFUSE: merge chains (to_key is itself merged away): %s" % chained[:5])
    return out


def pct(k, n):
    return "ABSTAIN (n=0)" if n == 0 else "%.1f%% (%d of %d)" % (100.0 * k / n, k, n)


def decision(res, sheet, verified):
    """PREREG decision rule. Returns (verdict line, [R5 lines]). No verdict until every sheet row has one:
    an unchecked name counts as not open, which would understate R3."""
    lines, stats = [], {}
    for t in ("A", "B"):
        keys = [k for k, tt in sheet if tt == t]
        noise = [k for k in keys if verified.get(k) == "noise"]
        checked = [k for k in keys if verified.get(k) and verified[k] != "noise"]
        bad = [k for k in checked if verified[k] in ("closed", "not_found", "wrong_area")]
        unfilled = [k for k in keys if not verified.get(k)]
        lines.append("R5 tier %s: closed+not_found+wrong_area = %s | noise excluded: %d | no verdict yet: %d of %d" % (
            t, pct(len(bad), len(checked)), len(noise), len(unfilled), len(keys)))
        stats[t] = (len(bad), len(checked), len(unfilled), len(keys))
    bad, checked = stats["A"][0], stats["A"][1]
    unfilled = stats["A"][2] + stats["B"][2]
    r3, r2 = set(res["r3"]), set(res["r2"])
    if unfilled:
        return "NOT EVALUATED - %d of %d sheet rows have no verdict" % (unfilled, len(sheet)), lines
    if len(r3) < 5:
        return "NO TOP SET (R3=%d, below 5)" % len(r3), lines
    if len(r3) >= 10 and r3 <= r2 and checked and bad / checked <= R5_MAX:
        return "STABLE TOP SET (R3=%d, all of them in R2, tier A R5 %s)" % (len(r3), pct(bad, checked)), lines
    return "INCONCLUSIVE (R3=%d; R3 names also in R2: %d of %d; tier A R5 %s)" % (
        len(r3), len(r3 & r2), len(r3), pct(bad, checked)), lines


def _write_csv(path: Path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def write_outputs(out: Path, res, base, errors, versions, verified, sheet_meta, merges=None):
    """`res` = the analysis being reported; `base` = the same rows with no verification filter.
    Written to <out>.partial and renamed at the end, so a crash never leaves a half-filled <out>."""
    tmp = out.with_name(out.name + ".partial")
    tmp.mkdir(parents=True)
    rows, n = res["rows"], res["n_total"]
    engines = sorted(res["by_engine"])
    sheet, n_a, n_b = sheet_meta
    merges = merges or {}

    cand_rows = []
    for k in sorted(res["resp_count"], key=lambda k: (-res["resp_count"][k], k)):
        c = res["resp_count"][k]
        _, lo, hi = wilson(c, n)
        cand_rows.append([k, res["display"][k], c, n, "%.1f" % (100.0 * c / n), "%.1f" % (100 * lo), "%.1f" % (100 * hi),
                          len(res["engines_of"][k]), ";".join(sorted(res["engines_of"][k])),
                          len(res["areas_of"][k]), res["struct_count"][k], res["prose_only"][k],
                          res["first_count"][k], tier_of(c), (verified or {}).get(k, "")])
    _write_csv(tmp / "candidates.csv",
               ["key", "display", "responses", "of_n", "share_pct", "wilson95_lo_pct", "wilson95_hi_pct", "engines_n",
                "engines", "areas_n", "structural_responses", "prose_only_responses", "first_named_responses", "tier",
                "verdict"], cand_rows)

    cite_rows, cut_rows, domains, resp_rows = Counter(), Counter(), defaultdict(Counter), []
    for r, m in zip(rows, res["mentions"]):
        cites = r.get("citations") or []
        cut = not TERMINAL.search(r["response_text"].rstrip())
        cite_rows[r["engine"]] += bool(cites)
        cut_rows[r["engine"]] += cut
        for d in sorted({domain_of(c) for c in cites}):
            domains[r["engine"]][d] += 1
        resp_rows.append([r["engine"], r["prompt_id"], r["_rep"], r.get("area", ""), r.get("intent", ""),
                          len(r["response_text"]), int(cut), int(bool((r.get("request_payload") or {}).get("tools"))),
                          len(cites), len(m["counted"]), m["first"], ";".join(m["counted"]), r["_src"]])
    _write_csv(tmp / "per_response.csv",
               ["engine", "prompt_id", "rep", "area", "intent", "chars", "ends_without_terminal_punct",
                "search_tool_in_payload", "citations", "counted_names", "first_named", "keys", "source_row"], resp_rows)
    _write_csv(tmp / "domains.csv", ["engine", "domain", "responses_citing", "of_engine_responses"],
               [[e, d, c, res["by_engine"][e]] for e in engines
                for d, c in sorted(domains[e].items(), key=lambda kv: (-kv[1], kv[0]))])
    _write_csv(tmp / "verify_sheet.csv",
               ["key", "display", "tier", "responses", "engines_n", "areas_n", "prose_only_responses", "verdict",
                "source_url", "checked_on", "notes"],
               [[k, base["display"][k], t, base["resp_count"][k], len(base["engines_of"][k]), len(base["areas_of"][k]),
                 base["prose_only"][k], (verified or {}).get(k, ""), "", "", ""] for k, t in sheet])

    mode = "VERIFIED NAMES ONLY (verdict=open)" if res["verified_mode"] else "ALL CANDIDATES - NOT VERIFIED"
    unused = sorted(k for k in merges if not base["merge_hits"][k])
    L = ["restaurant_v1 analysis - %s" % mode,
         "PARSE STATUS: %s" % PARSE_STATUS,
         "BANK %s | CLEAN RESPONSES %d | ERROR ROWS %d | POPULATION: the run files given" % (
             ",".join(sorted(versions)), n, sum(errors.values())),
         "PYTHON %s | prompt+engine cells with exactly 5 clean reps: %d of %d" % (
             sys.version.split()[0], res["cells"][0], res["cells"][1]),
         "MERGE RULES %d | rules that matched a name: %d%s" % (
             len(merges), len(merges) - len(unused), (" | NEVER MATCHED: %s" % unused[:5]) if unused else ""), ""]
    for e in engines:
        ne = res["by_engine"][e]
        L.append("[%s] n=%d errors=%d | R1 names>=1: %s | rows with >=1 citation: %s | ends without terminal punctuation: %s" % (
            e, ne, errors.get(e, 0), pct(res["named_rows"][e], ne), pct(cite_rows[e], ne), pct(cut_rows[e], ne)))
    L += ["[OVERALL] n=%d | R1 names>=1: %s" % (n, pct(sum(res["named_rows"].values()), n)), "",
          "All metrics count only names found in >=%d responses." % TIER_B_MIN,
          "Candidates before verification: tier A (>=%d responses) %d | tier B (%d-%d) %d" % (
              TIER_A_MIN, n_a, TIER_B_MIN, TIER_A_MIN - 1, n_b),
          "Verification sheet: %d rows = all %d of tier A + %d sampled from tier B (seed %d)" % (
              len(sheet), n_a, len(sheet) - n_a, SAMPLE_SEED),
          "Names counted here: %d (of %d distinct before the >=%d floor)" % (
              sum(1 for k in res["resp_count"] if res["resp_count"][k] >= TIER_B_MIN), len(res["resp_count"]), TIER_B_MIN),
          "R2 names in >=%d of 5 reps, same prompt+engine: %d" % (REPS_REQUIRED_FOR_R2, len(res["r2"])),
          "R3 names named by >=%d of %d engines, same area: %d" % (ENGINES_REQUIRED_FOR_R3, len(engines), len(res["r3"])),
          "R4 top-10 share of mentions: %s" % pct(*res["r4"]), "",
          "Most frequently named in this sample (R3 names; NOT an ordering - overlapping intervals are not ordered):"]
    for k in sorted(res["r3"], key=lambda k: (-res["resp_count"][k], k))[:25]:
        c = res["resp_count"][k]
        _, lo, hi = wilson(c, n)
        L.append("  %-34s %3d of %d [95%% CI %.1f-%.1f%%] engines=%d first-named=%d prose-only=%d" % (
            res["display"][k][:34], c, n, 100 * lo, 100 * hi, len(res["engines_of"][k]),
            res["first_count"][k], res["prose_only"][k]))
    L.append("")
    if verified is None:
        L += ["DECISION RULE: NOT EVALUATED - verification pending.",
              "Fill the verdict column of verify_sheet.csv (%s), then re-run with --verified and a new --out." % " | ".join(VERDICTS)]
    else:
        verdict, r5_lines = decision(res, sheet, verified)
        L += r5_lines + ["DECISION RULE: %s" % verdict]
    L += ["", "Limits: a name no engine ever put in a list head, table, heading or bold span is missed; prose-only",
          "matches are case-sensitive string matches and can still hit a phrase that is not the restaurant; a",
          "first-named count needs a structurally placed name, so prose-only answers have none; counts on verified",
          "names are lower bounds. Nothing here says anything about any restaurant's customers or revenue."]
    text = "\n".join(L) + "\n"
    (tmp / "summary.txt").write_text(text, encoding="utf-8")
    tmp.rename(out)
    return text


def main(argv=None):
    ap = argparse.ArgumentParser(description="restaurant_v1: extract restaurant names and compute the PREREG metrics")
    ap.add_argument("runs", nargs="+", help="run .jsonl files for ONE market")
    ap.add_argument("--out", required=True, help="new output directory (must not exist)")
    ap.add_argument("--verified", help="filled verify sheet CSV (columns key, verdict)")
    ap.add_argument("--merges", help="hand-written merge list CSV (columns from_key, to_key)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    partial = out.with_name(out.name + ".partial")
    if out.exists():
        sys.exit("REFUSE: %s exists. Versioned new paths only." % out)
    if partial.exists():
        sys.exit("REFUSE: %s exists - an earlier run stopped before finishing. It is left in place; "
                 "choose a different --out." % partial)
    missing = [p for p in a.runs if not Path(p).is_file()]
    if missing:
        sys.exit("REFUSE: no such run file(s): %s" % ", ".join(missing))
    rows, errors, versions = load_rows(a.runs)
    if len(versions) != 1:
        sys.exit("REFUSE: run files span bank versions %s; one market per analysis." % dict(versions))
    if not rows:
        sys.exit("REFUSE: zero clean rows in %d file(s); errors=%s" % (len(a.runs), dict(errors)))
    merges = read_merges(a.merges) if a.merges else None
    base = analyse(rows, merges=merges)
    sheet_meta = verification_sheet(base)                     # tiers are always set on ALL candidates
    verified = read_verified(a.verified, sheet_meta[0]) if a.verified else None
    res = analyse(rows, verified, merges) if verified is not None else base
    sys.stdout.write(write_outputs(out, res, base, errors, versions, verified, sheet_meta, merges))
    print("WROTE %s (candidates.csv, per_response.csv, domains.csv, verify_sheet.csv, summary.txt)" % out)


if __name__ == "__main__":
    main()
