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
