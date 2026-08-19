#!/usr/bin/env python3
"""
apply_d4_fix v0.1 — closes D4 in aivis's citation extractor.

WHAT IT CHANGES, AND NOTHING ELSE
---------------------------------
  1. src/aivis/parser.py   — replaces ONLY the `extract_domains` function span
                             (from its `def` line to the next top-level `def`),
                             and inserts the constants it needs directly above.
                             `DOMAIN_RE` IS NOT TOUCHED — other code may use it.
                             Adds `extract_domain_candidates` (additive).
  2. tests/test_extract_domains_brand_v1.py — rewritten: 5 pins flipped to plain
                             tests, the broken guard preserved byte-for-byte and
                             marked strict-xfail with its contract-change reason,
                             plus 6 new guards for the panel's findings.

Both paths were named to the operator and approved. No other file is written.

SAFETY
------
  * Idempotent. A second run detects the marker and exits ALREADY_APPLIED,
    writing nothing.
  * Refuses if either target is missing or its expected shape is absent.
  * Copies both originals into _d4_backup/ (a NEW directory) before writing.
    git remains the primary restore: `git checkout -- <path>` against 90c6e65.
  * Deletes nothing, ever.

THE RULE (published definition)
-------------------------------
A host counts as a citation domain when it appears with http(s)://, with a
www. prefix, or with a following slash-path -- or, as a bare token, when its
suffix is a recognised TLD that is not a common source-file extension, AND a
citation cue (Source:, Cited:, Reference:, See:, According to, [n]) occurs
earlier in the same paragraph with no negation between the cue and the token.
Everything else is returned by extract_domain_candidates() and never counted.
Brand self-mentions get no exemption and no credit.

Usage:  python apply_d4_fix_v0_1.py            (from the repo root)
        python apply_d4_fix_v0_1.py --check    (report only, write nothing)
"""

import hashlib
import os
import re
import shutil
import sys

VERSION = "apply_d4_fix v0.1"
PARSER = os.path.join("src", "aivis", "parser.py")
TESTS = os.path.join("tests", "test_extract_domains_brand_v1.py")
BACKUP_DIR = "_d4_backup"
MARKER = "_D4_URLISH"


# ---------------------------------------------------------------------------
# The replacement span for parser.py
# ---------------------------------------------------------------------------

NEW_EXTRACT = '''# --- D4 fix: citation qualification -------------------------------------
# Rule published in the methodology page. A dotted token is a citation domain
# only in citation context. Everything else is a candidate, not a citation.
#
# Recognised suffixes. Deliberately a moderate inline set, not the full IANA
# root: the cue/URL-shape test is the control, this is a secondary sieve, and
# a fuller list would admit MORE source-file extensions, not fewer.
# Reviewed 2026-08-19.
_D4_TLD = frozenset("""
com org net edu gov mil int info biz name pro io ai app dev co xyz online
site tech store blog cloud digital agency media news press today world life
live work space team group solutions systems services network global me tv
uk de fr jp ca au nl it es se ch in br mx ru pl no fi dk be at ie nz sg kr
""".split())

# Suffixes that are real TLDs but overwhelmingly appear as source-file
# extensions in software prose. "see README.md" must not mint a citation.
# KNOWN ASYMMETRY, disclosed rather than discovered: a brand whose real domain
# ends in one of these cannot earn a bare-token citation. It still qualifies
# via URL shape.
_D4_EXT = frozenset("md py sh ts rs so cc as im cd la ml".split())

_D4_URLISH = re.compile(r"(?i)(?:https?://|www\\.)[^\\s<>\\"')\\]]+")
_D4_HOSTOK = re.compile(r"(?i)^(?:[a-z0-9][-a-z0-9]*\\.)+([a-z]{2,24})$")
_D4_BARE = re.compile(
    r"(?i)(?<![\\w@./-])((?:[a-z0-9][-a-z0-9]*\\.)+([a-z]{2,24}))(/[^\\s<>\\"')\\]]*)?"
)
_D4_CUE = re.compile(
    r"(?i)\\[\\d+\\]|\\b(?:sources?|cited|citations?|references?|see|according\\s+to)\\b"
)
# A cue followed by a denial is not a citation. This is the mirror image of the
# defect closed in 7ff6781: "Sources: none found for acme.com".
_D4_NEG = re.compile(
    r"(?i)\\b(?:no|none|not|non|never|unable|without|lacks?|lacking|absent|missing)\\b"
)


def _d4_clean(host):
    host = host.lower().strip(".,;:!?)]}'\\"")
    return host[4:] if host.startswith("www.") else host


def _d4_scan(block):
    """Yield (host, qualified) for one paragraph."""
    for m in _D4_URLISH.finditer(block):
        raw = m.group(0)
        raw = re.sub(r"(?i)^https?://", "", raw)
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
        before = block[: m.start()]
        cues = list(_D4_CUE.finditer(before))
        if not cues:
            yield host, False
            continue
        gap = before[cues[-1].end():]
        yield host, not _D4_NEG.search(gap)


def _d4_walk(text, want):
    out = []
    for block in re.split(r"\\n\\s*\\n", text or ""):
        for host, ok in _d4_scan(block):
            if ok is want and host not in out:
                out.append(host)
    return out


def extract_domains(text: str) -> list[str]:
    """Return citation domains found in text.

    A host qualifies when it carries a scheme, a www. prefix or a following
    slash-segment, or when it is bare with a recognised suffix and a citation
    cue earlier in the same paragraph with no negation in between. Bare
    uncued tokens are candidates, not citations -- see
    extract_domain_candidates. Brand self-mentions receive no exemption.
    """
    return _d4_walk(text, True)


def extract_domain_candidates(text: str) -> list[str]:
    """Domain-shaped tokens the rule declined to count.

    Published beside the score so a refusal is inspectable rather than
    invisible. Never feeds citation_score.
    """
    return _d4_walk(text, False)


'''


