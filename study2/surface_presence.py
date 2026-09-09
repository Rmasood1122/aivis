#!/usr/bin/env python3
"""surface_presence.py — referral-surface presence measurement over stored transcripts.

STAGE: deterministic pre-pass. Runs BEFORE any LLM extraction. Stdlib only.

WHAT IT MEASURES
  For every clean evidence row (JSONL, aivis schema), classifies the transcript's
  behavior mode and counts referral-surface presence (binary per surface per
  transcript). Emits JSON + a markdown report section with denominators on every
  count. Subject presence on each surface defaults to NOT_MEASURED unless a
  presence file is supplied — this tool never guesses and never fetches.

WHAT IT IS NOT
  Not a validated extractor. Every count is UNVALIDATED_PARSE_PENDING_KAPPA.
  The keyword canon below has named false-positive vectors (see FP_NOTES),
  the same class as the D5 colour-Purple problem. The kappa study covers this
  tool's output the same as any other parse.

USAGE
  python3 surface_presence.py EVIDENCE.jsonl [EVIDENCE2.jsonl ...]
      [--subject NAME] [--firms firms.txt] [--presence presence.json]
      [--family-map map.json] [--out out.json] [--report report.md]

  firms.txt        one candidate firm name per line (drives NAMES_FIRMS mode)
  presence.json    {"surface_id": "PRESENT"|"ABSENT", ...} measured separately
  family-map.json  {"prompt_id": "family", ...} if rows lack a family field
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field

CANON_VERSION = "referral_surfaces_v0.1"

# Each surface: (surface_id, [(regex, flags)], fp_note)
# FP_NOTES document known false-positive vectors, D5-style. They are part of
# the canon and hash with it.
SURFACE_CANON: list[tuple[str, list[tuple[str, int]], str]] = [
    (
        "journalist_matching",
        [
            (r"\bHARO\b", 0),
            (r"\bHelp\s+a\s+Reporter\b", re.IGNORECASE),
            (r"\bConnectively\b", re.IGNORECASE),
            (r"\bQwoted\b", re.IGNORECASE),
            (r"\bSourceBottle\b", re.IGNORECASE),
        ],
        "HARO uppercase-only to avoid Spanish 'haro'/proper names.",
    ),
    (
        "professional_directory",
        [
            (r"\bPRSA\b", 0),
            (r"\bFind[-\s]a[-\s]Firm\b", re.IGNORECASE),
            (r"\bPRCA\b", 0),
        ],
        "PRSA/PRCA uppercase-only.",
    ),
    (
        "review_marketplace",
        [
            (r"\bClutch(?:\.co)?\b", 0),
            (r"\bG2(?:\.com)?\b", 0),
            (r"\bUpwork\b", re.IGNORECASE),
            (r"\bDesignRush\b", re.IGNORECASE),
            (r"\bBark\.com\b", re.IGNORECASE),
        ],
        "Clutch capitalized-only ('clutch situation' FP vector); Bark requires "
        ".com (dog-bark FP vector); bare 'G2' can FP on motorsport/military text.",
    ),
    (
        "trade_press",
        [
            (r"\bPRWeek\b", re.IGNORECASE),
            (r"\bPR\s+Week\b", 0),
            (r"\bAdweek\b", re.IGNORECASE),
            (r"\bBulldog\s+Reporter\b", re.IGNORECASE),
            (r"\bPRNEWS\b", 0),
        ],
        "",
    ),
    (
        "media_database",
        [
            (r"\bMuck\s?Rack\b", re.IGNORECASE),
            (r"\bCision\b", re.IGNORECASE),
            (r"\bProwly\b", re.IGNORECASE),
            (r"\bMeltwater\b", re.IGNORECASE),
        ],
        "",
    ),
    (
        "peer_referral",
        [
            (r"\bask\s+(?:other\s+)?(?:founders|peers|colleagues)\b", re.IGNORECASE),
            (r"\breferrals?\s+from\s+(?:peers|founders|your\s+network)\b", re.IGNORECASE),
            (r"\bword[-\s]of[-\s]mouth\b", re.IGNORECASE),
            (r"\bindustry\s+(?:groups|associations|contacts)\b", re.IGNORECASE),
        ],
        "Phrase-heuristic, weakest patterns in the canon; expect kappa to be "
        "lowest here. Treat counts as ceiling.",
    ),
]

REFUSAL_PATTERNS = [
    (r"\b(?:can(?:no|')t|cannot|unable\s+to)\s+(?:recommend|provide\s+specific|name\s+specific)", re.IGNORECASE),
    (r"\bI\s+don'?t\s+have\s+(?:access\s+to\s+)?(?:current|up[-\s]to[-\s]date|real[-\s]time)", re.IGNORECASE),
    (r"\bwithout\s+(?:knowing|more\s+information\s+about)\s+your\b", re.IGNORECASE),
]

NAMING_SPARSE_THRESHOLD = 0.20  # below this share of NAMES_FIRMS, naming metrics are UNDEFINED
LOW_N = 3

MODES = ("NAMES_FIRMS", "REFERS_TO_SURFACES", "REFUSES_OPAQUE", "OTHER")


def canon_hash() -> str:
    blob = json.dumps(
        [(sid, pats, note) for sid, pats, note in SURFACE_CANON],
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def engine_of(model: str) -> str:
    m = (model or "").lower()
    if m.startswith("claude") or "anthropic" in m:
        return "anthropic"
    if m.startswith(("gpt", "o1", "o3", "o4")) or "openai" in m:
        return "openai"
    if "sonar" in m or "perplexity" in m:
        return "perplexity"
    if "gemini" in m:
        return "google"
    return m or "unknown"


@dataclass
class Row:
    text: str
    engine: str
    family: str
    search_enabled: str
    prompt_id: str


@dataclass
class CellStats:
    total: int = 0
    modes: dict = field(default_factory=lambda: {m: 0 for m in MODES})
    surface_hits: dict = field(default_factory=lambda: defaultdict(int))


def load_rows(paths: list[str], family_map: dict[str, str]) -> tuple[list[Row], int, int]:
    rows: list[Row] = []
    attempted = 0
    skipped_error = 0
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                attempted += 1
                rec = json.loads(line)
                text = rec.get("response_text") or ""
                if not text or rec.get("error"):
                    skipped_error += 1
                    continue
                payload = rec.get("request_payload") or {}
                prompt_id = str(rec.get("prompt_id") or rec.get("id") or "")
                family = (
                    rec.get("family")
                    or rec.get("prompt_family")
                    or family_map.get(prompt_id)
                    or "unknown"
                )
                rows.append(
                    Row(
                        text=text,
                        engine=engine_of(rec.get("model") or payload.get("model") or ""),
                        family=str(family),
                        search_enabled=str(rec.get("search_enabled", "unknown")),
                        prompt_id=prompt_id,
                    )
                )
    return rows, attempted, skipped_error


def compile_firms(path: str | None) -> list[tuple[str, re.Pattern]]:
    if not path:
        return []
    firms = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            name = line.strip()
            if not name or name.startswith("#"):
                continue
            firms.append((name, re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)))
    return firms


def classify(text: str, firm_res: list[tuple[str, re.Pattern]]) -> tuple[str, list[str], list[str]]:
    """Returns (mode, surfaces_hit, firms_hit). Order of precedence:
    NAMES_FIRMS > REFERS_TO_SURFACES > REFUSES_OPAQUE > OTHER."""
    firms_hit = [name for name, rx in firm_res if rx.search(text)]
    surfaces_hit = []
    for sid, patterns, _note in SURFACE_CANON:
        for pat, flags in patterns:
            if re.search(pat, text, flags):
                surfaces_hit.append(sid)
                break
    if firms_hit:
        return "NAMES_FIRMS", surfaces_hit, firms_hit
    if surfaces_hit:
        return "REFERS_TO_SURFACES", surfaces_hit, []
    for pat, flags in REFUSAL_PATTERNS:
        if re.search(pat, text, flags):
            return "REFUSES_OPAQUE", [], []
    return "OTHER", [], []


def run(
    paths: list[str],
    subject: str | None,
    firms_path: str | None,
    presence_path: str | None,
    family_map_path: str | None,
) -> dict:
    family_map = {}
    if family_map_path:
        with open(family_map_path, encoding="utf-8") as fh:
            family_map = json.load(fh)
    presence = {}
    if presence_path:
        with open(presence_path, encoding="utf-8") as fh:
            presence = json.load(fh)
        bad = {k: v for k, v in presence.items() if v not in ("PRESENT", "ABSENT")}
        if bad:
            raise SystemExit(f"presence file values must be PRESENT|ABSENT, got: {bad}")

    firm_res = compile_firms(firms_path)
    rows, attempted, skipped = load_rows(paths, family_map)

    cells: dict[tuple[str, str, str], CellStats] = defaultdict(CellStats)
    for row in rows:
        mode, surfaces_hit, _firms = classify(row.text, firm_res)
        cell = cells[(row.engine, row.search_enabled, row.family)]
        cell.total += 1
        cell.modes[mode] += 1
        for sid in surfaces_hit:
            cell.surface_hits[sid] += 1

    engine_behavior = []
    referral_surfaces = []
    for (engine, search, family), cell in sorted(cells.items()):
        # mode-conservation check — refuse to emit if it fails
        if sum(cell.modes.values()) != cell.total:
            raise SystemExit(
                f"MODE CONSERVATION FAILED in cell {(engine, search, family)}: "
                f"{cell.modes} != {cell.total}"
            )
        naming_share = cell.modes["NAMES_FIRMS"] / cell.total if cell.total else 0.0
        sparse = naming_share < NAMING_SPARSE_THRESHOLD
        engine_behavior.append(
            {
                "engine": engine,
                "search_enabled": search,
                "family": family,
                "modes": dict(cell.modes),
                "denominator": cell.total,
                "naming_sparse": sparse,
                "primary_finding": (
                    "naming-share UNDEFINED in this cell (naming-sparse); "
                    "referral-surface presence is the measurable layer"
                    if sparse
                    else f"NAMES_FIRMS {cell.modes['NAMES_FIRMS']}/{cell.total}"
                ),
            }
        )
        for sid, _pats, _note in SURFACE_CANON:
            count = cell.surface_hits.get(sid, 0)
            if count == 0:
                continue
            referral_surfaces.append(
                {
                    "surface_id": sid,
                    "engine": engine,
                    "search_enabled": search,
                    "family": family,
                    "count": count,
                    "denominator": cell.total,
                    "low_n": count < LOW_N,
                    "subject_presence": presence.get(sid, "NOT_MEASURED"),
                }
            )

    return {
        "tool": "surface_presence.py",
        "canon_version": CANON_VERSION,
        "canon_sha256": canon_hash(),
        "subject": subject or "UNDECLARED",
        "inputs": paths,
        "rows_attempted": attempted,
        "rows_clean": len(rows),
        "rows_skipped_error_or_empty": skipped,
        "firms_list_supplied": bool(firm_res),
        "firms_count": len(firm_res),
        "note_no_firms": (
            None
            if firm_res
            else "NO FIRMS LIST: NAMES_FIRMS mode cannot fire; mode distribution "
            "is a lower bound on naming. Supply --firms before quoting modes."
        ),
        "engine_behavior": engine_behavior,
        "referral_surfaces": referral_surfaces,
        "extraction_status": "UNVALIDATED_PARSE_PENDING_KAPPA",
    }


def emit_markdown(result: dict) -> str:
    lines = []
    lines.append("## Referral-surface presence (deterministic pre-pass)")
    lines.append("")
    lines.append(
        f"Canon `{result['canon_version']}` · sha256 `{result['canon_sha256'][:16]}…` · "
        f"rows clean {result['rows_clean']} of attempted {result['rows_attempted']} · "
        f"status **{result['extraction_status']}**"
    )
    if result.get("note_no_firms"):
        lines.append("")
        lines.append(f"> ⚠ {result['note_no_firms']}")
    lines.append("")
    lines.append("### Behavior modes per cell")
    lines.append("")
    lines.append("| engine | search | family | NAMES | REFERS | REFUSES | OTHER | n | naming-sparse |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for eb in result["engine_behavior"]:
        m = eb["modes"]
        lines.append(
            f"| {eb['engine']} | {eb['search_enabled']} | {eb['family']} "
            f"| {m['NAMES_FIRMS']} | {m['REFERS_TO_SURFACES']} | {m['REFUSES_OPAQUE']} "
            f"| {m['OTHER']} | {eb['denominator']} | {'**YES**' if eb['naming_sparse'] else 'no'} |"
        )
    lines.append("")
    lines.append("### Surfaces the engine routes buyers to")
    lines.append("")
    if not result["referral_surfaces"]:
        lines.append("INSUFFICIENT_EVIDENCE — no surface hits in any cell.")
    else:
        lines.append("| surface | engine | family | count/n | low-n | subject presence |")
        lines.append("|---|---|---|---|---|---|")
        for rs in result["referral_surfaces"]:
            lines.append(
                f"| {rs['surface_id']} | {rs['engine']} | {rs['family']} "
                f"| {rs['count']}/{rs['denominator']} | {'yes' if rs['low_n'] else ''} "
                f"| {rs['subject_presence']} |"
            )
    lines.append("")
    lines.append(
        "Subject presence is measured separately and supplied via `--presence`; "
        "NOT_MEASURED is printed, never guessed."
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("evidence", nargs="+", help="evidence JSONL file(s)")
    ap.add_argument("--subject", default=None)
    ap.add_argument("--firms", default=None, help="one candidate firm name per line")
    ap.add_argument("--presence", default=None, help="JSON {surface_id: PRESENT|ABSENT}")
    ap.add_argument("--family-map", default=None, help="JSON {prompt_id: family}")
    ap.add_argument("--out", default=None, help="write JSON here (new path only)")
    ap.add_argument("--report", default=None, help="write markdown section here (new path only)")
    args = ap.parse_args(argv)

    for target in (args.out, args.report):
        if target:
            import os

            if os.path.exists(target):
                raise SystemExit(f"REFUSED: {target} exists. New paths only (destruction lock).")

    result = run(args.evidence, args.subject, args.firms, args.presence, args.family_map)
    blob = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        with open(args.out, "x", encoding="utf-8") as fh:
            fh.write(blob + "\n")
    else:
        print(blob)
    md = emit_markdown(result)
    if args.report:
        with open(args.report, "x", encoding="utf-8") as fh:
            fh.write(md)
    else:
        sys.stderr.write(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
