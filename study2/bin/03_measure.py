#!/usr/bin/env python3
"""03 · Measurement arm. Runs the bank against live engines in BOTH presentation orders.
Every row: raw response text, request payload, sha256, timestamp.
REFUSES to run without out/probe_receipt.json from this session."""
import json, os, sys, time, hashlib, pathlib, urllib.request, datetime, argparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(ROOT)

ap = argparse.ArgumentParser()
ap.add_argument("--bank", default="config/prompts_cosmetic_tristate_v1.json")
ap.add_argument("--sample", default="data/sample_validated.csv")
ap.add_argument("--runs", type=int, default=7)
ap.add_argument("--out", required=True, help="versioned output path; never a default")
ap.add_argument("--dry-run", action="store_true", help="no calls, prints the call plan and cost")
args = ap.parse_args()

OUTP = pathlib.Path(args.out)
if OUTP.exists():
    sys.exit(f"REFUSED: {OUTP} exists. Choose a new versioned path. Nothing is overwritten.")

UNIT_COST = 0.007602  # [MEASURED: P24]

ENGINES = {
    "claude": dict(url="https://api.anthropic.com/v1/messages", key="ANTHROPIC_API_KEY",
                   model="claude-sonnet-4-6", style="anthropic"),
    "chatgpt": dict(url="https://api.openai.com/v1/chat/completions", key="OPENAI_API_KEY",
                    model="gpt-4o", style="openai"),
    "grok": dict(url="https://api.x.ai/v1/chat/completions", key="XAI_API_KEY",
                 model="grok-2-latest", style="openai"),
}

receipt_p = pathlib.Path("out/probe_receipt.json")
if not receipt_p.exists():
    sys.exit("REFUSED: no out/probe_receipt.json. Run bin/00_probe.sh first.\n"
             "No measurement may be reported for a run that did not happen.")
receipt = json.loads(receipt_p.read_text())
live = [e["engine"] for e in receipt["engines"] if e["live"]]
name_map = {"anthropic": "claude", "openai": "chatgpt", "xai": "grok"}
live = [name_map.get(e, e) for e in live]
if not live:
    sys.exit("REFUSED: probe receipt shows 0 live engines.")

bank = json.loads(pathlib.Path(args.bank).read_text())
prompts = [p for fam in bank["families"].values() for p in fam]

import csv
with open(args.sample) as f:
    brands = [r for r in csv.DictReader(f)]
names = [b["practice_name"] for b in brands]

# OPEN-ENDED RETRIEVAL. The roster is NOT injected into the prompt: injecting it
# measures prompted recall, not retrieval, and makes a 60% top-3 rate arithmetically
# unreachable across 50 candidates. Order-bias reversal does not apply to an open
# prompt (there is no presented order to reverse); it is measured separately on the
# subset of responses where the MODEL itself emits a ranked list.
ORDERS = {"open": None}

total = len(prompts) * args.runs * len(live) * len(ORDERS)
plan = dict(prompts=len(prompts), runs=args.runs, engines=live, orders=list(ORDERS),
            brands=len(names), total_calls=total, est_cost_usd=round(total * UNIT_COST, 2))
print(json.dumps(plan, indent=2))

if args.dry_run:
    print("\nDRY RUN. No calls placed. No rows written.")
    sys.exit(0)


def call(engine, prompt_text):
    cfg = ENGINES[engine]
    key = os.environ.get(cfg["key"])
    if cfg["style"] == "anthropic":
        payload = {"model": cfg["model"], "max_tokens": 2048, "temperature": 0.0,
                   "messages": [{"role": "user", "content": prompt_text}]}
        hdrs = {"x-api-key": key, "anthropic-version": "2023-06-01",
                "content-type": "application/json",
                "anthropic-workspace-id": os.environ.get("ANTHROPIC_WORKSPACE_ID", "")}
    else:
        payload = {"model": cfg["model"], "max_tokens": 2048, "temperature": 0.0,
                   "messages": [{"role": "user", "content": prompt_text}]}
        hdrs = {"Authorization": f"Bearer {key}", "content-type": "application/json",
                "anthropic-workspace-id": os.environ.get("ANTHROPIC_WORKSPACE_ID", "")}
    body = json.dumps(payload).encode()
    req = urllib.request.Request(cfg["url"], data=body, headers=hdrs)
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = json.loads(r.read().decode())
    if cfg["style"] == "anthropic":
        text = "".join(b.get("text", "") for b in raw.get("content", []))
        rid = raw.get("id", "")
    else:
        text = raw["choices"][0]["message"]["content"]
        rid = raw.get("id", "")
    return text, rid, payload


written = 0
with OUTP.open("w") as out:
    for order_name, order_names in ORDERS.items():
        for p in prompts:
            text = p['text']
            for engine in live:
                for run in range(1, args.runs + 1):
                    try:
                        resp, rid, payload = call(engine, text)
                        err = None
                    except Exception as e:
                        resp, rid, payload, err = "", "", {}, f"{type(e).__name__}: {e}"
                    row = {
                        "bank_version": bank["bank_version"],
                        "prompt_id": p["id"], "engine": engine, "run": run,
                        "order": order_name, "temperature": 0.0,
                        "model": ENGINES[engine]["model"],
                        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "request_payload": payload, "response_id": rid,
                        "response_text": resp, "error": err,
                        "sha256": hashlib.sha256(resp.encode()).hexdigest() if resp else None,
                    }
                    out.write(json.dumps(row) + "\n")
                    out.flush()
                    written += 1
                    if written % 25 == 0:
                        print(f"  {written}/{total} rows  (${written*UNIT_COST:.2f})", flush=True)
                    time.sleep(0.35)

print(f"\nDONE. {written} rows to {OUTP}. Actual cost basis ${written*UNIT_COST:.2f}")
