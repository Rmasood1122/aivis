
# openai_adapter bare-import path (added 2026-09-03)
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src" / "aivis"))

import pytest

@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    """No test ever sees real credentials. Live keys in unit tests are how
    secrets end up printed to terminals (2026-09-05 incident)."""
    for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(var, raising=False)

@pytest.fixture(autouse=True)
def _isolate_secrets(monkeypatch):
    """The settings singleton swallows .env at import, so env isolation alone
    is not enough: null the singleton's keys too. Root cause of the
    2026-09-05 key leak into test output."""
    from aivis.settings import settings
    for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(var, raising=False)
        monkeypatch.setattr(settings, var, None, raising=False)
