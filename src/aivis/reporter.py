from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# D1 fix. The header line used to read "PCOS Visibility Engine - Audit Report",
# which is a different product. The name now lives in one constant and the
# caller may override the whole subtitle.
PRODUCT_NAME = "AI Visibility Audit"

LEFT_MARGIN = 72.0
RIGHT_MARGIN = 72.0
TOP_MARGIN = 72.0
BOTTOM_MARGIN = 72.0

TITLE_FONT = "Helvetica-Bold"
TITLE_SIZE = 16.0
SUBTITLE_FONT = "Helvetica"
SUBTITLE_SIZE = 9.0
BODY_FONT = "Helvetica"
BODY_SIZE = 10.0
LINE_HEIGHT = 14.0


def _max_prefix_chars(c, word: str, font: str, size: float, max_width: float) -> int:
    """Largest n such that word[:n] fits in max_width. Always returns >= 1."""
    lo, hi = 1, len(word)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if c.stringWidth(word[:mid], font, size) <= max_width:
            lo = mid
        else:
            hi = mid - 1
    return lo


def wrap_text(c, text: str, font: str, size: float, max_width: float) -> list[str]:
    """
    Wrap `text` to `max_width` without losing a character.

    D2 fix. The previous implementation drew ln[:120] and silently discarded
    everything past 120 characters, so a long cap-reason list or a long brand
    name vanished from the customer's PDF with no marker that anything was
    missing. This function never discards: a word too long to fit on a line of
    its own is hard-split across lines instead of truncated.
    """
    if text == "":
        return [""]

    out: list[str] = []
    cur = ""

    for word in text.split(" "):
        candidate = word if cur == "" else cur + " " + word
        if c.stringWidth(candidate, font, size) <= max_width:
            cur = candidate
            continue

        if cur != "":
            out.append(cur)
            cur = ""

        while word != "" and c.stringWidth(word, font, size) > max_width:
            n = _max_prefix_chars(c, word, font, size, max_width)
            out.append(word[:n])
            word = word[n:]

        cur = word

    if cur != "" or not out:
        out.append(cur)

    return out


def write_simple_pdf(
    path: Path,
    title: str,
    lines: list[str],
    subtitle: str | None = None,
) -> None:
    """
    Write a simple PDF report.

    D1: the subtitle is a parameter with a correct default, not a hardcoded
        foreign product name.
    D2: every line wraps; nothing is truncated.
    """
    subtitle_text = subtitle if subtitle is not None else f"{PRODUCT_NAME} - Audit Report"

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    max_width = width - LEFT_MARGIN - RIGHT_MARGIN
    y = height - TOP_MARGIN

    c.setFont(TITLE_FONT, TITLE_SIZE)
    for seg in wrap_text(c, title, TITLE_FONT, TITLE_SIZE, max_width):
        c.drawString(LEFT_MARGIN, y, seg)
        y -= TITLE_SIZE + 6.0
    y -= 12.0

    c.setFont(SUBTITLE_FONT, SUBTITLE_SIZE)
    for seg in wrap_text(c, subtitle_text, SUBTITLE_FONT, SUBTITLE_SIZE, max_width):
        c.drawString(LEFT_MARGIN, y, seg)
        y -= SUBTITLE_SIZE + 5.0
    y -= 8.0

    c.line(LEFT_MARGIN, y, width - RIGHT_MARGIN, y)
    y -= 20.0

    c.setFont(BODY_FONT, BODY_SIZE)
    for ln in lines:
        for seg in wrap_text(c, str(ln), BODY_FONT, BODY_SIZE, max_width):
            if y < BOTTOM_MARGIN:
                c.showPage()
                c.setFont(BODY_FONT, BODY_SIZE)
                y = height - TOP_MARGIN
            c.drawString(LEFT_MARGIN, y, seg)
            y -= LINE_HEIGHT

    c.save()
