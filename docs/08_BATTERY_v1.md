# aivis BATTERY v1 — 72 tests, six blocks of twelve
## 2026-08-31 · RUNG R0 (designed, not run) · META artifact, recipient: operator

**What this is.** A matrix, not a list. Six objects × twelve tests. The count follows from the
matrix; it was not chosen first. Every test names its probe, its pass evidence, the highest
rung a pass can earn, and the skill it exercises. The skill column is the point: the battery is
the *population* from which the skills inventory is computed, so the inventory is derived from
evidence rather than typed from memory.

**Scoring.** Each test is one of PASS / FAIL / ABSTAIN, with a tag. ABSTAIN = not runnable
now and says why. **No composite score** — a weighted composite would be the least informative
thing buildable here (04 §1). Report per block as `PASS a · FAIL b · ABSTAIN c · POPULATION 12`.

**The self-grading problem, named up front.** Blocks A–E test things a stranger could re-run.
Block F tests the operator's own process and is graded by the operator. The corpus has scored
itself favourably twice on record (03 Part C). So every Block F test passes **only on a file
with a git date**, never on recollection, and every F result carries `[SELF]` in addition to
its tag. A Block F pass without a file is a FAIL.

**Prerequisites, in order.** (1) One live API call — Block C is inert without credits and
credits were exhausted at last measurement [QUOTED: 02, 2026-08-20]. (2) Hours logged per
lane before starting; this battery is Lane I and counts against the spend gate. (3) Every
probe is read-only or writes to a *new* path. No test in this battery deletes anything.

---

## BLOCK A — SOFTWARE (does the code do what the documents say it does)

| ID | Test | Probe | PASS evidence | Ceiling | Skill |
|---|---|---|---|---|---|
| A01 | Clean-shell install | fresh venv, `pip install -e .`, `aivis --help` | exit 0 in a shell with no prior state | R2 | S8 |
| A02 | Suite on HEAD | `pytest -q` | count recorded with commit hash; 02's 97/3 amended if different | R1 | S8 |
| A03 | Dependency truth | declared `typer` spec vs `pip show typer` | declared range contains installed version | R1 | S8 |
| A04 | Unlink guard (B1) | `aivis smoke` with default `--out` against an existing file | refuses; a test asserts the refusal | R1 | S11 |
| A05 | Verifier recomputes from raw text | flip one byte of `response_text`, run `verify_hashes()` | MATCH → MISMATCH on that row | R2 | S1 |
| A06 | Digest is order-sensitive | reverse row order of an evidence file, recompute `bundle_digest` | digest changes | R2 | S1 |
| A07 | Stub cannot false-green | run stub path, inspect artifact | artifact carries a STUB marker; DISTINCT=1 is labelled as stub | R1 | S5 |
| A08 | No secret in history | `git log -p \| grep -E 'sk-ant\|AKIA\|ghp_'` | 0 hits, population = full history | R1 | S11 |
| A09 | Reproducible emit | same evidence file → PDF twice | identical digest both times | R1 | S1 |
| A10 | Evidence row schema | every row has payload, response_text, sha256, bank_version, model, temperature | count of complete rows = ROWS | R1 | S1 |
| A11 | Cross-version refusal (I-11) | compare two files with different `bank_version` | refuses with a named reason | R1 | S2 |
| A12 | Checker co-versioned with emitter (B3) | `git ls-files` for proof tool in aivis repo | same repo, same commit | R1 | S11 |

## BLOCK B — MEASUREMENT (do the numbers mean what they claim)

| ID | Test | Probe | PASS evidence | Ceiling | Skill |
|---|---|---|---|---|---|
| B01 | DISTINCT > 1 on a delivered artifact (RR-1b) | live 5 prompts × 2 runs, versioned out paths | DISTINCT ≥ 2 and digest verified | R2 | S1 |
| B02 | Intervals reach the page | `Dimension.low/high` on a live report | not None; printed beside the point estimate | R1 | S2 |
| B03 | Every count prints its denominator | grep report for counts without `n=` | 0 orphan counts | R1 | S4 |
| B04 | Abstention rate computed | from a named population of runs | rate + population + STATUS=COMPLETE | R1 | S2 |
| B05 | Order-flip delta | run bank in both orders | delta printed; RANK_WITHDRAWN stays if large | R1 | S2 |
| B06 | κ sample reproducible | re-run `kappa_sample.py` with seed 20260830 | byte-identical to `kappa_sample_v1.json` | R2 | S3 |
| B07 | κ preflight hash | every sample `(corpus,line)` hashes to sealed `sha256` | 100/100 — currently NO CHECK EXISTS [MEASURED: grep 2026-08-31] | R2 | S3 |
| B08 | κ unit matches §4 | read `kappa_compute.py` join; only `lower()` found [MEASURED: 2026-08-31] | unit = (response × candidate domain) or deviation amended by append | R1 | S3 |
| B09 | Alpha without merging | two label files → Krippendorff's α | computed on raw strings; disagreements listed, not resolved | R1 | S3 |
| B10 | Bootstrap reproduces | seed + B=20,000 on published rates | 77.0 / 67.9 / 63.8 ± rounding | R2 | S2 |
| B11 | Collinearity regression | for every dimension pair, check linear identity | none sums to a constant (the SRS=100−PS catch, automated) | R1 | S2 |
| B12 | No interval → ABSTAIN | any metric lacking run-level data | prints ABSTAIN, not a point | R1 | S4 |

