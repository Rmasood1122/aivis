"""The suite must test the checkout it is run from.

With two git worktrees and one `pip install -e`, pytest in the second worktree imported the
first worktree's `aivis` (2026-10-07, aivis-restaurant: ImportError on aivis.engine_select,
and before that every plain pytest run there silently tested another folder's code).
`pythonpath = ["src"]` in pyproject.toml fixes it; this test fails if that line is removed
while an editable install points somewhere else.
"""
from pathlib import Path

import aivis

ROOT = Path(__file__).resolve().parents[1]


def test_aivis_is_imported_from_this_checkout():
    imported = Path(aivis.__file__).resolve()
    assert imported.is_relative_to(ROOT / "src"), (
        f"tests are running against {imported}, not this checkout ({ROOT / 'src'})"
    )