# ---------------------------------------------------------------------------
# The replacement content for the characterization test file
# ---------------------------------------------------------------------------

NEW_TESTS = '''"""
Characterization tests for aivis.parser.extract_domains -- the D4 defect.

STATE: the fix has landed. The five original pins are now plain tests. One
original guard is preserved byte-for-byte under a strict xfail because the
rule change deliberately broke its contract -- see CONTRACT CHANGE below.

CONTRACT CHANGE D4-C1 (2026-08-19)
----------------------------------
A bare dotted token with no citation cue and no URL shape is no longer a
citation domain. `test_guard_no_duplicates` asserted dedupe using an uncued
fixture, so it now returns []. Its assertion is UNCHANGED and marked
strict-xfail; the dedupe property it defended is re-pinned by
`test_guard_no_duplicates_under_cue` below.

The assertion was NOT loosened to `<= 1`. That would pass on an empty list, on
a None-shaped return, and on a completely broken extractor -- widening a check
to clear a failing case is register incidents #9 and #40, and it converts a
green tick into evidence for a claim nothing supports.
"""

import pytest

from aivis.parser import extract_domains, extract_domain_candidates


# ---------------------------------------------------------------------------
# GUARDS -- correct before and after the fix.
# ---------------------------------------------------------------------------

def test_guard_full_url_yields_bare_domain():
    got = extract_domains("See https://www.example.com/reports/2026 for detail.")
    assert "example.com" in got


def test_guard_bare_domain_in_citation_context_is_found():
    got = extract_domains("Source: example.org")
    assert "example.org" in got


def test_guard_multiple_distinct_domains_all_found():
    got = extract_domains("Cited: alpha.com and beta.co.uk and gamma.org")
    for expected in ("alpha.com", "beta.co.uk", "gamma.org"):
        assert expected in got, f"lost a real citation domain: {expected}"


@pytest.mark.xfail(strict=True, reason="CONTRACT CHANGE D4-C1: uncued bare token is no longer a citation")
def test_guard_no_duplicates():
    got = extract_domains("example.com and example.com again")
    assert got.count("example.com") == 1


def test_guard_empty_input_returns_empty_list():
    assert extract_domains("") == []
    assert extract_domains(None) == []


# ---------------------------------------------------------------------------
# GUARDS added with the fix -- the expert panel's findings.
# ---------------------------------------------------------------------------

def test_guard_no_duplicates_under_cue():
    """D4-C1's replacement: dedupe still holds, now with a cue present."""
    got = extract_domains("Source: example.com and example.com again")
    assert got.count("example.com") == 1


def test_guard_negation_after_cue_is_not_a_citation():
    """Mirror image of the defect closed in 7ff6781."""
    got = extract_domains("Sources: none found for acme.com")
    assert "acme.com" not in got


def test_guard_source_file_extension_is_not_a_citation():
    """.md is Moldova. A cue plus a valid TLD must not mint README.md."""
    got = extract_domains("See README.md for details, and setup.py to install.")
    assert "readme.md" not in got
    assert "setup.py" not in got


def test_guard_cue_does_not_leak_across_paragraphs():
    """Cue scope is the paragraph. A cue must not license the next one."""
    got = extract_domains("Source: alpha.com\\n\\nbeta.com is also popular.")
    assert "alpha.com" in got
    assert "beta.com" not in got


def test_guard_according_to_is_a_cue():
    got = extract_domains("According to g2.com the tool ranks well.")
    assert "g2.com" in got


def test_guard_declined_tokens_are_retrievable_not_discarded():
    """Nothing is silently dropped. A refusal must be inspectable."""
    text = "Monday.com is a popular project management tool. No sources cited."
    assert extract_domains(text) == []
    assert "monday.com" in extract_domain_candidates(text)


# ---------------------------------------------------------------------------
# FORMERLY PINNED -- the D4 defect. These now pass.
# ---------------------------------------------------------------------------

def test_brand_name_is_not_a_citation_domain():
    text = "Monday.com is a popular project management tool. No sources cited."
    assert extract_domains(text) == []


def test_unspaced_sentence_join_is_not_a_domain():
    got = extract_domains("The tool was available.Visit the vendor for pricing.")
    assert "available.visit" not in got


def test_abbreviation_join_is_not_a_domain():
    got = extract_domains("Supports Slack, Teams, etc.Integrations vary by plan.")
    assert "etc.integrations" not in got


def test_brand_name_excluded_when_a_real_citation_is_present():
    text = "Monday.com leads the category. Source: https://g2.com/reports"
    got = extract_domains(text)
    assert "g2.com" in got, "the real citation must survive"
    assert "monday.com" not in got, "the brand name must not be counted"


def test_docstring_no_longer_claims_behaviour_the_code_cannot_perform():
    src = extract_domains.__doc__ or ""
    assert "paths" not in src, "docstring still claims path stripping that cannot occur"
'''


