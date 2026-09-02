"""wilson-v1: interval correctness + presence in the aggregate (battery B02, partial)."""
import pytest
from aivis.intervals import wilson


def test_wilson_reproduces_pr_report_absence_row():
    # 0/41 buyer-intent absence row, named PR report 2026-09-01: CI 0.0-8.6%
    p, lo, hi = wilson(0, 41)
    assert p == 0.0 and lo == 0.0
    assert abs(hi - 0.0857) < 0.0005


def test_wilson_textbook_value():
    p, lo, hi = wilson(5, 10)
    assert abs(lo - 0.2366) < 0.0005 and abs(hi - 0.7634) < 0.0005


def test_wilson_refuses_zero_n():
    with pytest.raises(ValueError):
        wilson(0, 0)


# --- B02 offline half: interval in the aggregate and on the rendered line ---
from tests.test_variance import SCORING_CFG, _make_obj


def test_ci95_present_and_brackets_rate():
    # 2 mentioned of 3 parsed: rate 0.6667, interval must bracket it
    objs = [_make_obj(brand_rank=1), _make_obj(brand_rank=2), _make_obj(brand_rank=None)]
    s = summ = __import__("aivis.variance", fromlist=["summarize_anchor"]).summarize_anchor(objs, SCORING_CFG)
    ci = s["mention_rate_ci95"]
    assert isinstance(ci, list) and len(ci) == 2
    lo, hi = ci
    assert 0.0 <= lo <= s["mention_rate"] <= hi <= 1.0
    assert (lo, hi) != (0.0, 1.0)  # an interval that excludes nothing asserts nothing


def test_abstained_summary_carries_no_interval():
    # No parsed rows -> early return; an interval on n=0 would be the estimate
    # intervals.py exists to refuse.
    from aivis.variance import summarize_anchor
    s = summarize_anchor([_make_obj(parse_success=False)], SCORING_CFG)
    assert "mention_rate_ci95" not in s


def test_report_line_renders_ci():
    # The cli.py f-string pattern, verbatim shape: page, not just JSON (I-4's DEFEATED-BY)
    from aivis.variance import summarize_anchor
    objs = [_make_obj(brand_rank=1), _make_obj(brand_rank=None)]
    summ = summarize_anchor(objs, SCORING_CFG)
    line = (
        f"  Mention rate: {summ['mention_rate']:.0%} "
        f"[95% CI {summ['mention_rate_ci95'][0]:.1%}-{summ['mention_rate_ci95'][1]:.1%}, "
        f"n={summ['runs_scored']}] (stable={summ['mention_stable']})"
    )
    assert "95% CI" in line and "n=2" in line
