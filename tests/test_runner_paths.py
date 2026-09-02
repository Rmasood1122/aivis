"""Runner error/retry/timeout paths — 13 battery item 4. All network mocked."""
from types import SimpleNamespace

import httpx
import pytest

from aivis import runner


def _patch_key(monkeypatch, value="test-key"):
    monkeypatch.setattr(runner, "settings", SimpleNamespace(ANTHROPIC_API_KEY=value))


class FakeResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.text = text
        self.request = httpx.Request("POST", runner.ANTHROPIC_URL)

    def json(self):
        return self._json


def _install_client(monkeypatch, script):
    """script: FakeResponse or Exception per post(), consumed in order."""
    calls = []

    class _Client:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False

        def post(self, url, json=None, headers=None):
            calls.append({"url": url, "json": json, "headers": headers})
            item = script.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

    monkeypatch.setattr(runner.httpx, "Client", _Client)
    return calls


def _install_sleep(monkeypatch):
    waits = []
    monkeypatch.setattr(runner.time, "sleep", lambda s: waits.append(s))
    return waits


OK_JSON = {
    "content": [
        {"type": "text", "text": "hello "},
        {"type": "tool_use", "id": "x"},
        {"type": "text", "text": "world"},
    ],
    "model": "claude-sonnet-5-20260901",
    "usage": {"input_tokens": 3, "output_tokens": 2},
}


def test_missing_key_raises(monkeypatch):
    _patch_key(monkeypatch, value=None)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY not set"):
        runner.run_once("p")


def test_success_concatenates_text_blocks(monkeypatch):
    _patch_key(monkeypatch)
    calls = _install_client(monkeypatch, [FakeResponse(200, OK_JSON)])
    r = runner.run_once("the prompt")
    assert r.raw_text == "hello world"
    assert r.model_version_hint == "claude-sonnet-5-20260901"
    assert r.usage == {"input_tokens": 3, "output_tokens": 2}
    assert r.request_payload["prompt_text"] == "the prompt"
    assert len(calls) == 1


def test_default_temperature_sent(monkeypatch):
    _patch_key(monkeypatch)
    calls = _install_client(monkeypatch, [FakeResponse(200, OK_JSON)])
    runner.run_once("p")
    assert calls[0]["json"]["temperature"] == 0.0


def test_temperature_none_omitted(monkeypatch):
    _patch_key(monkeypatch)
    calls = _install_client(monkeypatch, [FakeResponse(200, OK_JSON)])
    runner.run_once("p", temperature=None)
    assert "temperature" not in calls[0]["json"]


def test_retryable_then_success(monkeypatch):
    _patch_key(monkeypatch)
    waits = _install_sleep(monkeypatch)
    calls = _install_client(monkeypatch, [FakeResponse(429), FakeResponse(200, OK_JSON)])
    r = runner.run_once("p")
    assert r.raw_text == "hello world"
    assert len(calls) == 2
    assert waits == [2.0]


def test_retryable_exhausts_and_raises(monkeypatch):
    _patch_key(monkeypatch)
    waits = _install_sleep(monkeypatch)
    calls = _install_client(
        monkeypatch, [FakeResponse(429), FakeResponse(500), FakeResponse(529)]
    )
    with pytest.raises(RuntimeError, match="failed after 3 retries"):
        runner.run_once("p")
    assert len(calls) == 3
    assert waits == [2.0, 4.0, 8.0]


def test_non_retryable_raises_immediately(monkeypatch):
    _patch_key(monkeypatch)
    waits = _install_sleep(monkeypatch)
    calls = _install_client(monkeypatch, [FakeResponse(400, text='{"error":"bad"}')])
    with pytest.raises(RuntimeError, match="returned 400"):
        runner.run_once("p")
    assert len(calls) == 1
    assert waits == []


def test_connect_error_retries_then_success(monkeypatch):
    _patch_key(monkeypatch)
    _install_sleep(monkeypatch)
    calls = _install_client(
        monkeypatch, [httpx.ConnectError("refused"), FakeResponse(200, OK_JSON)]
    )
    r = runner.run_once("p")
    assert r.raw_text == "hello world"
    assert len(calls) == 2


def test_read_timeout_exhausts(monkeypatch):
    _patch_key(monkeypatch)
    waits = _install_sleep(monkeypatch)
    _install_client(
        monkeypatch,
        [httpx.ReadTimeout("t"), httpx.ReadTimeout("t"), httpx.ReadTimeout("t")],
    )
    with pytest.raises(RuntimeError, match="Last error"):
        runner.run_once("p")
    assert waits == [2.0, 4.0, 8.0]


def test_stub_ignores_prompt_and_marks_itself():
    a = runner.run_once_stub("alpha")
    b = runner.run_once_stub("completely different prompt")
    assert a.raw_text == b.raw_text  # constant output — A07's documented property
    assert a.request_payload.get("stub") is True
    assert a.raw_json is None


def test_backoff_is_exponential(monkeypatch):
    waits = _install_sleep(monkeypatch)
    runner._backoff(1)
    runner._backoff(2)
    runner._backoff(3)
    assert waits == [2.0, 4.0, 8.0]
