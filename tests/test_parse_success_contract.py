"""
Contract tests for aivis.parser.parse_tool_list metadata.

Derived from src/aivis/parser.py lines 134-173. Two properties, both read
directly from the source, neither previously asserted anywhere:

  N2  parse_success (line 169) checks only `rank` and `name_raw`. PE-03 and
      PE-04 append to parse_errors and do NOT continue, so their entries stay
      in tool_list. A parse therefore reports success while carrying errors.

  CIT lines 145-148 zero out citation_domains for the whole line whenever the
      substring "no citation" appears anywhere in it, regardless of what the
      hedge actually refers to.
"""
import pytest
from aivis.parser import parse_tool_list

DUP = ("1. Asana - Good for sprint planning\n"
       "2. Notion - Good for docs\n"
       "3. Asana - Duplicate on purpose\n")


def test_duplicate_raises_pe04():
    _, meta = parse_tool_list(DUP)
    assert "PE-04" in meta["parse_errors"]


def test_parse_success_is_true_while_errors_exist():
    """Characterisation: this passes today. It is the bug, pinned."""
    _, meta = parse_tool_list(DUP)
    assert meta["parse_errors"] != []
    assert meta["parse_success"] is True


@pytest.mark.xfail(strict=True,
                   reason="BUG N2: parse_success (line 169) ignores parse_errors entirely")
def test_parse_success_should_be_false_when_errors_exist():
    _, meta = parse_tool_list(DUP)
    assert meta["parse_success"] is False


def test_no_citation_phrase_is_unscoped():
    """The hedge is about a figure; the rule deletes an unrelated real domain."""
    raw = "1. Asana - see asana.com, but I have no citation for the 2024 figure\n"
    tools, _ = parse_tool_list(raw)
    assert tools[0].citation_domains == ["asana.com"]
