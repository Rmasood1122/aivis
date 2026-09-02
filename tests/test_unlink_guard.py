"""guards-v1: smoke refuses to overwrite an existing evidence file (B1, battery A04)."""
from pathlib import Path
from typer.testing import CliRunner
from aivis.cli import app

runner = CliRunner()


def test_smoke_refuses_existing_out(tmp_path: Path):
    existing = tmp_path / "smoke_runs.jsonl"
    existing.write_text('{"sentinel": true}\n', encoding="utf-8")
    result = runner.invoke(app, ["smoke", "--out", str(existing)])
    assert result.exit_code != 0
    assert existing.read_text(encoding="utf-8") == '{"sentinel": true}\n'  # untouched
