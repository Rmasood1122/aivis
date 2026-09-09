"""aivis bank runner — Perplexity Sonar surface. New-path tool; touches nothing existing.

Discipline baked in (sources: 03 defects, 08/13 ledgers):
  D0  - progress counts CLEAN responses, never rows written; DONE is refused
        and exit code is 1 if CLEAN == 0. The dollar line is SUMMED from the
        per-row usage.cost the API itself returns [MEASURED], never estimated;
        rows lacking a cost block are counted and named on the same line.
  B1  - --out is REQUIRED and must NOT already exist; nor may the errors file
        or the manifest. This tool never overwrites or unlinks anything.
  err - engine failures go to <out>.errors.jsonl, never into the evidence
        file, so DISTINCT on the evidence file is DISTINCT of clean rows by
        construction.
  J10 - manifest carries UTC ISO8601 start/end.
  A10 - every clean row carries request_payload, response_text, sha256,
        bank_version, model, temperature.
  G10 NOTE - load_bank is duplicated from run_bank_openai_v2.py verbatim.
        Consolidating the three copies into a shared module edits existing
        files and needs a named "go"; logged, not done here.
  MANIFEST carries surface_currency — the model-currency ledger item, first
        implementation: this endpoint is vendor-marked legacy, and that fact
        rides with the data instead of living in a doc.

Usage (smoke: first 5 prompts x 2 runs):
  PYTHONPATH=src/aivis python run_bank_perplexity_v1.py \
      --bank study2/config/prompts_pr_agency_v1.json \
      --runs 2 --model sonar --limit 5 \
      --out data/audits/pr_agency_pplx_smoke1_v1.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import sleep as _sleep

from perplexity_adapter import SURFACE, EngineError, run_once_perplexity

SURFACE_CURRENCY = (
    "perplexity chat.completions vendor-marked LEGACY, migration target "
    "Agent API [REPORTED: docs.perplexity.ai + perplexity.ai/api-platform, "
    "fetched 2026-09-05]; re-check before any run after 2026-12-01"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_bank(path: Path) -> tuple[list[dict], str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    bank_version, sealed = "", ""
    if isinstance(data, dict) and "families" in data:
        bank_version = str(data.get("bank_version", ""))
        sealed = str(data.get("sealed", ""))
        prompts = []
        for fam, items in data["families"].items():
            for p in items:
                prompts.append({"id": p["id"], "text": p["text"], "family": fam})
    elif isinstance(data, dict) and "prompts" in data:
        prompts = [dict(p, family=p.get("family", "")) for p in data["prompts"]]
        bank_version = str(data.get("bank_version", ""))
    elif isinstance(data, list):
        prompts = [dict(p, family=p.get("family", "")) for p in data]
    else:
        sys.exit(f"REFUSED: unrecognised bank schema at {path}")
    if not prompts:
        sys.exit(f"REFUSED: bank at {path} contains zero prompts")
    ids = [p.get("id", "") for p in prompts]
    if len(set(ids)) != len(ids):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        sys.exit(
            f"REFUSED: bank id collision — {len(ids)} entries, "
            f"{len(set(ids))} distinct ids. Duplicates: {dupes[:6]}"
        )
    return prompts, bank_version, sealed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", required=True, type=Path)
    ap.add_argument("--runs", required=True, type=int)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True, type=Path,
                    help="evidence file; must not already exist")
    ap.add_argument("--sleep", type=float, default=0.6)
    ap.add_argument("--bank-version", default="v1")
    ap.add_argument("--limit", type=int, default=0,
                    help="first N prompts in bank order; 0 = all")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=2048)
    args = ap.parse_args()

    api_key = os.environ.get("PERPLEXITY_API_KEY", "")
    if not api_key:
        sys.exit("REFUSED: PERPLEXITY_API_KEY not set")

    out: Path = args.out
    err_path = Path(str(out) + ".errors.jsonl")
    manifest_path = Path(str(out) + ".manifest.json")
    for p in (out, err_path, manifest_path):
        if p.exists():
            sys.exit(f"REFUSED: {p} already exists — this tool never overwrites")
    out.parent.mkdir(parents=True, exist_ok=True)

    prompts, bank_version_file, sealed = load_bank(args.bank)
    bank_version = bank_version_file or args.bank_version
    if args.limit > 0:
        prompts = prompts[: args.limit]

    started = _utc_now()
    attempted = clean = errored = 0
    hashes: set[str] = set()
    models_returned: set[str] = set()
    cost_total = 0.0
    cost_rows = 0
    tok_in = tok_out = 0

    with out.open("a", encoding="utf-8") as fh_out, \
            err_path.open("a", encoding="utf-8") as fh_err:
        for prompt in prompts:
            for run_index in range(1, args.runs + 1):
                attempted += 1
                try:
                    row = run_once_perplexity(
                        prompt_text=prompt["text"],
                        model=args.model,
                        api_key=api_key,
                        temperature=args.temperature,
                        max_tokens=args.max_tokens,
                    )
                except EngineError as err:
                    errored += 1
                    fh_err.write(json.dumps({
                        "ts": _utc_now(),
                        "prompt_id": prompt.get("id", ""),
                        "family": prompt.get("family", ""),
                        "run_index": run_index,
                        "error": str(err),
                    }) + "\n")
                    fh_err.flush()
                    print(f"[{clean}/{attempted} clean] "
                          f"{prompt.get('id','?')} run {run_index} ERROR")
                    _sleep(args.sleep)
                    continue
                row["prompt_id"] = prompt.get("id", "")
                row["family"] = prompt.get("family", "")
                row["run_index"] = run_index
                row["bank_version"] = bank_version
                fh_out.write(json.dumps(row, ensure_ascii=False) + "\n")
                fh_out.flush()
                clean += 1
                hashes.add(row["sha256"])
                if row.get("model"):
                    models_returned.add(row["model"])
                usage = row.get("usage") or {}
                tok_in += int(usage.get("prompt_tokens") or 0)
                tok_out += int(usage.get("completion_tokens") or 0)
                cost = (usage.get("cost") or {}).get("total_cost")
                if isinstance(cost, (int, float)):
                    cost_total += float(cost)
                    cost_rows += 1
                print(f"[{clean}/{attempted} clean] "
                      f"{prompt.get('id','?')} run {run_index} ok")
                _sleep(args.sleep)

    ended = _utc_now()
    manifest = {
        "engine": "perplexity",
        "surface": SURFACE,
        "surface_currency": SURFACE_CURRENCY,
        "model_requested": args.model,
        "models_returned": sorted(models_returned),
        "bank": str(args.bank),
        "bank_version": bank_version,
        "bank_sealed": sealed,
        "prompts_in_scope": len(prompts),
        "limit_first_n": args.limit,
        "iteration_order": "prompt-major: all runs of prompt i before i+1",
        "runs_per_prompt": args.runs,
        "temperature_requested": args.temperature,
        "max_tokens_requested": args.max_tokens,
        "attempted": attempted,
        "clean": clean,
        "errors": errored,
        "distinct_clean": len(hashes),
        "prompt_tokens_total": tok_in,
        "completion_tokens_total": tok_out,
        "cost_usd_summed_from_usage": round(cost_total, 6),
        "cost_rows_carrying_usage_cost": f"{cost_rows} of {clean} clean rows",
        "started_utc": started,
        "ended_utc": ended,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(f"CLEAN {clean} of ATTEMPTED {attempted} · ERRORS {errored} "
          f"· DISTINCT_CLEAN {len(hashes)}")
    if cost_rows:
        print(f"COST ${cost_total:.4f} summed from usage.cost "
              f"[MEASURED: {cost_rows} of {clean} clean rows]")
    else:
        print("COST unavailable: no row carried usage.cost")
    print(f"manifest: {manifest_path}")
    if clean == 0:
        print("REFUSED: zero clean responses — this run is NOT done (D0)")
        return 1
    print("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
