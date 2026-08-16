from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def write_simple_pdf(path: Path, title: str, lines: list[str]) -> None:
    """Write a simple PDF report. MVP — will be replaced with full template."""
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    y = height - 72

    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, title)
    y -= 30

    c.setFont("Helvetica", 9)
    c.drawString(72, y, "PCOS Visibility Engine — Audit Report")
    y -= 20
    c.line(72, y, width - 72, y)
    y -= 20

    c.setFont("Helvetica", 10)
    for ln in lines:
        if y < 72:
            c.showPage()
            y = height - 72
            c.setFont("Helvetica", 10)
        c.drawString(72, y, ln[:120])
        y -= 14

    c.save()
