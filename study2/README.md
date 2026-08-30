# RANKING-FACTOR STUDY — RUNNABLE PIPELINE
## Category 1: cosmetic practices, NY/NJ/CT · 2026-08-29 · RUNG R1 (ran on this machine, synthetic data only)

**Cost: $4.79** [EST: 630 calls × $0.007602]. 30 prompts × 7 runs × 3 engines, open-ended.

Five of seven stages are automated. Two are yours and cannot be scripted — a script that
generates them is a script that fabricates them.

---

## SETUP (once)

    unzip / copy this folder somewhere, then:
    cd study
    chmod +x run_study.sh bin/*.sh bin/*.py
    export ANTHROPIC_API_KEY=sk-ant-...
    export OPENAI_API_KEY=sk-...
    export XAI_API_KEY=xai-...

You need at least one key. Three gives you the three-engine design.

---

## STAGE 1 · PROBE — automated, 5 seconds

    ./run_study.sh probe

Places one real call per engine and writes `out/probe_receipt.json` with the HTTP code and
response ID. **If this fails, nothing downstream will run.** That is deliberate: a prior
attempt at this study reported 1,260 calls of telemetry with zero calls placed.

---

## STAGE 2 · THE SAMPLE — **THIS IS YOUR JOB**, ~4 hours

    cp config/sample_worksheet_TEMPLATE.csv config/sample_worksheet.csv

Open it and fill 50 rows by hand. 25 pairs. For each pair, two practices that match
**exactly** on metro, size band and founding decade.

Where to get the rows: state medical board listings, RealSelf, practice websites, LinkedIn
for provider counts, state business registration for founding year. Every size and founding
figure needs a URL in the source column — the validator rejects "estimate".

**The one rule that makes or breaks the study:** do not look up whether a practice is
AI-recommended before you fill this in. You are choosing 50 comparable practices, not 25
winners and 25 losers. The split is assigned in stage 5 from measurement. If you pick
knowing the answer, no downstream statistic recovers it.

    ./run_study.sh validate

Drops any pair that doesn't match on all three variables and prints the drop count. If fewer
than 25 pairs survive, it abstains. Add pairs — do not relax the matching.

---

## STAGE 3 · COST PLAN — automated, instant

    ./run_study.sh plan

Prints the call count and cost. Places no calls. Read it before spending.

---

## STAGE 4 · MEASURE — automated, ~40 minutes

    ./run_study.sh measure

630 open-ended calls at temperature 0. Every row stores the raw response, the request
payload, a SHA-256 and a timestamp to `data/runs_<timestamp>.jsonl`. Nothing is overwritten;
the script refuses an existing output path.

The prompts do **not** name your 50 practices. That is the point — you are measuring who the
models retrieve unprompted, not who they recognise when handed a list.

---

## STAGE 5 · SCORE — automated, instant

    ./run_study.sh score

Assigns ranked / middle / non-ranked by **pre-registered tertile of the observed top-three
rate on buyer-intent and comparison prompts**. Percentiles rather than an absolute bar,
because an absolute bar cannot be pre-registered without knowing the distribution, and
setting one after seeing the data breaks the seal.

The middle tertile is discarded. That is not waste; it is the contrast the design depends on.

---

## STAGE 6 · CODING — **THIS IS YOUR CONTRACTORS' JOB**, ~8 hours each

    ./run_study.sh sheets

Writes shuffled, unlabelled sheets to `out/coding_sheets/`. Hand `coder_01..04.csv` to four
people and `coder_99_DOUBLE.csv` to a fifth for the 20% double-code.

**Never send them `data/BLIND_KEY_DO_NOT_SHARE.json` or `data/code_id_map_DO_NOT_SHARE.json`.**
A coder who knows which brands are ranked will find the features that explain it. Blinding
costs one shuffle and is the cheapest quality control in the study.

Before they start, you need the sealed codebook: 8 features, F1–F8, each with a definition a
second person could apply without asking you a question. Run prompt 09 in DESIGN mode to
produce it. Date it. Nothing gets coded until it exists.

Coders enter 1 or 0 per feature. Nothing else.

---

## STAGE 7 · ANALYZE — automated, instant

    ./run_study.sh analyze

Per feature: prevalence in each group with denominators, the difference, a 95% interval
uncorrected and Bonferroni-corrected over 8 tests, a per-size-band breakdown that flags
size proxies, and inter-coder agreement from the double-coded subset.

**If nothing separates, it prints H1 FALSIFIED and says the action list does not exist.**
That is a result, it is publishable, and it is the one outcome nobody else in this category
will ever put in writing. Do not shorten the list to avoid it.

---

## WHAT THIS PIPELINE WILL NOT GIVE YOU

Causation. This is a matched case-control design and it produces association only. "Practices
with X are more often recommended" is supportable. "X gets you recommended" is not, at any
sample size. The causal claim needs a staggered before/after intervention study, which is a
separate budget and a separate quarter.

---

## KNOWN STATE

    Pipeline tested end-to-end on synthetic data 2026-08-29: signal detected, noise rejected.
    Never run against live engines. RUNG R1.
    Real sample: 0 of 50 rows.
    Codebook: not written.