## BLOCK C — PERFORMANCE (what it costs, how fast, how stable) — ALL BLOCKED ON CREDITS

| ID | Test | Probe | PASS evidence | Ceiling | Skill |
|---|---|---|---|---|---|
| C01 | Credits live | one call | 200, request id recorded | R1 | S12 |
| C02 | Unit cost re-measured | 30 calls, billed tokens | figure vs $0.007602 [MEASURED: P24]; amend if drifted | R1 | S12 |
| C03 | Latency | p50 / p95 over 30 calls | both printed with n | R1 | S8 |
| C04 | Determinism at T=0 | 10 identical calls | DISTINCT count printed; "not deterministic" stays or goes on evidence | R1 | S2 |
| C05 | Parse-error rate | observed over I-3's run | rate + n; sets I-8 threshold (replaces the 10% guess) | R1 | S3 |
| C06 | Full bank cost & time | 30 × 3 on one engine | actual vs $0.68 [EST] | R1 | S12 |
| C07 | Rate-limit behaviour | 90 calls unthrottled | retries logged; no silent drops; row count = attempts − named failures | R1 | S8 |
| C08 | Second engine end-to-end | one prompt, one run | row with distinct `model` field, hash-verified | R1 | S8 |
| C09 | N ≥ 7 per combo | config | N printed on report face | R1 | S2 |
| C10 | MDC computed | from C09's N and observed variance | N and MDC published together | R1 | S2 |
| C11 | Engine error → no fabricated row | force a 401 | row absent, failure logged, count reconciles | R1 | S5 |
| C12 | Stability carries an interval | N ≥ 7 run-level data retained | interval printed or ABSTAIN | R1 | S2 |

## BLOCK D — PRODUCT (the artifact a buyer receives)

| ID | Test | Probe | PASS evidence | Ceiling | Skill |
|---|---|---|---|---|---|
| D01 | Report from a live run | not the specimen | zero ⟦ ⟧ placeholders | R2 | S9 |
| D02 | SPECIMEN banner when any placeholder | grep for ⟦ and for banner | banner present iff placeholders present | R1 | S4 |
| D03 | Rung on the face | first page | rung printed | R1 | S4 |
| D04 | Banned words absent | grep report for the §6 list | 0 hits, population = full report text | R1 | S4 |
| D05 | Placeholders never quoted | grep 02–07 and any outbound for ⟦ content | 0 hits | R1 | S4 |
| D06 | Verifier is independent | fresh venv **without** aivis, run `verify_report.py` | MATCH using stdlib only | R2 | S1 |
| D07 | Digest binds | PDF digest vs recomputed | equal | R2 | S1 |
| D08 | Invariants public and chained | fetch method page, recompute receipt | digest matches receipt; date provable | R2 | S1 |
| D09 | Taxonomy public, bank withheld | fetch repos | categories visible, instantiated prompts absent | R1 | S11 |
| D10 | Limitations predate findings | git dates of limitations block vs results | earlier commit | R1 | S9 |
| D11 | Every load-bearing number tagged | grep numbers vs tags in report | ratio printed; 100% or amended | R1 | S4 |
| D12 | "What do I do Monday" | a reader not the operator names the three actions and their costs unaided | recorded verbatim | R3 | S9 |

## BLOCK E — CONCEPT (does the position exist in the market, not the documents)

| ID | Test | Probe | PASS evidence | Ceiling | Skill |
|---|---|---|---|---|---|
| E01 | Inbound answered (M0) | reply sent | their response recorded verbatim; OUTBOUND line updated | R3 | S10 |
| E02–E06 | Five screened conversations | one sealed prediction file per conversation, dated before the call | five transcripts | R3 | S10 |
| E07 | B0 evaluated | count against sealed rule ≥2/5 unprompted | PASS/FAIL recorded; kill rule honoured either way | R3 | S7 |
| E08 | Nine vendor pages re-fetched | all nine, today | every "0 of 9" recomputed with date; plan re-derived if any moved | R2 | S6 |
| E09 | Zeo Radar conflict resolved | re-fetch | one record, tagged | R2 | S6 |
| E10 | A stranger runs the verifier | send artifact + verifier | their MATCH output, recorded | R3 | S1 |
| E11 | A stranger pays | pilot delivered, payment clears | `pilot_001_delivered_v1.json` | R4 | S10 |
| E12 | Causal null still stands | dated literature re-check, three routes | null confirmed or the moat amended | R2 | S7 |