# ---------------------------------------------------------------------------
# patch machinery
# ---------------------------------------------------------------------------

def sha12(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def read(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def fail(msg):
    print("REFUSED: " + msg)
    return 1


def main(argv):
    check_only = "--check" in argv
    print(VERSION)

    for p in (PARSER, TESTS):
        if not os.path.isfile(p):
            return fail("missing target %s (run from the repo root)" % p)

    src = read(PARSER)
    if MARKER in src:
        print("ALREADY_APPLIED=1  (marker %s present; nothing written)" % MARKER)
        return 0

    m = re.search(r"^def extract_domains\b", src, re.M)
    if not m:
        return fail("no top-level `def extract_domains` in %s" % PARSER)
    nxt = re.search(r"^def \w+", src[m.end():], re.M)
    if not nxt:
        return fail("no following top-level def; refusing to guess the span end")

    start, end = m.start(), m.end() + nxt.start()
    old_span = src[start:end]
    new_src = src[:start] + NEW_EXTRACT + src[end:]

    old_tests = read(TESTS)

    if check_only:
        print("CHECK_ONLY=1")
        print("SPAN_LINES=%d" % old_span.count("\n"))
        print("PARSER_SHA_BEFORE=%s" % sha12(src))
        print("PARSER_SHA_AFTER=%s" % sha12(new_src))
        return 0

    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copyfile(PARSER, os.path.join(BACKUP_DIR, "parser.py.pre_d4"))
    shutil.copyfile(TESTS, os.path.join(BACKUP_DIR, "test_brand_v1.py.pre_d4"))

    write(PARSER, new_src)
    write(TESTS, NEW_TESTS)

    after = read(PARSER)
    ok_marker = MARKER in after
    ok_untouched = "DOMAIN_RE = re.compile" in after
    ok_sibling = "def extract_domain_candidates" in after

    print("SPAN_REPLACED_LINES=%d" % old_span.count("\n"))
    print("DOMAIN_RE_UNTOUCHED=%d" % int(ok_untouched))
    print("SIBLING_ADDED=%d" % int(ok_sibling))
    print("BACKUPS=%s" % BACKUP_DIR)
    print("PARSER_LINES=%d TESTS_LINES=%d"
          % (after.count("\n") + 1, NEW_TESTS.count("\n") + 1))
    print("APPLIED=%d" % int(ok_marker and ok_untouched and ok_sibling))
    return 0 if (ok_marker and ok_untouched and ok_sibling) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
