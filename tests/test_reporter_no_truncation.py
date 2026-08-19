"""
Contract: the PDF writer loses no characters, and names no other product.

Pins defects D1 and D2. The old reporter drew ln[:120] with no marker, so a
long cap-reason list silently lost its tail in the artifact the customer
receives -- the one place a silent loss is least recoverable.
"""

from __future__ import annotations

import inspect

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from aivis import reporter
from aivis.reporter import (
    BODY_FONT,
    BODY_SIZE,
    LEFT_MARGIN,
    RIGHT_MARGIN,
    write_simple_pdf,
    wrap_text,
)

MAX_WIDTH = letter[0] - LEFT_MARGIN - RIGHT_MARGIN


def _canvas(tmp_path):
    return canvas.Canvas(str(tmp_path / "probe.pdf"), pagesize=letter)


def _rejoin(segments: list[str]) -> str:
    """Reconstruct the source text from wrapped segments, ignoring wrap points."""
    return "".join(segments).replace(" ", "")


# --- D2: no silent truncation ---------------------------------------------


def test_long_line_is_wrapped_not_truncated(tmp_path):
    c = _canvas(tmp_path)
    text = "Cap reasons: " + ", ".join(f"REASON_{i}(0.42)" for i in range(40))
    assert len(text) > 120

    segments = wrap_text(c, text, BODY_FONT, BODY_SIZE, MAX_WIDTH)

    assert len(segments) > 1
    assert _rejoin(segments) == text.replace(" ", "")


def test_every_segment_fits_the_page_width(tmp_path):
    c = _canvas(tmp_path)
    text = "x" * 40 + " " + "y" * 400 + " tail"
    for seg in wrap_text(c, text, BODY_FONT, BODY_SIZE, MAX_WIDTH):
        assert c.stringWidth(seg, BODY_FONT, BODY_SIZE) <= MAX_WIDTH


def test_unbreakable_token_is_split_not_dropped(tmp_path):
    c = _canvas(tmp_path)
    token = "A" * 1000
    segments = wrap_text(c, token, BODY_FONT, BODY_SIZE, MAX_WIDTH)
    assert "".join(segments) == token


def test_short_line_is_left_alone(tmp_path):
    c = _canvas(tmp_path)
    assert wrap_text(c, "Runs: 5", BODY_FONT, BODY_SIZE, MAX_WIDTH) == ["Runs: 5"]


def test_empty_line_is_preserved_as_a_blank(tmp_path):
    c = _canvas(tmp_path)
    assert wrap_text(c, "", BODY_FONT, BODY_SIZE, MAX_WIDTH) == [""]


def _record_drawn(monkeypatch) -> list[str]:
    """Capture every string the PDF writer actually draws on the page."""
    drawn: list[str] = []
    original = canvas.Canvas.drawString

    def spy(self, x, y, text, *args, **kwargs):
        drawn.append(text)
        return original(self, x, y, text, *args, **kwargs)

    monkeypatch.setattr(canvas.Canvas, "drawString", spy)
    return drawn


def test_nothing_is_lost_between_input_lines_and_drawn_output(tmp_path, monkeypatch):
    """The D2 regression, measured on the artifact rather than on the source."""
    drawn = _record_drawn(monkeypatch)
    long_line = "Cap reasons: " + ", ".join(f"LIST_STABILITY_HARD_{i}(0.31)" for i in range(30))
    assert len(long_line) > 120

    write_simple_pdf(tmp_path / "r.pdf", "AI Visibility Smoke Report", [long_line])

    rendered = "".join(drawn).replace(" ", "")
    assert long_line.replace(" ", "") in rendered


# --- D1: no foreign product name ------------------------------------------


def test_no_other_product_is_named_on_the_page(tmp_path, monkeypatch):
    drawn = _record_drawn(monkeypatch)
    write_simple_pdf(tmp_path / "r.pdf", "AI Visibility Smoke Report", ["Prompt: PM-D01"])
    page_text = " ".join(drawn)
    assert "PCOS" not in page_text
    assert "AI Visibility" in page_text


def test_caller_can_override_the_subtitle(tmp_path, monkeypatch):
    drawn = _record_drawn(monkeypatch)
    write_simple_pdf(
        tmp_path / "r.pdf",
        "AI Visibility Smoke Report",
        ["Prompt: PM-D01"],
        subtitle="Acme Corp - Confidential",
    )
    assert "Acme Corp - Confidential" in " ".join(drawn)


def test_subtitle_defaults_to_this_product_and_is_overridable(tmp_path):
    sig = inspect.signature(write_simple_pdf)
    assert "subtitle" in sig.parameters
    assert sig.parameters["subtitle"].default is None
    assert "AI Visibility" in reporter.PRODUCT_NAME


# --- the writer still produces a file --------------------------------------


def test_write_simple_pdf_produces_a_nonempty_pdf(tmp_path):
    out = tmp_path / "reports" / "r.pdf"
    write_simple_pdf(out, "AI Visibility Smoke Report", ["Prompt: PM-D01", "z" * 600])
    assert out.exists()
    assert out.stat().st_size > 0
    assert out.read_bytes()[:5] == b"%PDF-"