## BLOCK F — OPERATOR PROCESS (where the skills live) — every result `[SELF]`, file-dated only

| ID | Test | Probe | PASS evidence | Ceiling | Skill |
|---|---|---|---|---|---|
| F01 | Pre-registration precedes runs | git dates of sealed files vs run files | every study: seal < run | R1 | S2 |
| F02 | Receipts verify offline | `chain_receipt.py` on published invariants | MATCH | R2 | S1 |
| F03 | Ledger has no leaks | count items on prior board vs count in carry-forward | equal; population both printed | R1 | S11 |
| F04 | Fabrication log complete | six incidents, each with mechanism | file exists, 6 entries [QUOTED: memory] | R1 | S5 |
| F05 | Tag coverage | count load-bearing numbers vs count tagged in 02–07 | ratio printed | R1 | S4 |
| F06 | No destructive git ops | `git reflog` for reset --hard / force push | 0, population = reflog | R1 | S11 |
| F07 | Outbound integers computed | population named each session | grep for `OUTBOUND:` lines lacking a population | R1 | S10 |
| F08 | Amendment-by-append applied | every falsified line has an `## AMENDED` block | count falsified = count amended | R1 | S11 |
| F09 | DEFEATED-BY on every step | grep 05 | steps without one listed | R1 | S9 |
| F10 | Three-route derivation on record | at least one count derived three ways | file cites the three routes | R1 | S2 |
| F11 | Teardown reproducible | a stranger re-fetches 07's URLs | same structure found, recorded | R3 | S6 |
| F12 | Spend gate logged | hours per lane in 02 | logged at lane switch, not reconstructed | R1 | S11 |

---

## THE SKILLS — computed from the battery (population: 72 tests)

Each skill lists the tests that exercise it, the artifacts on record that already evidence it,
and what makes it **repeatable** — i.e. what would have to be packaged so a second person, or
you on a different project, could run it without this project's context.

| ID | Skill | Tests | Evidence on record | Repeatable form |
|---|---|---|---|---|
| S1 | **Evidence engineering** — content-addressed logs, hash chains, recipient-side verifiers | A05 A06 A09 A10 B01 D06 D07 D08 E10 F02 | `evidence.py`, `verify_evidence.py`, `chain_receipt.py`, `Rehanrana11/evidence-verify` v0.3.0 [QUOTED: memory] | one stdlib verifier + a spec: row schema, digest definition, verification recipe |
| S2 | **Measurement design** — pre-registration, intervals, denominators, MDC, collinearity checks | B02 B04 B05 B10 B11 B12 C04 C09 C10 C12 F01 F10 | sealed B0/κ protocol, bootstrap CIs, the SRS=100−PS catch, Bonferroni-Wilson pipeline | a pre-registration template + a "denominator audit" checklist |
| S3 | **LLM evaluation & labelling ops** — golden sets, blinded labelling, inter-rater agreement | B06 B07 B08 B09 C05 | κ apparatus (`kappa_sample.py`, `kappa_label.py`, `kappa_compute.py`), EVAL_MASTERY_24 | the labelling kit as a standalone repo with its rules-before-labels doc |
| S4 | **Claims discipline** — rung ladder, provenance tags, banned-word lists, placeholder marking | B03 B12 D02 D03 D04 D05 D11 F05 | charter §5–6, the specimen banner, six-tag system | a one-page claims policy any team could adopt |
| S5 | **Agentic-AI operation under verification** — bash-first probes, fabrication detection, gates that check truth not existence | A07 C11 F04 | six recorded fabrication catches with mechanisms; probe-and-paste protocol | a written protocol: what an AI may assert, what must be pasted back |
| S6 | **Competitive teardown from public sources** | E08 E09 F11 | 07_TEARDOWN (R2, stranger-checkable in an hour), 04_VENDOR_SCAN seven dimensions | the seven-dimension gate + the URL-structure method |
| S7 | **Study design** — natural experiments, confounding, power, pre-committed outcomes | E07 E12 | Credible PR cohort design (07 §7), PR-agency sealed study, segmentation insight | a design memo template: intervention, control, MDC, failure modes, pre-commit |
| S8 | **Python tooling** — CLIs, pipelines, tests, dependency hygiene | A01 A02 A03 C03 C07 C08 | aivis CLI, study pipeline, 97/3 suite [QUOTED, decayed] | ordinary; the differentiator is S1–S5 wrapped around it |
| S9 | **Writing for adversarial readers** — limitations first, DEFEATED-BY, "what do I do Monday" | D01 D10 D12 F09 | the specimen's three-decisions structure, 05's DEFEATED-BY lines | a report spec (the specimen, once a real run fills it) |
| S10 | **Buyer discovery & outreach without claims** — screened conversations, warm-lead separation | E01–E06 E11 F07 | B0 screen design; Tempur-Pedic point-of-sale access; **0 sent to strangers** [QUOTED: 02] | this is the least evidenced skill on the list and the one the plan says matters most |
| S11 | **Process governance** — destruction lock, carry-forward ledger, amendment-by-append | A04 A08 A12 D09 F03 F06 F08 F12 | the charter itself; 43-thread loss diagnosed and fixed structurally | the charter, stripped of aivis specifics |
| S12 | **Cost engineering** — unit cost, spend gates, cost-per-gap tables | C01 C02 C06 | $0.007602 [MEASURED: P24]; Annex A cost table | a cost-per-decision table format |

