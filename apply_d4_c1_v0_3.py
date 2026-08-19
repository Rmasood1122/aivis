#!/usr/bin/env python3
"""
apply_d4_c1 v0.3 — records contract change D4-C1 on the one test that
asserted the defect.

THE TEST
--------
    tests/test_parser_adversarial.py
    def test_integration_mention_becomes_a_citation_domain():
        raw = "1. Trello - Kanban boards that integrate with slack.com for notifications\\n"
        tools, meta = parse_tool_list(raw)
        assert tools[0].citation_domains == ["slack.com"]

`slack.com` there is a product being MENTIONED, not a source being CITED.
The test's own name states the defect -- a mention becoming a citation domain
-- and asserts it as expected behaviour. Under the D4 rule the correct answer
is [], so this test now fails.

WHAT THIS DOES
--------------
Adds ONE decorator directly above that def:

    pytest.mark.xfail(strict=True, reason="CONTRACT CHANGE D4-C1: ...")

and an `import pytest` if the file lacks one. THE ASSERTION IS NOT TOUCHED.

WHY NOT JUST FIX THE TEST
-------------------------
Deleting it, or changing ["slack.com"] to [], erases the evidence that the
suite was defending the bug. strict=True means that if the old permissive
behaviour ever returns, the suite goes RED rather than quietly accepting it --
the assertion keeps working as a tripwire in the opposite direction.

This is the same handling given to `test_guard_no_duplicates`, and it is
deliberately NOT the anti-pattern of loosening an assertion until it passes
(register incidents #9, #40).

SAFETY
------
  Idempotent (marker D4-C1). Backs the file up to _d4_backup/ first.
  Re-parses the file with `ast` after writing and reports the result --
  a syntax error is caught here, not by your test run. Deletes nothing.

Usage:  python apply_d4_c1_v0_3.py [--check]
"""

import ast
import hashlib
import os
import re
import shutil
import sys

VERSION = "apply_d4_c1 v0.3"
TARGET = os.path.join("tests", "test_parser_adversarial.py")
BACKUP_DIR = "_d4_backup"
MARKER = "D4-C1"
FUNC = "test_integration_mention_becomes_a_citation_domain"

DECORATOR = (
    '@pytest.mark.xfail(strict=True, reason="CONTRACT CHANGE D4-C1: '
    'a product mentioned in prose is not a citation. Assertion preserved '
    'byte-for-byte; strict=True means the old permissive behaviour returning '
    'turns this red again.")\n'
)


def sha12(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:12]


def main(argv):
    check = "--check" in argv
    print(VERSION)

    if not os.path.isfile(TARGET):
        print("REFUSED: missing %s (run from the repo root)" % TARGET)
        return 1

    with open(TARGET, "r", encoding="utf-8", newline="") as fh:
        src = fh.read()

    if MARKER in src:
        print("ALREADY_APPLIED=1  (marker %s present; nothing written)" % MARKER)
        return 0

    m = re.search(r"^def %s\s*\(" % re.escape(FUNC), src, re.M)
    if not m:
        print("REFUSED: no top-level `def %s`" % FUNC)
        return 1

    new = src[:m.start()] + DECORATOR + src[m.start():]

    added_import = 0
    if not re.search(r"^import pytest\b", new, re.M):
        first = re.search(r"^(?:import|from)\s+\S+", new, re.M)
        if not first:
            print("REFUSED: no import block found; refusing to guess placement")
            return 1
        new = new[:first.start()] + "import pytest\n" + new[first.start():]
        added_import = 1

    try:
        ast.parse(new)
    except SyntaxError as exc:
        print("REFUSED: patched source does not parse (line %s): %s"
              % (exc.lineno, exc.msg))
        return 1

    if check:
        print("CHECK_ONLY=1")
        print("FUNC_LINE=%d" % (src[:m.start()].count("\n") + 1))
        print("IMPORT_ADDED=%d" % added_import)
        print("PARSES=1")
        print("SHA_BEFORE=%s" % sha12(src))
        print("SHA_AFTER=%s" % sha12(new))
        return 0

    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copyfile(TARGET, os.path.join(BACKUP_DIR, "test_parser_adversarial.py.pre_d4c1"))
    with open(TARGET, "w", encoding="utf-8", newline="") as fh:
        fh.write(new)

    with open(TARGET, "r", encoding="utf-8", newline="") as fh:
        after = fh.read()

    # the assertion must be unchanged, and the decorator must sit on the line
    # immediately above the def
    assertion_intact = '== ["slack.com"]' in after
    lines = after.split("\n")
    idx = next((i for i, l in enumerate(lines) if l.startswith("def " + FUNC)), -1)
    adjacent = idx > 0 and lines[idx - 1].startswith("@pytest.mark.xfail")

    ok = MARKER in after and assertion_intact and adjacent
    print("IMPORT_ADDED=%d" % added_import)
    print("ASSERTION_INTACT=%d" % int(assertion_intact))
    print("DECORATOR_ADJACENT=%d" % int(adjacent))
    print("PARSES=1")
    print("APPLIED=%d" % int(ok))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
