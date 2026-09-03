# OpenAI adapter — live smoke checklist (runs on YOUR machine, not the container)

STATUS OF THIS PACKAGE: mocked suite 9/9 green [MEASURED: clean container,
2026-09-03]. Live path [UNVERIFIED on destination] until step 4 below passes.
Per charter §10, nothing external may claim a working ChatGPT adapter before
step 4. Battery mapping: C08 (second engine end-to-end) closes at step 4;
C02-class unit cost for OpenAI closes at step 6.

## 1. Key hygiene BEFORE the key exists (K01/K02 lessons)
- Create the key at platform.openai.com with minimal scope; fund $5.
- Put it in .env as OPENAI_API_KEY. Confirm .env is gitignored FIRST:
  `git check-ignore -v .env` must return a hit.
- The Anthropic key-rotation gate is separate and still open; this adds a
  second credential to the same file — same rules, same exposure history.

## 2. Drop-in (new paths only — no "go" needed)
- Copy openai_adapter.py and test_openai_adapter.py into the repo at NEW paths
  (suggest src/aivis/engines/openai_adapter.py, tests/test_openai_adapter.py).
- Run the mocked suite locally: `python -m pytest tests/test_openai_adapter.py -q`
  Expected: 9 passed. If import paths differ, fix the test import line only.

## 3. Interface note — [UNVERIFIED]
This adapter was written WITHOUT access to the private repo. It matches the
A10 row schema from the ledgers, but the exact call signature your runner.py
expects is unverified. Reconcile by reading runner.py's Anthropic path first;
adapt the adapter to it, never the reverse.

## 4. C08 — one prompt, one run, live
    python -c "
    import json, os
    from aivis.engines.openai_adapter import run_once_openai
    row = run_once_openai('What are the best premium mattress brands?',
                          'gpt-4o-mini', os.environ['OPENAI_API_KEY'],
                          prompt_id='SMOKE-01', bank_version='v1')
    print(json.dumps({k: row[k] for k in ('model','temperature','request_id','sha256','param_adaptations')}, indent=2))
    print('TEXT_LEN', len(row['response_text']))
    " 
  PASS = a row with a distinct `model` field, hash recomputable, request_id
  recorded. Paste the output into the ledger; C08 closes on the paste, not on
  memory.

## 5. Verify the row the hard way
- Recompute sha256 of response_text independently (one line of python) and
  compare. Grep the row JSON for the key prefix: 0 hits required (K05).

## 6. Unit cost — BEFORE any margin claim
- The $0.007602 figure is Claude-only [MEASURED: P24]. Run 30 calls, read
  `usage` from the rows, compute cost from OpenAI's posted prices, record
  with population. Until then, OpenAI cost is [UNVERIFIED] and stays out of
  the Sep 8 numbers.

## 7. Integration into cli.py (EDITS EXISTING FILES — needs your "go")
Minimal diff points: engine flag/dispatch where run_once is selected; the
evidence writer already takes the row dict; report face must print the
surface declaration string per engine. Cross-surface DISTINCT comparisons
remain refused per the session-6 amendment — OpenAI rows never pool with
Claude rows in one metric.

## Claims boundary until step 4 passes
Sayable: "the ChatGPT adapter is built and its test suite is green; the live
run is scheduled." NOT sayable: "aivis runs on ChatGPT." After step 4:
"measures ChatGPT via the OpenAI developer API — declared surface" is exact.
