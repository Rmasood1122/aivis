"""
Engine adapters - OpenAI and Perplexity, normalised to runner.RunResult.

ADDITIVE MODULE. Nothing in runner.py is modified. Anthropic calls delegate to
runner.run_once so there is exactly one Anthropic implementation.

KNOWN DUPLICATION (B7/G10 class): _post_with_retries below is a SECOND retry
loop; runner.run_once has the first. Correct end state is one shared helper,
which requires editing runner.py under a named "go". Logged, not hidden.

SURFACE DISCIPLINE: every adapter records what it actually sent, including
whether temperature was accepted. Surfaces are NOT pooled - an API surface and
a consumer app are different instruments and the report prints the gap.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

from .runner import (
    MAX_RETRIES,
    RETRYABLE,
    TIMEOUT,
    RunResult,
    _backoff,
    run_once,
)


@dataclass(frozen=True)
class EngineSpec:
    key: str
    label: str
    url: str
    default_model: str
    env_var: str
    supports_temperature: bool
    live_retrieval: bool
    surface_note: str


# NOTE ON MODEL IDS: every default_model below is [UNVERIFIED] and MUST be
# confirmed against the provider's live model list before any measured run.
# A model id quoted from memory is exactly the typer ^0.12.3 lesson.
ENGINES: dict[str, EngineSpec] = {
    "anthropic": EngineSpec(
        key="anthropic",
        label="Claude",
        url="https://api.anthropic.com/v1/messages",
        default_model="claude-sonnet-5",
        env_var="ANTHROPIC_API_KEY",
        supports_temperature=False,  # rejected for claude-sonnet-5; see invariant amendment
        live_retrieval=False,
        surface_note="developer API; no web retrieval, no memory, no system prompt",
    ),
    "openai": EngineSpec(
        key="openai",
        label="ChatGPT (API)",
        url="https://api.openai.com/v1/chat/completions",
        default_model="gpt-4o",
        env_var="OPENAI_API_KEY",
        supports_temperature=True,
        live_retrieval=False,
        surface_note=(
            "developer API, NOT the consumer ChatGPT app. The app adds web "
            "search, memory and a system prompt; results are not comparable "
            "and are never pooled with it."
        ),
    ),
    "perplexity": EngineSpec(
        key="perplexity",
        label="Perplexity",
        url="https://api.perplexity.ai/chat/completions",
        default_model="sonar",
        env_var="PERPLEXITY_API_KEY",
        supports_temperature=True,
        live_retrieval=True,
        surface_note=(
            "performs LIVE web retrieval at answer time. Responses are a "
            "function of the web at the moment of the call, so run timestamps "
            "are load-bearing and re-runs are not expected to reproduce."
        ),
    ),
}

# Copilot is deliberately absent: no public API. Excluded on the report face
# with that reason, per the engine matrix in 10 section 3.


class EngineError(RuntimeError):
    """Raised when an engine call cannot be completed."""


def _api_key(spec: EngineSpec) -> str:
    """Settings first, environment second. Neither present is a hard failure."""
    key = None
    try:
        from .settings import settings

        key = getattr(settings, spec.env_var, None)
    except Exception:  # noqa: BLE001 - settings may not define every engine
        key = None
    key = key or os.environ.get(spec.env_var)
    if not key:
        raise EngineError(f"{spec.env_var} not set. Add it to .env or the environment.")
    return key


def _post_with_retries(url: str, body: dict, headers: dict) -> dict:
    """POST with the same retry semantics as runner.run_once. See DUPLICATION note."""
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                resp = client.post(url, json=body, headers=headers)

            if resp.status_code == 200:
                return resp.json()

            if resp.status_code in RETRYABLE:
                last_error = httpx.HTTPStatusError(
                    f"HTTP {resp.status_code}", request=resp.request, response=resp
                )
                _backoff(attempt)
                continue

            error_body = ""
            try:
                error_body = resp.text
            except Exception:  # noqa: BLE001, S110
                # Best-effort read of the error body for the message below.
                pass
            raise EngineError(f"{url} returned {resp.status_code}: {error_body}")

        except (
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.PoolTimeout,
        ) as e:
            last_error = e
            _backoff(attempt)
            continue

    raise EngineError(
        f"{url} failed after {MAX_RETRIES} retries. Last error: {last_error}"
    )


def _extract_openai_text(data: dict) -> str:
    """OpenAI chat-completions shape. Perplexity is wire-compatible."""
    choices = data.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return message.get("content") or ""


def _run_openai_compatible(
    spec: EngineSpec,
    prompt: str,
    *,
    model: str,
    temperature: float | None,
    max_tokens: int,
) -> RunResult:
    api_key = _api_key(spec)

    body: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }

    temperature_sent: float | None = None
    if temperature is not None and spec.supports_temperature:
        body["temperature"] = temperature
        temperature_sent = temperature

    headers = {
        "Authorization": f"Bearer {api_key}",
        "content-type": "application/json",
    }

    request_payload = {
        "engine": spec.key,
        "url": spec.url,
        "model": model,
        "temperature": temperature_sent,
        "temperature_supported": spec.supports_temperature,
        "max_tokens": max_tokens,
        "live_retrieval": spec.live_retrieval,
        "surface_note": spec.surface_note,
        "prompt_length": len(prompt),
        "prompt_text": prompt,
    }

    data = _post_with_retries(spec.url, body, headers)

    # Perplexity's `citations` / `search_results` are preserved inside raw_json.
    # RunResult is deliberately NOT extended: changing its shape would touch
    # runner.py and every consumer of the evidence row schema.
    return RunResult(
        raw_text=_extract_openai_text(data),
        raw_json=data,
        request_payload=request_payload,
        model_version_hint=data.get("model"),
        usage=data.get("usage", {}) or {},
    )


def run_once_on(
    engine: str,
    prompt: str,
    *,
    model: str | None = None,
    temperature: float | None = 0.0,
    max_tokens: int = 2048,
) -> RunResult:
    """
    Execute one prompt against a named engine.

    Anthropic delegates to runner.run_once - one implementation, not two.
    """
    if engine not in ENGINES:
        raise EngineError(
            f"Unknown engine {engine!r}. Known: {', '.join(sorted(ENGINES))}"
        )

    spec = ENGINES[engine]
    chosen = model or spec.default_model

    if spec.key == "anthropic":
        return run_once(
            prompt,
            model=chosen,
            temperature=temperature if spec.supports_temperature else None,
            max_tokens=max_tokens,
        )

    return _run_openai_compatible(
        spec,
        prompt,
        model=chosen,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def declared_surface(engine: str, model: str | None = None) -> dict:
    """The surface block a report prints. No call made."""
    spec = ENGINES[engine]
    return {
        "engine": spec.key,
        "label": spec.label,
        "model": model or spec.default_model,
        "temperature_supported": spec.supports_temperature,
        "live_retrieval": spec.live_retrieval,
        "surface_note": spec.surface_note,
    }
