"""
Runner module — Anthropic Claude API via httpx.

Supports both real API execution and stub mode for offline testing.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import httpx

from .settings import settings

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-5"

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0  # seconds: 2, 4, 8
TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)
RETRYABLE = {429, 500, 502, 503, 529}


@dataclass
class RunResult:
    raw_text: str
    raw_json: dict | None
    request_payload: dict
    model_version_hint: str | None = None
    usage: dict = field(default_factory=dict)


def run_once(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float | None = 0.0,
    max_tokens: int = 2048,
) -> RunResult:
    """
    Execute a single prompt against the Anthropic Messages API.

    Full payload capture for audit trail. Retries on transient
    errors with exponential backoff. Raises after exhausting retries.
    """
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Add it to .env or environment."
        )

    request_body = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }

    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }

    if temperature is not None:
        request_body["temperature"] = temperature

    request_payload = {
        "url": ANTHROPIC_URL,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "prompt_length": len(prompt),
        "prompt_text": prompt,
    }

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                resp = client.post(
                    ANTHROPIC_URL,
                    json=request_body,
                    headers=headers,
                )

            if resp.status_code == 200:
                data = resp.json()
                raw_text = ""
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        raw_text += block.get("text", "")

                return RunResult(
                    raw_text=raw_text,
                    raw_json=data,
                    request_payload=request_payload,
                    model_version_hint=data.get("model"),
                    usage=data.get("usage", {}),
                )

            if resp.status_code in RETRYABLE:
                last_error = httpx.HTTPStatusError(
                    f"HTTP {resp.status_code}",
                    request=resp.request,
                    response=resp,
                )
                _backoff(attempt)
                continue

            # Non-retryable HTTP error
            error_body = ""
            try:
                error_body = resp.text
            except Exception:
                pass
            raise RuntimeError(
                f"Anthropic API returned {resp.status_code}: {error_body}"
            )

        except (
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.PoolTimeout,
        ) as e:
            last_error = e
            _backoff(attempt)
            continue

    raise RuntimeError(
        f"Anthropic API failed after {MAX_RETRIES} retries. Last error: {last_error}"
    )


def run_once_stub(prompt: str) -> RunResult:
    """Stub runner for offline testing. No API key needed."""
    fake = (
        "1. Asana - Excellent task management with timeline views and team "
        "collaboration features (no citation)\n"
        "2. Monday.com - Visual project workflows with customizable dashboards "
        "(no citation)\n"
        "3. ClickUp - All-in-one workspace with docs, goals, and sprint management "
        "(no citation)\n"
        "4. Jira - Industry standard for agile software development teams "
        "(no citation)\n"
        "5. Trello - Simple Kanban boards ideal for lightweight project tracking "
        "(no citation)\n"
        "6. Notion - Flexible docs-first approach with database-powered project views "
        "(no citation)\n"
        "7. Linear - Fast, keyboard-driven issue tracking built for product teams "
        "(no citation)\n"
        "8. Wrike - Enterprise-grade resource management and reporting "
        "(no citation)\n"
        "9. Basecamp - Straightforward project organization without complexity "
        "(no citation)\n"
        "10. Smartsheet - Spreadsheet-style project management with automation "
        "(no citation)\n"
    )
    return RunResult(
        raw_text=fake,
        raw_json=None,
        request_payload={"prompt": prompt, "stub": True},
    )


def _backoff(attempt: int) -> None:
    wait = RETRY_BACKOFF_BASE ** attempt
    time.sleep(wait)
