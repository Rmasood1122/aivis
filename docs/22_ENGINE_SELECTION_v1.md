# 22 · ENGINE SELECTION v1 — which engines a study calls, and why

Written 2026-10-07. New paths only; no existing file was edited.

| Path | Role |
|---|---|
| `config/engine_policy_v1.json` | the policy: tiers, relevant verticals, recorded model ids, sources |
| `src/aivis/engine_select.py` | the selector (pure lookup) and the runner-command builder |
| `run_study_v1.py` | CLI: prints the plan; with `--execute` launches `run_bank_multi_v2.py` |
| `tests/test_engine_select.py` | 55 test cases, no network |

## The rule

An engine runs for a study only when it is **core** for the study audience, or
**conditional** with one condition met:

1. `--request ENGINE` — the buyer asked for it by name → `CLIENT_REQUESTED`
2. `--declare "ENGINE=reason"` — the operator writes why it is relevant (10+ characters,
   stored on the plan) → `OPERATOR_DECLARED`
3. the study vertical is on that engine's `relevant_verticals` list → `VERTICAL_RELEVANT`

Otherwise it is skipped with `CONDITION_NOT_MET`, and the skip is printed.

| Engine | b2c | b2b | mixed |
|---|---|---|---|
| openai (ChatGPT) | core | core | core |
| gemini | core | core | core |
| anthropic (Claude) | conditional | core | core |
| perplexity | conditional | core | core |

So a consumer study (restaurants, realtors) calls ChatGPT and Gemini. Perplexity and Claude
are not called unless one of the three conditions holds. A B2B study calls all four.

Perplexity's seed `relevant_verticals`: investing, personal_finance, consumer_tech,
academic_research [EST — no per-vertical usage data opened]. Claude's list is empty.

## What it will not do

- **No default audience.** `--audience` must be `b2c`, `b2b` or `mixed`; anything else is refused.
- **No surface without an adapter.** Google AI Mode, Google AI Overviews, Meta AI, Grok and
  Copilot appear on every plan as `NOT_MEASURED` with the reason. Requesting one is refused.
  Gemini with search is named as the nearest proxy for the two Google surfaces and is never
  pooled with them.
- **No command for a skipped engine.** `runner_commands()` builds one command per `RUN` row
  and nothing else, so a study launched from its plan cannot call a skipped engine.
- **No overwrite.** Plan files follow the runner's rule: an existing path is refused.
- **No swallowed failure.** `--execute` stops at the first non-zero exit and returns that code.

## Use

```bash
# plan only
python run_study_v1.py --audience b2c --vertical restaurants --local

# plan + commands, nothing called
python run_study_v1.py --audience b2c --vertical restaurants --local \
    --bank restaurants_v1/nyc_prompts_v1.jsonl --runs 5 --outdir restaurants_v1/runs

# 1 prompt x 1 run per picked engine, then the measured run
python run_study_v1.py ... --smoke --execute
python run_study_v1.py ... --execute
```

`--execute` first writes `engine_plan_<tag>_<date>.json` into `--outdir`: policy version,
SHA-256 of the policy bytes, the profile, one row per surface, and the commands.

Web search: on for `b2c` and for `--local`, off for `b2b`, unless `--search` / `--no-search`
is given. Perplexity always retrieves live.

## Model ids

Each id in the policy is the string recorded in `request_payload.model` of committed evidence;
`test_every_recorded_model_id_is_present_in_its_committed_evidence` re-reads those files.
Recorded is not the same as currently served — smoke first.

**Open defect, carried:** the only search-enabled OpenAI evidence
(`realtor_v1/runs/multi_openai_realtor_v1_20260923.jsonl`) records the resolved snapshot
`gpt-4o-2024-08-06`, not the alias that was requested. That is an older snapshot than the
consumer default named in the study2 reports. Before a B2C run: smoke-test whether the consumer
alias accepts web search, and pass it with `--model openai=<id>` if it does. The plan prints
this caveat on every search-enabled OpenAI row.

## Limits

- Usage figures in the policy are third-party numbers tagged [REPORTED], read through a page
  summary on 2026-10-07 and not opened first-hand. Re-open each source before a figure leaves
  the repo.
- Tiers are declared by the operator with those figures as the stated basis. Nothing is
  computed from them.
- B2B tiers are [EST]: no B2B usage data has been opened. They match prior practice (all four
  engines in the PR-agency study).
- Selection decides which API surfaces are called. It does not make an API surface equal to a
  consumer app; the surface notes in `engines.py` still apply.
- `run_bank_multi_v2.py` is unchanged and can still be pointed at any engine by hand. The rule
  is enforced for studies launched through `run_study_v1.py`. Putting the check inside the
  runner itself is an edit to an existing file and needs a "go".

## Changing the policy

`engine_policy_v1.json` is not edited after its first measured run. A change is
`engine_policy_v2.json` with the reason stated; the plan's `policy_sha256` shows which bytes
picked the engines for any past run.

## Owed elsewhere (existing files, need a "go")

- One carry-forward row in `docs/02_START_HERE_aivis.md` for this build and the OpenAI
  search-model defect above.
