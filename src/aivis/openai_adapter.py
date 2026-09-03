"""aivis engine adapter: OpenAI developer API (chat.completions).

SURFACE DECLARATION (printed on every row and every report):
  This measures the OpenAI *developer API*, not the consumer ChatGPT app.
  The consumer app adds search, memory and system context the API does not.
  Rows from this surface are never pooled or compared with consumer-app data.

Invariants honoured (source: aivis docs 03/08/13 ledgers):
  - sha256 is computed over response_text alone (03 Part A).
  - An engine error produces NO row; the failure is raised and logged by the
    caller so counts reconcile (C11, D0).
  - The API key appears in the Authorization header only — never in
    request_payload, never anywhere in the stored row (K05).
  - Every HTTP call carries a timeout; retries are bounded with backoff+jitter;
    auth errors fail fast without retry (J01, J02).
  - Timestamps are UTC ISO8601 (J10).
  - Parameters the API rejects (temperature, max_tokens on newer models) are
    omitted and DECLARED per-row in param_adaptations — the session-6
    temperature invariant, generalised.

Stdlib only. New file; integration into cli.py/runner.py needs a named "go".
"""

from __future__ import annotations

import hashlib
import io
import json
import random
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
SURFACE = (
    "openai developer API (chat.completions) — consumer ChatGPT app adds "
    "search/memory; surfaces are not comparable and are never pooled"
)
FAST_FAIL_CODES = {401, 403, 404}
RETRY_CODES = {429, 500, 502, 503, 529}
MAX_PARAM_ADAPTATIONS = 2  # bounded: temperature drop + max_tokens rename


class EngineError(RuntimeError):
    """Raised when no valid response was obtained. NO evidence row exists."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _post(body: dict, api_key: str, timeout: float) -> tuple[dict, str]:
    """One HTTP attempt. Returns (parsed_json, request_id_header)."""
    req = urllib.request.Request(
        OPENAI_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",  # header only; never stored
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        req_id = resp.headers.get("x-request-id", "")
    return json.loads(raw), req_id


def _error_body(err: urllib.error.HTTPError) -> str:
    try:
        return err.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def run_once_openai(
    prompt: str,
    model: str,
    api_key: str,
    *,
    prompt_id: str = "",
    bank_version: str = "",
    temperature: float | None = 0.0,
    max_tokens: int = 2048,
    timeout: float = 60.0,
    max_retries: int = 3,
    backoff_base: float = 1.0,
    _sleep=time.sleep,
) -> dict:
    """Run one prompt once. Returns a complete evidence row, or raises
    EngineError (in which case no row exists anywhere — C11)."""
    body: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }
    if temperature is not None:
        body["temperature"] = temperature

    adaptations: list[str] = []
    attempt = 0
    while True:
        try:
            data, req_id = _post(body, api_key, timeout)
            break
        except urllib.error.HTTPError as err:
            detail = _error_body(err)
            if err.code == 400 and len(adaptations) < MAX_PARAM_ADAPTATIONS:
                # Parameter-rejection adaptation: omit and DECLARE, never
                # silently default (session-6 temperature invariant).
                if "temperature" in detail and "temperature" in body:
                    del body["temperature"]
                    adaptations.append("temperature omitted (api_rejected)")
                    continue
                if "max_tokens" in detail and "max_tokens" in body:
                    body["max_completion_tokens"] = body.pop("max_tokens")
                    adaptations.append(
                        "max_tokens renamed max_completion_tokens (api_rejected)"
                    )
                    continue
            if err.code in FAST_FAIL_CODES:
                raise EngineError(
                    f"HTTP {err.code} (no retry): {detail[:400]}"
                ) from err
            if err.code in RETRY_CODES and attempt < max_retries:
                attempt += 1
                _sleep(backoff_base * (2 ** (attempt - 1)) + random.random())
                continue
            raise EngineError(f"HTTP {err.code}: {detail[:400]}") from err
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            if attempt < max_retries:
                attempt += 1
                _sleep(backoff_base * (2 ** (attempt - 1)) + random.random())
                continue
            raise EngineError(f"transport failure: {err}") from err

    try:
        response_text = data["choices"][0]["message"]["content"]
        if not isinstance(response_text, str) or not response_text:
            raise KeyError("empty content")
    except (KeyError, IndexError, TypeError) as err:
        # A 200 with no usable text is a failure, not a row (D0's lesson:
        # check the content, never the status).
        raise EngineError(f"malformed 200 response: {err}") from err

    declared_temperature = (
        "omitted (api_rejected)"
        if "temperature" not in body
        else body["temperature"]
    )
    return {
        "engine": "openai",
        "surface": SURFACE,
        "model": data.get("model", model),  # served model, from the response
        "model_requested": model,
        "temperature": declared_temperature,
        "param_adaptations": adaptations,
        "ts": _utc_now(),
        "request_id": req_id or data.get("id", ""),
        "prompt_id": prompt_id,
        "bank_version": bank_version,
        "request_payload": dict(body),  # JSON body only — no auth header (K05)
        "response_text": response_text,
        "sha256": hashlib.sha256(response_text.encode("utf-8")).hexdigest(),
        "usage": data.get("usage", {}),  # kept raw for C02 unit-cost measurement
    }
