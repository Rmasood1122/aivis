"""
Vertical classification for names the vertical map does not list.

ADDITIVE MODULE. The map (config/vertical_map_v1.json) stays first: a listed
vertical never reaches this module's model call.

Order for any typed business or vertical:
  1. vertical map, exact key or alias          -> VERTICAL_MAP
  2. classification ledger, same name as before -> MODEL_CLASSIFIED (no call)
  3. one model call, answer appended to ledger  -> MODEL_CLASSIFIED
  4. no key, call failed, unreadable or
     "unknown" answer                           -> VERTICAL_UNCLASSIFIED (mixed)

DISCIPLINE:
  - A model answer is evidence, so it is kept like evidence: the ledger row
    stores the raw response text and its SHA-256, and a row whose stored
    audience does not match its own stored response is refused on read.
  - The ledger is append-only and first-row-wins. To correct a model answer,
    add a row to the vertical map; the map outranks the ledger.
  - The model call is injected (`call`), so tests never touch the network.
  - A failed or unreadable classification is never turned into b2c or b2b.
    It falls back to the map's declared `unclassified` row and says why.
  - This is NOT a measurement call. It decides which engines a study will
    call; it produces no visibility number.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from .engine_select import (
    AUDIENCE_FROM_MAP,
    AUDIENCE_UNCLASSIFIED,
    BASE_AUDIENCES,
    Classification,
    SelectionError,
    classify_vertical,
)

AUDIENCE_FROM_CLASSIFIER = "MODEL_CLASSIFIED"
PROMPT_VERSION = "vertical_classify_prompt_v1"
UNKNOWN = "unknown"
ANSWERS = (*BASE_AUDIENCES, "mixed", UNKNOWN)

PROMPT_V1 = """\
Classify who asks an AI assistant for recommendations about this kind of business.

Business: "{name}"

Answer with one JSON object and nothing else:
{{"audience": "b2c" | "b2b" | "mixed" | "unknown", "local": true | false}}

audience:
- "b2c": the buyers are members of the public.
- "b2b": the buyers are businesses, or professionals buying for their work.
- "mixed": both kinds of buyer are common.
- "unknown": the text is not a kind of business, or you cannot tell.
local: true when buyers usually look for a provider near them (a city, a
neighbourhood or a region); otherwise false.
"""

# (text, model id) <- prompt
ClassifierCall = Callable[[str], tuple[str, str]]


class ClassifyError(ValueError):
    """The model's answer could not be read as a classification."""


def build_prompt(name: str) -> str:
    return PROMPT_V1.format(name=name.replace('"', "'").strip())


def parse_classification(text: str) -> tuple[str, bool]:
    """Strict: one JSON object with a known audience and a boolean local."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ClassifyError(f"no JSON object in answer: {text[:80]!r}")
    try:
        obj = json.loads(text[start:end + 1])
    except json.JSONDecodeError as ex:
        raise ClassifyError(f"answer is not valid JSON: {text[:80]!r}") from ex
    audience, local = obj.get("audience"), obj.get("local")
    if audience not in ANSWERS:
        raise ClassifyError(f"audience {audience!r} is not one of {ANSWERS}")
    if not isinstance(local, bool):
        raise ClassifyError(f"local {local!r} is not true or false")
    return audience, local


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_ledger(path: str | Path) -> dict[str, dict]:
    """
    name -> first ledger row for that name. A missing file is an empty ledger.

    Every row is re-checked against its own stored response. A row that was
    edited after the fact is a refused ledger, not a skipped row.
    """
    p = Path(path)
    if not p.exists():
        return {}
    rows: dict[str, dict] = {}
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        where = f"{p.name} line {n}"
        if _sha256(row["response_text"]) != row["sha256"]:
            raise SelectionError(f"{where}: sha256 does not match response_text")
        if parse_classification(row["response_text"]) != (row["audience"], row["local"]):
            raise SelectionError(f"{where}: stored audience/local differ from the stored response")
        rows.setdefault(row["name"], row)
    return rows


def _append(path: str | Path, row: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _from_row(base: Classification, row: dict, vmap: dict, how: str) -> Classification:
    record = {
        "ledger_name": row["name"],
        "classifier_engine": row["classifier_engine"],
        "classifier_model": row["classifier_model"],
        "prompt_version": row["prompt_version"],
        "response_sha256": row["sha256"],
        "classified_at": row["ts"],
    }
    if row["audience"] == UNKNOWN:
        return replace(
            base, record=record,
            note=(f"{base.vertical!r}: the classifier answered \"unknown\" ({how}); treated as "
                  f"{vmap['unclassified']['audience']}. Add a map row or pass --audience."),
        )
    return replace(
        base, audience=row["audience"], local=row["local"], source=AUDIENCE_FROM_CLASSIFIER,
        record=record,
        note=(f"{base.vertical!r} is not in {vmap['map_version']}; {row['classifier_model']} "
              f"answered {row['audience']}, local={row['local']} ({how}). Model answer, "
              "not operator-reviewed."),
    )


def resolve_vertical(
    name: str,
    vmap: dict,
    *,
    ledger_path: str | Path,
    call: ClassifierCall | None,
    engine: str = "anthropic",
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Classification:
    """Map first, then ledger, then one model call. `call=None` turns the call off."""
    base = classify_vertical(name, vmap)
    if base.source == AUDIENCE_FROM_MAP:
        return base

    ledger = read_ledger(ledger_path)
    if base.vertical in ledger:
        return _from_row(base, ledger[base.vertical], vmap, "from the ledger, no call made")

    if call is None:
        return replace(base, note=base.note + " Classifier is off.")

    prompt = build_prompt(name)
    try:
        text, model = call(prompt)
    except Exception as ex:  # noqa: BLE001 - any failure must fall back, visibly
        return replace(base, note=base.note + f" Classifier call failed: {str(ex)[:160]}")
    try:
        audience, local = parse_classification(text)
    except ClassifyError as ex:
        return replace(base, note=base.note + f" Classifier answer unreadable: {ex}")

    row = {
        "ts": now().isoformat(),
        "name": base.vertical,
        "given": name,
        "audience": audience,
        "local": local,
        "classifier_engine": engine,
        "classifier_model": model,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": _sha256(prompt),
        "response_text": text,
        "sha256": _sha256(text),
    }
    _append(ledger_path, row)
    return _from_row(base, row, vmap, f"new call, row appended to {Path(ledger_path).name}")


def default_call(engine: str = "anthropic") -> ClassifierCall:
    """The live call: one short prompt through the existing engine adapters."""

    def _call(prompt: str) -> tuple[str, str]:
        from .engines import ENGINES, run_once_on

        result = run_once_on(engine, prompt, max_tokens=100)
        return result.raw_text, result.model_version_hint or ENGINES[engine].default_model

    return _call


__all__ = [
    "AUDIENCE_FROM_CLASSIFIER",
    "AUDIENCE_UNCLASSIFIED",
    "ClassifyError",
    "build_prompt",
    "default_call",
    "parse_classification",
    "read_ledger",
    "resolve_vertical",
]
