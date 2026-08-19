"""
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
    got = extract_domains("Source: alpha.com\n\nbeta.com is also popular.")
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
