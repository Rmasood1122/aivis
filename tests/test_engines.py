"""Engine adapter tests - OpenAI and Perplexity. All network mocked."""
import httpx
import pytest

from aivis import engines


class FakeResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.text = text
        self.request = httpx.Request("POST", "https://example.invalid/v1")

    def json(self):
        return self._json


def _install_client(monkeypatch, script):
    calls = []

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, json=None, headers=None):
            calls.append({"url": url, "json": json, "headers": headers})
            item = script.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

    monkeypatch.setattr(engines.httpx, "Client", _Client)
    return calls


def _install_sleep(monkeypatch):
    waits = []
    monkeypatch.setattr(engines, "_backoff", lambda a: waits.append(a))
    return waits


OPENAI_OK = {
    "choices": [{"message": {"role": "assistant", "content": "answer text"}}],
    "model": "gpt-4o-2026-01-01",
    "usage": {"prompt_tokens": 5, "completion_tokens": 2},
}

PPLX_OK = {
    "choices": [{"message": {"role": "assistant", "content": "pplx answer"}}],
    "model": "sonar",
    "citations": ["https://a.example", "https://b.example"],
    "usage": {"total_tokens": 9},
}


def test_registry_shape():
    assert set(engines.ENGINES) == {"anthropic", "openai", "perplexity"}
    assert "copilot" not in engines.ENGINES  # no public API, excluded by design


def test_unknown_engine_refuses():
    with pytest.raises(engines.EngineError, match="Unknown engine"):
        engines.run_once_on("bing", "p")


def test_missing_key_refuses(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(engines, "_api_key", engines._api_key)
    with pytest.raises(engines.EngineError, match="OPENAI_API_KEY not set"):
        engines.run_once_on("openai", "p")


def test_openai_success(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    calls = _install_client(monkeypatch, [FakeResponse(200, OPENAI_OK)])
    r = engines.run_once_on("openai", "the prompt")
    assert r.raw_text == "answer text"
    assert r.model_version_hint == "gpt-4o-2026-01-01"
    assert r.request_payload["engine"] == "openai"
    assert r.request_payload["prompt_text"] == "the prompt"
    assert calls[0]["headers"]["Authorization"] == "Bearer k"


def test_openai_sends_temperature(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    calls = _install_client(monkeypatch, [FakeResponse(200, OPENAI_OK)])
    engines.run_once_on("openai", "p", temperature=0.0)
    assert calls[0]["json"]["temperature"] == 0.0


def test_temperature_none_omitted(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    calls = _install_client(monkeypatch, [FakeResponse(200, OPENAI_OK)])
    r = engines.run_once_on("openai", "p", temperature=None)
    assert "temperature" not in calls[0]["json"]
    assert r.request_payload["temperature"] is None


def test_perplexity_preserves_citations(monkeypatch):
    monkeypatch.setenv("PERPLEXITY_API_KEY", "k")
    _install_client(monkeypatch, [FakeResponse(200, PPLX_OK)])
    r = engines.run_once_on("perplexity", "p")
    assert r.raw_text == "pplx answer"
    assert r.raw_json["citations"] == ["https://a.example", "https://b.example"]
    assert r.request_payload["live_retrieval"] is True


def test_empty_choices_returns_empty_string(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    _install_client(monkeypatch, [FakeResponse(200, {"model": "m"})])
    r = engines.run_once_on("openai", "p")
    assert r.raw_text == ""


def test_null_content_returns_empty_string(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    _install_client(
        monkeypatch,
        [FakeResponse(200, {"choices": [{"message": {"content": None}}]})],
    )
    r = engines.run_once_on("openai", "p")
    assert r.raw_text == ""


def test_retryable_then_success(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    waits = _install_sleep(monkeypatch)
    calls = _install_client(
        monkeypatch, [FakeResponse(429), FakeResponse(200, OPENAI_OK)]
    )
    r = engines.run_once_on("openai", "p")
    assert r.raw_text == "answer text"
    assert len(calls) == 2
    assert waits == [1]


def test_retryable_exhausts(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    waits = _install_sleep(monkeypatch)
    _install_client(
        monkeypatch, [FakeResponse(429), FakeResponse(500), FakeResponse(529)]
    )
    with pytest.raises(engines.EngineError, match="failed after 3 retries"):
        engines.run_once_on("openai", "p")
    assert waits == [1, 2, 3]


def test_non_retryable_raises_immediately(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    waits = _install_sleep(monkeypatch)
    calls = _install_client(monkeypatch, [FakeResponse(401, text="bad key")])
    with pytest.raises(engines.EngineError, match="returned 401"):
        engines.run_once_on("openai", "p")
    assert len(calls) == 1
    assert waits == []


def test_connect_error_retries(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    _install_sleep(monkeypatch)
    calls = _install_client(
        monkeypatch, [httpx.ConnectError("refused"), FakeResponse(200, OPENAI_OK)]
    )
    r = engines.run_once_on("openai", "p")
    assert r.raw_text == "answer text"
    assert len(calls) == 2


def test_anthropic_delegates_to_runner(monkeypatch):
    seen = {}

    def fake_run_once(prompt, *, model, temperature, max_tokens):
        seen.update(
            {"prompt": prompt, "model": model, "temperature": temperature,
             "max_tokens": max_tokens}
        )
        return engines.RunResult(raw_text="claude", raw_json=None, request_payload={})

    monkeypatch.setattr(engines, "run_once", fake_run_once)
    r = engines.run_once_on("anthropic", "p", temperature=0.0)
    assert r.raw_text == "claude"
    # claude-sonnet-5 rejects temperature: the adapter must send None
    assert seen["temperature"] is None
    assert seen["model"] == "claude-sonnet-5"


def test_declared_surface_makes_no_call(monkeypatch):
    _install_client(monkeypatch, [])  # any call would IndexError
    s = engines.declared_surface("perplexity")
    assert s["live_retrieval"] is True
    assert "LIVE web retrieval" in s["surface_note"]
    assert engines.declared_surface("openai")["live_retrieval"] is False