**Reading the map honestly.** S1, S2, S4, S5 and S11 are the ones with the most artifacts
behind them and the ones no reviewer questioned — they are also the rarest combination on the
market, because most people who can do S8 have never done S2, and most who can do S2 have
never operated an AI agent under S5. S10 is the thinnest and is load-bearing for everything
else, which the plan already says.

**Not in this file, deliberately:** value, demand, and where the work is. That needs live
market data — job postings, contract rates, which titles map to S1–S5 — and it is a search
task, not a design task. It follows this one.

---
BATTERY v1 · RUNG R0 · 0 of 72 run · POPULATION 72 · STATUS=COMPLETE (design)

## RESULTS LEDGER
| Date | Test | Result | Evidence |
|---|---|---|---|
| 2026-09-01 | C01 | PASS | HTTP 200, msg_011CecoBQr85qo7utX1NnLsK, claude-haiku-4-5-20251001 [MEASURED: curl] — falsifies 02 "credits exhausted [QUOTED: 2026-08-20]"; 02 to be amended |
| 2026-09-01 | A02 | PASS | 97 passed / 3 xfailed on f271f75 [MEASURED] |
| 2026-09-01 | A03 | PASS | typer 0.27.1 declared = installed [MEASURED] |
| 2026-09-01 | A04 | FAIL | cli.py:195 out.unlink() present, no guard, no refusal test [MEASURED] |
| 2026-09-01 | A08 | PASS | 0 credentials, full history; 3 hits all length-21 documented exposure notice. Spec amended: pass = 0 hits excluding enumerated notices [MEASURED] |
| 2026-09-01 | A10 | PASS | mattress 194/194, pr_agency 191/191 COMPLETE [MEASURED] |
| 2026-09-01 | B06 | PASS | byte-identical 4cc3563d... via: kappa_sample.py --seed 20260830 --n 100 --corpus study2/data/mattress_run2.jsonl:study2/config/prompts_mattress_premium_v1.json --corpus study2/data/pr_agency_run4.jsonl:study2/config/prompts_pr_agency_v1.json — invocation now on record [MEASURED: R2] |
| 2026-09-01 | D05 | PASS | 3 hits = battery's own spec text, population repo docs [MEASURED] |
| 2026-09-01 | D06 | PASS | clean container, no aivis, stdlib; 3 attack classes caught [MEASURED: R2, third party] |
| 2026-09-01 | D08 | PASS | anon clone aivis-method 44a1c55; chain LINKS 2/2, 3 hash routes agree [MEASURED: R2, third party] |
| 2026-09-01 | F02 | PASS | offline verify after clone [MEASURED: R2] |
| 2026-09-02 | A04 | PASS | guard + test test_unlink_guard.py, commit 5fc559b [MEASURED] |
| 2026-09-02 | B01 | PASS | smoke_evidence_20260901_live_v1.jsonl ROWS=7 DISTINCT=7; bundle_digest acea2d7a... printed in PDF AND recomputed independently, equal. SHAPE DEVIATION: 1 prompt x 7 runs, not 5x2; pass property (DISTINCT>=2, digest bound) met [MEASURED] |
| 2026-09-02 | B02 | PASS | live page prints "100% [95% CI 64.6%-100.0%, n=7]"; pypdf extraction [MEASURED] |
| 2026-09-02 | B07 | PASS | verify_kappa_sample.py 100/100, 0-based calibrated, commit 93ac50c [MEASURED] |
