#!/usr/bin/env python3
"""
apply_d4_paren v0.2 — corrects a false negative introduced by v0.1.

WHY
---
v0.1's cue list omitted the parenthetical citation form. The operator's own
suite caught it in one run:

    tests/test_parser.py::test_parse_with_citations
    raw = "1. Asana - Great tool (asana.com)\\n2. Jira - Agile standard (atlassian.com)\\n"
    assert tools[0].citation_domains == ["asana.com"]     # got []

The adjacent test proves the parenthesis is a designed citation field, not
incidental punctuation:

    def test_parse_no_citation_explicit():
        raw = "1. Asana - Great tool (no citation)\\n"

Same slot. When there is no source, the model writes "(no citation)" there.
So a domain enclosed in parentheses or brackets is cited BY THE FORMAT, and
v0.1 was dropping real citations -- the false-negative direction every expert
on the panel named as worse than the defect being fixed, because it fails
silently and the score simply goes down.

WHAT IT CHANGES
---------------
  src/aivis/parser.py ONLY, and within it ONLY:
    * the `_d4_scan` span (adds `_d4_paren_span` + parenthetical qualification)
    * one exact sentence inside `extract_domains.__doc__`, so the published
      rule and the code do not diverge.
  Nothing else. DOMAIN_RE untouched. No test file is modified.

The negation guard still applies inside the parenthesis: "(no source for
asana.com)" is declined, so this does not reopen the 7ff6781 defect.

SAFETY
------
  Idempotent (marker _D4_PAREN). Requires v0.1 applied. Backs the file up to
  _d4_backup/ before writing. Deletes nothing.

Usage:  python apply_d4_paren_v0_2.py [--check]
"""

import hashlib
import os
import shutil
import re
import sys

VERSION = "apply_d4_paren v0.2"
PARSER = os.path.join("src", "aivis", "parser.py")
BACKUP_DIR = "_d4_backup"
MARKER = "_D4_PAREN"
REQUIRES = "_D4_URLISH"

NEW_SCAN = '''_D4_PAREN_OPEN = "(["
_D4_PAREN_CLOSE = ")]"


def _d4_paren_span(block, s, e):
    """Text from an enclosing opener to the match, or None if not enclosed.

    A domain inside (...) or [...] is cited by the format: in ranked-list
    output the parenthetical is the citation slot, which is why a model with
    no source writes "(no citation)" in exactly that position.
    """
    head = block[:s]
    stack = []
    for i, ch in enumerate(head):
        if ch in _D4_PAREN_OPEN:
            stack.append(i)
        elif ch in _D4_PAREN_CLOSE and stack:
            stack.pop()
    if not stack:
        return None
    for ch in block[e:]:
        if ch in _D4_PAREN_CLOSE:
            return head[stack[-1] + 1:]
        if ch in _D4_PAREN_OPEN:
            return None
    return None


def _d4_scan(block):
    """Yield (host, qualified) for one paragraph."""
    for m in _D4_URLISH.finditer(block):
        raw = re.sub(r"(?i)^https?://", "", m.group(0))
        host = _d4_clean(raw.split("/")[0])
        if _D4_HOSTOK.match(host):
            yield host, True

    for m in _D4_BARE.finditer(block):
        host, tld, path = m.group(1), m.group(2).lower(), m.group(3)
        host = _d4_clean(host)
        if tld not in _D4_TLD or tld in _D4_EXT:
            yield host, False
            continue
        if path:
            yield host, True
            continue
        par = _d4_paren_span(block, m.start(), m.end())
        if par is not None:
            yield host, not _D4_NEG.search(par)
            continue
        before = block[: m.start()]
        cues = list(_D4_CUE.finditer(before))
        if not cues:
            yield host, False
            continue
        yield host, not _D4_NEG.search(before[cues[-1].end():])


'''

DOC_OLD = ("cue earlier in the same paragraph with no negation in between. Bare")
DOC_NEW = ("cue earlier in the same paragraph, or an enclosing parenthesis,\n"
           "    with no negation in between. Bare")


def sha12(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:12]


def main(argv):
    check = "--check" in argv
    print(VERSION)
    if not os.path.isfile(PARSER):
        print("REFUSED: missing %s (run from the repo root)" % PARSER)
        return 1

    with open(PARSER, "r", encoding="utf-8", newline="") as fh:
        src = fh.read()

    if REQUIRES not in src:
        print("REFUSED: v0.1 not applied (marker %s absent)" % REQUIRES)
        return 1
    if MARKER in src:
        print("ALREADY_APPLIED=1  (marker %s present; nothing written)" % MARKER)
        return 0

    m = re.search(r"^def _d4_scan\b", src, re.M)
    if not m:
        print("REFUSED: no top-level `def _d4_scan`")
        return 1
    nxt = re.search(r"^def \w+", src[m.end():], re.M)
    if not nxt:
        print("REFUSED: no following top-level def; refusing to guess span end")
        return 1

    span = src[m.start(): m.end() + nxt.start()]
    new = src[:m.start()] + NEW_SCAN + src[m.end() + nxt.start():]

    hits = new.count(DOC_OLD)
    if hits != 1:
        print("REFUSED: docstring sentence found %d times, expected 1" % hits)
        return 1
    new = new.replace(DOC_OLD, DOC_NEW, 1)

    if check:
        print("CHECK_ONLY=1")
        print("SPAN_LINES=%d" % span.count("\n"))
        print("DOC_EDITS=1")
        print("SHA_BEFORE=%s" % sha12(src))
        print("SHA_AFTER=%s" % sha12(new))
        return 0

    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copyfile(PARSER, os.path.join(BACKUP_DIR, "parser.py.pre_paren"))
    with open(PARSER, "w", encoding="utf-8", newline="") as fh:
        fh.write(new)

    with open(PARSER, "r", encoding="utf-8", newline="") as fh:
        after = fh.read()
    ok = (MARKER in after and "DOMAIN_RE = re.compile" in after
          and "def extract_domain_candidates" in after)
    print("SPAN_REPLACED_LINES=%d" % span.count("\n"))
    print("DOMAIN_RE_UNTOUCHED=%d" % int("DOMAIN_RE = re.compile" in after))
    print("PARSER_LINES=%d" % (after.count("\n") + 1))
    print("APPLIED=%d" % int(ok))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
