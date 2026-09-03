"""aivis bank runner — OpenAI surface. New-path tool; touches nothing existing.

Discipline baked in (sources: 03 defects, 13 ledger):
  D0  - progress counts CLEAN responses, never rows written; DONE is refused
        and exit code is 1 if CLEAN == 0. The cost line prints token usage
        totals, never a dollar figure (OpenAI unit cost is unmeasured).
  B1  - --out is REQUIRED and must NOT already exist; this tool never
        overwrites or unlinks anything.
  err - engine failures go to <out>.errors.jsonl, never into the evidence
        file, so DISTINCT on the evidence file is DISTINCT of clean rows by
        construction.
  J10 - run manifest carries UTC ISO8601 start/end.

Usage:
  PYTHONPATH=src/aivis python run_bank_openai.py \
      --bank study2/config/prompts_pr_agency_v1.json \
      --runs 3 --model gpt-4o-mini \
      --out data/audits/pr_agency_openai_run1_v1.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from openai_adapter import EngineError, run_once_openai


def load_bank(path: Path) -> tuple[list[dict], str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    bank_version, sealed = "", ""
    if isinstance(data, dict) and "families" in data:
        # Real study2 schema: {bank_version, sealed, construction_rule,
        #                      families: {name: [{id, text}, ...]}}
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
        # The MT-C01..C06 lesson: a colliding bank corrupts every denominator.
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
                    help="versioned NEW path; refused if it exists")
    ap.add_argument("--sleep", type=float, default=0.6)
    ap.add_argument("--bank-version", default="v1")
    args = ap.parse_args()

    if args.out.exists():
        sys.exit(f"REFUSED: {args.out} exists. This tool never overwrites. "
                 f"Pick a new versioned path.")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key or api_key == "PASTE_NEW_KEY_HERE":
        sys.exit("REFUSED: OPENAI_API_KEY not set")

    prompts, file_bank_version, sealed = load_bank(args.bank)
    bank_version = file_bank_version or args.bank_version
    fams = sorted({p["family"] for p in prompts if p.get("family")})
    print(f"BANK {args.bank}  version={bank_version!r}  sealed={sealed!r}")
    print(f"PROMPTS {len(prompts)}  FAMILIES {len(fams)} {fams}")
    err_path = args.out.with_suffix(args.out.suffix + ".errors.jsonl")
    args.out.parent.mkdir(parents=True, exist_ok=True)

    started = datetime.now(timezone.utc).isoformat()
    attempted = clean = errors = 0
    hashes: set[str] = set()
    tok_in = tok_out = 0

    with args.out.open("a", encoding="utf-8") as out_f, \
         err_path.open("a", encoding="utf-8") as err_f:
        for p in prompts:
            for run_i in range(args.runs):
                attempted += 1
                try:
                    row = run_once_openai(
                        p["text"], args.model, api_key,
                        prompt_id=p.get("id", ""),
                        bank_version=bank_version,
                    )
                except EngineError as e:
                    errors += 1
                    err_f.write(json.dumps({
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "prompt_id": p.get("id", ""), "run": run_i,
                        "error": str(e)[:500],
                    }) + "\n")
                    err_f.flush()
                    continue
                row["family"] = p.get("family", "")
                out_f.write(json.dumps(row) + "\n")
                out_f.flush()
                clean += 1
                hashes.add(row["sha256"])
                usage = row.get("usage", {}) or {}
                tok_in += int(usage.get("prompt_tokens", 0) or 0)
                tok_out += int(usage.get("completion_tokens", 0) or 0)
                print(f"CLEAN {clean}/{attempted} attempted  "
                      f"[{p.get('id','?')} run {run_i+1}/{args.runs}]",
                      flush=True)
                time.sleep(args.sleep)

    ended = datetime.now(timezone.utc).isoformat()
    print("-" * 60)
    print(f"ATTEMPTED {attempted}  CLEAN {clean}  ERRORS {errors}  "
          f"DISTINCT_CLEAN {len(hashes)}")
    print(f"TOKENS prompt={tok_in} completion={tok_out}  "
          f"(cost: compute AFTER from posted prices — never quoted here)")
    print(f"START {started}  END {ended}")
    print(f"EVIDENCE {args.out}")
    print(f"ERRORS   {err_path} ({errors} entries)")
    if clean == 0:
        print("VERDICT: FAILED — zero clean responses. Nothing is DONE.")
        return 1
    print("VERDICT: run complete. Verify next: verify_evidence.py, then report.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
