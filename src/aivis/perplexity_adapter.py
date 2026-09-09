"""aivis engine adapter: Perplexity Sonar API (chat.completions surface).

SURFACE DECLARATION (printed on every row and every report):
  This measures the Perplexity Sonar API, chat.completions endpoint —
  vendor-marked LEGACY as of 2026-09 (migration target: their Agent API)
  [REPORTED: docs.perplexity.ai, 2026-09-05].
  This surface is RETRIEVAL-AUGMENTED: answers are grounded in a live web
  search at request time. Rows from this surface are NEVER pooled or compared
  with parametric-API surfaces (OpenAI/Anthropic developer APIs) or with the
  Perplexity consumer app.

Invariants honoured (source: aivis docs 03/08/13 ledgers):
  - sha256 is computed over response_text alone (03 Part A) — the existing
    verify_evidence.py runs on these rows unchanged.
  - An engine error produces NO row; the failure is raised and logged by the
    caller so counts reconcile (C11, D0).
  - The API key appears in the Authorization header only — never in
    request_payload, never anywhere in the stored row (K05).
  - Every HTTP call carries a timeout; retries are bounded with backoff+jitter;
    auth errors fail fast without retry (J01, J02).
  - Timestamps are UTC ISO8601 (J10).
  - Parameters the API rejects are omitted and DECLARED per-row in
    param_adaptations — the session-6 temperature invariant, generalised.
  - HTTP error bodies are READ and carried in the raised message — the
    empty-body error reader the OpenAI adapter still lacks (ledger item).

NEW ON THIS SURFACE ONLY:
  - citations and search_results are stored per row exactly as returned;
    absence is stored as an empty list, never fabricated.
  - usage (including Perplexity's per-request cost block) is stored raw per
    row. C02 unit cost for this engine is READ from rows, never estimated.

Stdlib only. New file; integration into cli.py/runner.py needs a named "go".
"""

from __future__ import annotations

import hashlib
import json
import random
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
SURFACE = (
    "perplexity sonar API (chat.completions, vendor-marked legacy 2026-09) — "
    "RETRIEVAL-AUGMENTED, grounded in live web search at request time; never "
    "pooled with parametric-API surfaces or the consumer app"
)
FAST_FAIL_CODES = {401, 403, 404}
RETRY_CODES = {429, 500, 502, 503, 529}
MAX_PARAM_ADAPTATIONS = 2  # bounded: temperature drop + max_tokens drop
DROPPABLE_PARAMS = ("temperature", "max_tokens")


class EngineError(RuntimeError):
    """Engine could not produce a clean response. NO row is written."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _post(body: dict, api_key: str, timeout: float) -> tuple[dict, str]:
    req = urllib.request.Request(
        PERPLEXITY_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        req_id = resp.headers.get("x-request-id", "") or ""
    return json.loads(raw), req_id


def _error_body(err: urllib.error.HTTPError) -> str:
    """Read the error body; an unreadable body is reported as such, never
    silently dropped (the adapter empty-body ledger item, closed here)."""
    try:
        text = err.read().decode("utf-8", errors="replace")
        return text if text.strip() else "<empty error body>"
    except Exception as read_err:  # noqa: BLE001 - reported, not swallowed
        return f"<unreadable error body: {read_err!r}>"


def _dropped_param(status: int, body_text: str, payload: dict) -> str:
    """If a 400 names a droppable param still present in the payload, return
    its name; else empty string."""
    if status != 400:
        return ""
    lowered = body_text.lower()
    for name in DROPPABLE_PARAMS:
        if name in payload and name in lowered:
            return name
    return ""


def run_once_perplexity(
    prompt_text: str,
    model: str,
    api_key: str,
    temperature: float | None = 0.0,
    max_tokens: int | None = 2048,
    timeout: float = 120.0,
    max_retries: int = 4,
) -> dict:
    """One prompt, one clean row — or EngineError and no row at all."""
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt_text}],
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    adaptations: list[str] = []
    attempt = 0
    while True:
        try:
            data, req_id = _post(payload, api_key, timeout)
            break
        except urllib.error.HTTPError as err:
            body_text = _error_body(err)
            dropped = _dropped_param(err.code, body_text, payload)
            if dropped and len(adaptations) < MAX_PARAM_ADAPTATIONS:
                del payload[dropped]
                adaptations.append(
                    f"dropped {dropped}: API rejected it "
                    f"(HTTP 400: {body_text[:160]})"
                )
                continue
            if err.code in FAST_FAIL_CODES:
                raise EngineError(
                    f"fast-fail HTTP {err.code}: {body_text[:400]}"
                ) from err
            if err.code in RETRY_CODES and attempt < max_retries:
                attempt += 1
                delay = min(2.0**attempt, 30.0) + random.uniform(0.0, 1.0)
                time.sleep(delay)
                continue
            raise EngineError(
                f"HTTP {err.code} after {attempt} retries: {body_text[:400]}"
            ) from err
        except (urllib.error.URLError, TimeoutError) as err:
            if attempt < max_retries:
                attempt += 1
                delay = min(2.0**attempt, 30.0) + random.uniform(0.0, 1.0)
                time.sleep(delay)
                continue
            raise EngineError(
                f"transport failure after {attempt} retries: {err!r}"
            ) from err

    try:
        response_text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as err:
        raise EngineError(
            f"response missing choices[0].message.content: "
            f"{json.dumps(data)[:400]}"
        ) from err
    if not isinstance(response_text, str) or not response_text:
        raise EngineError("empty or non-text response — no row written")

    return {
        "ts": _utc_now(),
        "engine": "perplexity",
        "surface": SURFACE,
        "model": data.get("model", "") or model,
        "model_requested": model,
        "temperature": payload.get("temperature"),
        "param_adaptations": adaptations,
        "request_payload": payload,
        "request_id": str(data.get("id", "")) or req_id,
        "response_text": response_text,
        "sha256": hashlib.sha256(response_text.encode("utf-8")).hexdigest(),
        "citations": data.get("citations") or [],
        "search_results": data.get("search_results") or [],
        "usage": data.get("usage") or {},
    }
