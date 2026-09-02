"""
Evidence trail export — B3.

The substrate (raw_response_text, request_payload, response_hash) has been
captured on every row since the runner was written; none of it reached the
artifact a customer receives. This module is the missing last mile:

  evidence_appendix_lines(objs) -> lines for the PDF report
  write_evidence_jsonl(path, objs) -> the raw evidence file shipped WITH the PDF
  verify_hashes(objs) -> at-export integrity check; failures are REPORTED,
                         never silently dropped
  bundle_digest(objs) -> one SHA-256 over all run hashes, printed in the PDF
                         and recomputable from the evidence file, tying the
                         two artifacts together

Abstained runs are included in the trail on purpose: an abstention is a
result, and its evidence ships with the same provenance as a score.
"""
from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from pathlib import Path

from .models import VisibilityObj


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def bundle_digest(objs: Sequence[VisibilityObj]) -> str:
    """SHA-256 over the newline-joined per-run response hashes, in run order."""
    joined = "\n".join(o.response_hash for o in objs)
    return _sha256(joined)


def verify_hashes(objs: Sequence[VisibilityObj]) -> list[str]:
    """
    Recompute each row's response hash from its stored raw text.

    Returns one human-readable line per mismatch; empty list means every
    stored transcript still matches its recorded hash.
    """
    problems: list[str] = []
    for o in objs:
        actual = _sha256(o.raw_response_text)
        if actual != o.response_hash:
            problems.append(
                f"HASH MISMATCH run {o.run_index}: "
                f"stored {o.response_hash} != recomputed {actual}"
            )
    return problems


def evidence_appendix_lines(objs: Sequence[VisibilityObj]) -> list[str]:
    """
    The EVIDENCE TRAIL section for the customer PDF.

    Includes every run — scored or abstained. Nothing is truncated: the full
    64-character hash appears for each run (the PDF writer wraps, it does not
    cut).
    """
    objs = list(objs)
    lines: list[str] = [
        "",
        "=== EVIDENCE TRAIL ===",
        "Every number in this report is derived from stored raw model",
        "responses. Each run below lists the SHA-256 of the exact response",
        "text received. The full transcripts accompany this report as an",
        "evidence file (JSONL, one run per line); recomputing any run's",
        "hash from its transcript must reproduce the value printed here.",
        "",
        f"Runs in trail: {len(objs)}",
        f"Evidence bundle digest (sha256 over per-run hashes, run order): "
        f"{bundle_digest(objs)}",
    ]

    problems = verify_hashes(objs)
    if problems:
        lines.append("")
        lines.append("!!! EVIDENCE INTEGRITY CHECK FAILED AT EXPORT TIME !!!")
        lines.extend(problems)
    else:
        lines.append(
            "Integrity: all response hashes re-verified against stored "
            "transcripts at export time."
        )

    for o in objs:
        temp_s = "n/a" if o.temperature is None else str(o.temperature)
        served = o.model_version_hint or "n/a"
        lines.extend(
            [
                "",
                f"Run {o.run_index} - {o.executed_at_utc.isoformat()}",
                f"  model requested: {o.model_provider}/{o.model_name}"
                f"  served: {served}",
                f"  temperature: {temp_s}  max_tokens: {o.max_tokens}",
                f"  prompt: {o.prompt_id} {o.prompt_version}"
                f"  family: {o.prompt_family}",
                f"  response_sha256: {o.response_hash}",
                f"  parse: mode={o.parse_mode} success={o.parse_success}"
                f"  errors={','.join(o.parse_errors) or 'none'}",
                f"  anchor: {o.stability_anchor_key}",
            ]
        )

    return lines


def write_evidence_jsonl(path: Path, objs: Iterable[VisibilityObj]) -> None:
    """
    Write the evidence file the customer receives next to the PDF.

    Full rows, raw transcripts included. Deterministic-overwrite ("w"), unlike
    storage.write_jsonl which appends: this file is a rendered export of the
    given runs, regenerated whole each time, never an accumulating log.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for o in objs:
            f.write(o.model_dump_json())
            f.write("\n")
