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

## AMENDED 2026-10-07 — the audience now comes from the vertical name

Supersedes two lines above: "No default audience" under *What it will not do*, and the
`--audience b2c --vertical restaurants --local` form under *Use* (still accepted, no longer
needed). Test count is now 91 cases, not 55.

New path: `config/vertical_map_v1.json` — 40 verticals with aliases, each row
`{audience, local}`. `run_study_v1.py` takes the vertical as its one required argument:

```bash
python run_study_v1.py restaurants      # b2c, local  -> ChatGPT + Gemini
python run_study_v1.py fashion          # b2c         -> ChatGPT + Gemini
python run_study_v1.py retail           # b2c         -> ChatGPT + Gemini
python run_study_v1.py "law firms"      # mixed, local -> all four
python run_study_v1.py "pr agencies"    # b2b         -> all four
python run_study_v1.py stocks           # b2c, on Perplexity's list -> ChatGPT + Gemini + Perplexity
```

- **Matching** is exact key or alias after normalisation, plus one singular/plural retry.
  No substring or fuzzy match: "lawn care" resolves to home_services, never to law.
- **Unlisted vertical** → the map's declared `unclassified` row: `mixed`, every engine planned,
  `VERTICAL_UNCLASSIFIED` and a WARNING line printed. Nothing is guessed into b2c or b2b.
  Cost of that choice: an unlisted consumer vertical calls Claude and Perplexity until a row is
  added or `--audience` is passed.
- **`--audience` overrides the map.** The plan then records `OPERATOR` as the source and keeps
  what the map said (`map_audience`).
- **The plan carries the map's version and SHA-256** next to the policy's.
- **"law firms" is `mixed`** (consumer and corporate buyers both ask), so it plans all four.
  "personal injury lawyers" is `b2c`; "corporate law" is `b2b`.

Limit: every row of the map is an operator classification [EST]. No usage data sits behind it.
Rows may be added in place; changing an existing row's audience or local value is
`vertical_map_v2.json` with the reason stated.

Two pins hold the map and the policy together:
`test_the_rule_holds_for_every_row_of_the_map` and
`test_every_relevant_vertical_in_the_policy_is_a_key_of_the_map`.

## AMENDED 2026-10-07 (2) — any business name resolves, not only the 40 on the map

Supersedes the "Unlisted vertical" bullet in the amendment above, and the header line of
`engine_select.py` that calls selection "a lookup, no model call": the ENGINE choice is still a
pure lookup on (audience, vertical); the AUDIENCE of an unlisted name may now come from one
model call. Test count is now 122 cases across two files.

New paths: `src/aivis/vertical_classify.py`, `tests/test_vertical_classify.py`, and — created
on first use — `state/vertical_classified_v1.jsonl`.

Order for any typed name:

| Step | Source printed on the plan | Model call |
|---|---|---|
| 1. vertical map, exact key or alias | `VERTICAL_MAP` | none |
| 2. classification ledger, same name as before | `MODEL_CLASSIFIED` | none |
| 3. one short call, answer appended to the ledger | `MODEL_CLASSIFIED` | one |
| 4. no key, failed call, unreadable or "unknown" answer | `VERTICAL_UNCLASSIFIED` + WARNING | — |

```bash
python run_study_v1.py "wedding photographers"          # step 3 the first time, step 2 after
python run_study_v1.py "wedding photographers" --no-classify   # step 4, every engine planned
python run_study_v1.py "wedding photographers" --audience b2c  # operator decides, no call
```

- **The answer is kept like evidence.** Each ledger row stores the raw response text, its
  SHA-256, the prompt's SHA-256, the classifier engine and model, and the time. On every read a
  row is re-checked: the hash must match the text, and the stored audience must match what the
  stored text says. A row edited by hand is a refused ledger.
- **Append-only, first row wins.** To correct a model answer, add a row to
  `vertical_map_v1.json`; the map outranks the ledger. The ledger is not edited.
- **Step 4 never guesses.** It takes the map's declared `unclassified` row (`mixed`) and prints
  why (key missing, HTTP error, unreadable answer).
- **Not a measurement call.** It decides which engines a study calls and produces no visibility
  number. Default classifier: the Anthropic adapter already in `engines.py`
  (`--classifier-engine openai` to change). A plan for an unlisted name is therefore no longer
  free of network calls: one call, about 100 output tokens, the first time that name is seen.
- **Tests never reach a model.** The call is injected in-process; subprocess tests set
  `AIVIS_NO_CLASSIFY=1` because a subprocess reads the real `.env`.

Limits:
- A `MODEL_CLASSIFIED` audience is a model's answer [UNVERIFIED], not an operator
  classification. The plan prints "not operator-reviewed" on that line. Read it before
  `--execute`.
- The live call has not been exercised: the build environment had no API key. Covered by
  injected-call tests only; first live use is the smoke.
- `state/vertical_classified_v1.jsonl` is written on the operator's disk and is not in git
  until committed. A plan cites a row by `response_sha256`; commit the ledger with the study.

## AMENDED 2026-10-07 (3) — answer cap, and a study that must NOT be launched from here

Test count is now 126 cases.

- **`--max-tokens`, default 8192.** Earlier in the day `run_study_v1.py` passed no cap, so the
  runner's own default of 2048 applied. `restaurant_v1/run_market_v2.sh` (branch
  `claude/restaurant-v1-prereg`) records answers cut short at 2048 [QUOTED: that script's header;
  the evidence rows were not re-opened here]. The cap is now passed to every command.
- **`restaurant_v1` is a sealed four-engine design.** Its PREREG fixes ChatGPT, Claude, Gemini
  and Perplexity with search on, and metric R3 counts restaurants named by 3 or more of 4
  engines. NYC was collected on all four on 2026-10-06. `run_study_v1.py restaurants` plans two
  engines, so launching MA, DE or CT from it would change the design mid-study and leave R3
  without a denominator. Those markets stay on `restaurant_v1/run_market_v2.sh`, which also
  performs the seal check that this CLI does not. Running fewer engines there is a PREREG v2
  with the reason stated, not a flag.
- The selector applies to studies designed after it.
