# 03 · LOCKED — measurements that cannot be recomputed, and defects that are still armed

Two lists. Both exist because the old project lost **43 live threads across 19 sessions with
zero deletions** — purely by not being retyped. Everything here is carried in full, every
session, or it is gone.

---

## PART A — IRREPLACEABLE MEASUREMENTS

These cost real API spend, real machine time, or a one-off condition that no longer exists.
Re-deriving them is expensive or impossible. **Nothing here may be re-typed from memory into
another document without carrying its tag.**

| Measurement | Value | Tag |
|---|---|---|
| Unit cost per measurement | **$0.007602** | [MEASURED: P24] |
| — the misreading to never repeat | `$0.007366` was a misread of the same figure; corrected on record | [QUOTED: register] |
| Bank size | **30 prompts**, five families of six | [MEASURED: config/prompts_v1.json] |
| — the wrong figure still circulating | 810 prompts / $6.16 — **WRONG**, do not budget from it | [QUOTED: correction 2026-08-20] |
| Battery result | **V = 0 of 24** delivered outputs on HEAD, abstention rate 0.375, per-probe rungs recorded | [MEASURED: battery-run-v3] |
| Evidence-file table | ROWS/DISTINCT across six files: DISTINCT=1 in five of six; the sixth (`live_smoke_runs.jsonl`, DISTINCT=5) pairs with a pre-B3 PDF carrying no evidence section | [MEASURED: 2026-08-20] |
| — the sentence that follows from it | *"The evidence trail and distinct per-row hashes have never coexisted in a delivered artifact."* | [DERIVED] |
| `bundle_digest` definition | SHA-256 over the **newline-joined** per-run response hashes, **in run order** | [QUOTED: `src/aivis/evidence.py`, sole commit `3e322a9`] |
| Disk encryption on the host | BitLocker = 1 on `C:` | [MEASURED: powershell probe 2026-08-19] |
| Portfolio secret exposure | **0**, at HEAD and in all history | [MEASURED] |
| Suite at last observation | 97 passed / 3 xfailed on `41bc7eb` | [QUOTED: -19g] — decayed |
| Stub behaviour | `run_once_stub` returns a **constant string and ignores its prompt argument** | [QUOTED: `runner.py:137-165`] |
| Battery self-versioning | `battery-run-v3.jsonl` and `v4.jsonl` are **byte-identical** — the battery embeds no clock, ref, or self-version | [MEASURED] |
| — the consequence | Every `[MEASURED: battery-run-vN]` tag in the corpus is anchored only by a hand-typed note | [DERIVED] |

### From the 2026-08-27 CAAI re-scoring (new, computed this session)

| Measurement | Value | Tag |
|---|---|---|
| CAAI v1.0's fifth dimension is collinear | `SRS = 100 − PS` **exactly**, all three brands, delta 0.00 | [MEASURED: recomputation, 3 routes] |
| — the honest collapse | `.45·PS + .25·DS + .20·SS + .10·(100−FI)`, weights sum to 1.00, reproduces the published scores exactly | [DERIVED] |
| — the consequence | Presence carried **45%** of the composite while presented as 25% | [DERIVED] |
| Bootstrap CIs at n=30 (B=20,000) | Purple 77.0 [72.8–80.8] · Casper 67.9 [62.9–72.7] · Tempur 63.8 [58.6–68.8] | [MEASURED] |
| Separation | P(Purple>Casper)=0.998 · P(Purple>Tempur)=1.000 · **P(Casper>Tempur)=0.870, NOT separated** | [MEASURED] |
| — the caveat that must travel with it | SS and FI carry no interval (run-level data unavailable), so the composite interval is **narrower than the truth** and these probabilities are **upper bounds** | [DERIVED] |
| Weight sensitivity | Rank 1 holds under all four weightings; ranks 2/3 invert under dominance-led | [MEASURED] |

---

## PART B — ARMED DEFECTS

Live hazards. Each was measured, written down, and then dropped off every subsequent board
in the old project. **Carry all of them, every session, until each is DONE or
DROPPED-BECAUSE.**

### B1 · `aivis` `cli.py:194-195` — unconditional unlink
```
if out.exists(): out.unlink()
```
No flag, no prompt, against a default of `data/audits/smoke_runs.jsonl`. **An unlink with no
confirmation, in a product whose entire proposition is evidence integrity.**
Carried since 2026-08-20; absent from every board after.
**Interim rule, binding:** never run `aivis smoke` without explicit versioned `--out`,
`--aggregate-out`, `--pdf-out`, `--evidence-out`.
**Fixing it edits an existing file → needs a named "go".**

### B2 · GitHub PAT expires ~2026-08-30
Three days from this document's date. Nothing schedules its rotation. Carried since
2026-08-23. **Highest urgency item in this file by calendar.**

### B3 · The proof tool is not versioned with the product it proves
`proof_aivis_pdf_v0_*` lives in `sdlc-designer/tools/`; aivis lives in `caai-test/`. Drift
between checker and emitter is undetectable. This is the best available explanation for a
historical `BUNDLE_DIGEST_IN_PDF=True` that was **arithmetically impossible** and reached a
state document anyway.

### B4 · `_patch_v1` is a pre-D4 elder — a `cp -r` of it reverts the citation fix
Carried in four destruction queues, then dropped. **Still armed and no longer on any list.**

### B5 · Eight `accepted_non_claims` entries, "unconfirmed by operator"
Every "unrowed 0" measurement since 2026-08-17 rests on an unreviewed suppression list.
It is the ledger's trust boundary and it has never been read.

### B6 · `canonical.py`'s 100% mutation score was measured by a harness with a known stale-`.pyc` bug
The decision on record was explicit: **"may not be quoted anywhere until re-run."** It has
been quoted since. The re-run never happened.

---

## PART C — THE LESSONS THAT COST SOMETHING TO LEARN

Short, and each one was paid for.

- **M9 — awareness is not a control.** Measuring a problem does not fix it. A rule with no
  runnable check is a ritual, and rituals fail.
- **Verify the verifier.** Two bugs were found in the mutation harness itself. Five fork
  guards survived every mutation because the test harness never built trees deeper than one.
- **A caveated green gets quoted without its caveat.** That is how an impossible `True`
  reached a state document. Split the row instead of caveating it.
- **A number that moves in the direction you want is the number to distrust on sight.** The
  battery harness scored itself favourably twice.
- **Agreement between instruments that share an assumption is not confirmation.**
- **A claim retired on faulty evidence is a second incident, not a fix.**
- **Every control that held was structural; every voluntary rule was broken at least once.**
  What made refusal safe was the container lacking a credential, not the rule.
- **A 97-green suite shipped a CLI that crashed from a clean install** — `typer ^0.12.3`
  declared, `0.27.1` tested.
- **Fabricated citations appeared in an audit about process discipline** ("the Q19 standard",
  "the Q17 screen" — zero hits across 78 documents). And on 2026-08-27, a fabricated model
  transcript appeared in a report about not fabricating things. **This failure recurs. It is
  not a one-off.**
- **When a convention requires destruction to achieve an effect, check whether a new file
  achieves the same effect first.** It usually does.
## AMENDED 2026-08-29 — session 3

Everything below was measured or computed this session. Sources are named per row.
Supersedes: 13_HANDOFF §1's "30 prompts × 7 runs" and its n=110 brand table; the
Part A line "the evidence trail and distinct per-run hashes have never coexisted in
a delivered artifact"; and 02_START_HERE's RR-1b RED.

---

### A · MATTRESS RUN — corrections to 13_HANDOFF §1

| Measurement | Value | Tag |
|---|---|---|
| `sha256` is over `response_text` alone | 194 of 194 clean rows recompute identically | [MEASURED: recomputation, `mattress_run2.jsonl`] |
| `request_payload` populated on clean rows | 194 of 194; carries model, temperature, max_tokens, message | [MEASURED] |
| — consequence | 02_START_HERE's "raw response + request payload + SHA-256" is TRUE for this file. STATUS=COMPLETE, denominator 194 | [DERIVED] |
| Byte-level non-determinism at temp 0.0 | 194 distinct texts of 194 | [MEASURED] |
| Decision-level, groups at exactly n=7 | identical brand SET **3 of 27** · identical first-three **10 of 27** | [MEASURED] |
| — the distinction that must travel | byte-difference is NOT decision-difference. Kirsten et al.'s 9–28% is a decision figure; only the row above is comparable to it | [DERIVED] |
| Bank id collision | `prompts_mattress_premium_v1.json`: 30 entries, **24 distinct ids**, 30 distinct texts. MT-C01–C06 each appear under `category` and `comparison` with different text | [MEASURED] |
| — the leak | `{p["id"]: family}` is last-writer-wins, so all 12 filed as `comparison`. 42+42+26 = **110**, exact. The n=110 set was 24% broad-category prompts | [DERIVED] |
| — recovery | complete, from `request_payload.messages[0].content`. Zero unmapped rows. No re-run needed | [MEASURED] |

**Corrected table — TRUE comparison + buyer_intent, n=84, Claude only, 20-name regex:**

| Brand | Mention | First-3 by position |
|---|---|---|
| Purple | 100.0% | 71.4% |
| Tempur-Pedic | 98.8% | 94.0% |
| Saatva | 83.3% | 70.2% |
| Helix | 47.6% | 2.4% |
| Casper | 42.9% | 20.2% |

**The n=110 table in 13_HANDOFF §1 may not be quoted anywhere.**

---

### B · PR-AGENCY RUN — first sealed study this project has run

| Measurement | Value | Tag |
|---|---|---|
| Pre-registration sealed before the run | `14_PREREG_pr_agency_v1.md`, sha256 `fec11fb2…`, sealed 2026-08-29T17:41:21Z | [MEASURED: `out/prereg_seal_20260829.txt`] |
| Run | `pr_agency_run4.jsonl` · 210 attempted · **191 clean** · 19 transport errors | [MEASURED] |
| Bundle digest | `9eb756a2ca6ae2175bfe55a09d5b2c99b30e1451c2cd60050ddc0d1e2ee4abea` | [MEASURED: computed independently by `verify_evidence.py` and `make_report.py`, agreeing] |
| Hash identity | 191 of 191 | [MEASURED] |
| Byte-distinct at temp 0.0 | 191 of 191 | [MEASURED] |
| **Runs per prompt is 5, 6, AND 7** | errors were unevenly distributed; pooled rates are unequally weighted | [MEASURED: `make_report` instrument record] |
| Credible PR present | **0 of 191**, all five families. Denominator 191, STATUS=COMPLETE for this file | [MEASURED] |
| Sealed outcome fired | **C**, with a correction: boutiques of comparable size DO appear (Clarity PR 11.5%, Reputation Ink 7.3%, Reputation Rhino 5.8%, Brandstyle 5.2%) | [MEASURED] |
| — why the n=10 pilot died | Clarity PR is `category`-only (4 prompts, 1 family). The "visible" group is not visible at buyer intent. `15_PILOT` is SUPERSEDED, uncoded | [DERIVED] |
| — the arithmetic that killed it | at 4 vs 6 with 8 features, Bonferroni bar is 0.00625; **only a 4/0 split clears it** (Fisher p=0.0048). 3/4 vs 0/6 gives 0.0333 and is noise | [MEASURED: computed 2026-08-29] |
| Criteria at buyer intent (n=41) | pricing 75.6% · media relationships 51.2% · realistic promises 43.9% · self-service 39.0% | [MEASURED: `criteria_miner`, CANON declared] — **unvalidated parse** |
| — the row that is not obvious | `owned_media_diy` **42.9% in `problem` (18/42)**: at the moment of pain the model teaches HARO and self-pitching; hiring a firm is one bullet among several | [MEASURED, excerpts read] |
| — the row that discriminates | `contributor_warning` 50.0% `long_tail` · 28.0% `comparison` · **0% `buyer_intent` and `category`** | [MEASURED] |

---

### C · DEFECTS FOUND, BY BLAST RADIUS

- **D0 · The runner printed `DONE. 210 rows` and `Actual cost basis $1.60` on a run
  where all 210 rows errored.** Zero calls left the machine (73s for 210 rows;
  `TypeError` building the request after a restart wiped `ANTHROPIC_API_KEY`). The
  progress counter counts rows written, not responses received; the cost line is
  `plan × unit_cost`, an [EST] printed under the word "Actual". **A run that produced
  nothing reported success.** Needs a terminal check refusing DONE at zero clean rows,
  and the cost line labelled EST or read from real usage. **UNFIXED — needs a "go".**
- **D1 · A candidate list of ≤4 with `hits[:3]` makes first-three identical to
  mention.** Produced 94.5/94.5, 39.1/39.1, 95.5/95.5. Not a finding; the slice.
  **FIXED STRUCTURALLY** — `make_report.py` refuses the column below five candidates
  and prints why. [MEASURED]
- **D2 · `max_tokens: 1024` truncated table-formatted responses.** One confirmed cut
  mid-brand-name at 2759 chars. **FIXED** — raised to 2048 at `bin/03_measure.py:73,79`
  under a named "go"; backup `03_measure.py.pre_maxtokens_20260829`. Max clean response
  went 2,882 → 4,704 chars, none near ceiling. [MEASURED]
- **D3 · Transport errors are not randomly distributed.** All 16 mattress errors fell in
  `category`; PR errors clustered in `comparison` (25 rows vs ~41). Denominators must be
  printed per family. [MEASURED]
- **D4 · February's top-3 denominator is unknown.** Feb reports Casper 80.0/10.0, a pair
  unreachable under a 3-brand candidate set. The Feb candidate list and extraction rule
  are recorded nowhere. **Any Feb-to-Aug top-3 comparison is illegal until they are.**
  [DERIVED]
- **D5 · Named false-positive vectors in the 20-name regex**: Purple (colour), Bear,
  Birch, Titan, Plank, Stearns-without-&-Foster. κ with instances attached. [DERIVED]
- **D6 · Bundle digest alone cannot detect text tampering** — it folds the STORED
  hashes, so an edited response with an intact hash passes it. Found by writing the
  checker and testing it against a tampered fixture. **FIXED** — the checker computes a
  second digest from the text and fails on divergence. [MEASURED]
- **D7 · `signal.SIGPIPE` does not exist on Windows.** Shipped in `criteria_miner.py`,
  crashed on first real use. **FIXED** with `hasattr` guard; backup
  `criteria_miner.py.pre_sigpipe_20260829`. The checker is the artifact a recipient runs
  on THEIR platform — B3's problem in a new form. [MEASURED]
- **D8 · The probe receipt survives a credential loss inside the same session.** run3
  ran at 18:15Z against a receipt written 17:34Z by a shell destroyed by a Windows
  restart. Charter §10: a gate that checks a token EXISTS rather than that it is TRUE is
  not a gate. Partially mitigated — a failed probe now deletes the stale receipt and the
  runner refuses. [MEASURED]

---

### D · BARS CLOSED

| Bar | Status | Evidence |
|---|---|---|
| **RR-1b** | **CLOSED** | 191 distinct hashes, informational rather than an artifact of `ts` in the hash [DERIVED from A above] |
| **B5 · recipient-executable verification** | **CLOSED** | `verify_evidence.py`, stdlib only, no network, no aivis install. Ran against `pr_agency_run4.jsonl`: VERDICT PASS |
| **Board item 11 · method invariants published and chained** | **CLOSED** | `github.com/Rmasood1122/aivis-method`, commit `8e55539c8d62b1dc3b48f2f441b73fc6dd7037f6`, chain head `a5614f65af7b8080de7884cb6d77aa3e9b307941e1de75077f2aad6d0a06b128` |
| — rung | **R2** | fresh `git clone` in a clean shell: LINKS OK 2 of 2, both docs MATCHES, VERDICT PASS [MEASURED 2026-08-30] |
| **B2 · GitHub PAT** | superseded in practice | HTTPS via `credential.helper manager` pushed successfully; SSH key `id_ed25519` is NOT registered on the account |

---

### E · CREDENTIAL EXPOSURE — action required

A live `ANTHROPIC_API_KEY` beginning `sk-ant-api03-dt_tskt9` was pasted into a chat
window on 2026-08-29. **Rotate at console.anthropic.com if not already done.**
`.env` created with `.gitignore` entry and `chmod 600`; still contains the literal
`PASTE_NEW_KEY_HERE`. `~/.ssh/id_ed25519` is `-rw-r--r--`, world-readable on the host.

---

### F · TOOLS BUILT THIS SESSION

| File | What it does | Rung |
|---|---|---|
| `verify_evidence.py` | recipient-side checker; two digests, tampering test passed | **R2** — clean clone |
| `make_report.py` | evidence file → report, every number computed at run time, no template | R1 |
| `criteria_miner.py` | criteria extraction against a DECLARED canon | R1 |
| `chain_receipt.py` | append-only hash chain; catches doc edits and back-dating | **R2** |
| `METHOD_invariants_v1.md` | 13a, published | **R2** |
| `prompts_pr_agency_v1.json` | 30 prompts, 30 unique ids, 5 families of 6 | R1 |
| `14_PREREG_pr_agency_v1.md` | sealed pre-registration, four outcomes committed | R1 |
| `15_PILOT_coding_sheet_pr_firms.md` | **SUPERSEDED, uncoded** — case group failed family validation | R0 |

---

### G · LESSONS, ADDED TO PART C

- **A tool can fabricate too.** Incident #6 was a model reporting 1,260 calls with no
  credentials. D0 is a *script* reporting 210 rows and a dollar figure with no calls.
  The credential gate caught the first; nothing caught the second except opening the
  file. **Check `clean`, never the console.**
- **Write the checker to find the emitter's bugs.** D6 was invisible until a tampered
  fixture was built for it. "Verify the verifier" now has a second instance.
- **The evidence trail paid for itself on our own data before any buyer saw it.** The
  family leak was fully recoverable from `request_payload` with no re-run. That is the
  product proposition demonstrated internally.
- **A short candidate list is a silent metric collapse.** D1 appeared in February's
  report, in this session's first probe, and again in new code within the hour. Only the
  structural refusal stopped it.

## AMENDED 2026-09-01 — session 4
| Item | Value | Tag |
|---|---|---|
| RR-1b | SPLIT. Precondition MET: 191 distinct clean hashes. Product `bundle_digest` exercised in tests only (`test_evidence_trail.py:135,141`). Never bound into a DISTINCT>1 delivered artifact. The 08-29 CLOSED was reached via a study2 reimplementation | [MEASURED: probes 2026-09-01] |
| B7 (new) | Three `bundle_digest` implementations — `src/aivis/evidence.py:32`, `study2/make_report.py:38`, `study2/verify_evidence.py:34`. Identical by inspection: sha256 of "\n".join(hashes), utf-8. Caller ordering unverified | [MEASURED: read 2026-09-01] |
| Error rows share one hash | `pr_agency_run4.jsonl`: ROWS 210 · CLEAN 191 · ERROR 19 · DISTINCT_CLEAN 191 · DISTINCT_ERR 1. Any DISTINCT quoted from this file is of clean rows or it is wrong by one | [MEASURED: 2026-09-01] |
| API credits | LIVE. HTTP 200, msg_011CecoBQr85qo7utX1NnLsK, claude-haiku-4-5-20251001. Supersedes "exhausted [QUOTED: 2026-08-20]" | [MEASURED: curl 2026-09-01] |
| B2 PAT | Pushes succeeded over HTTPS 2026-08-31 and 2026-09-01. Expiry date itself still unread | [MEASURED] |
| 03_APPEND_20260829 | Applied to this file's foot this session. Had lived unapplied in ~/Downloads since 08-29 — §2 failure, two days | [MEASURED] |
| 13_HANDOFF | Cited by the 08-29 append as superseded; not present in the project or on disk under ~/caai-test | [MEASURED: find 2026-09-01] |

## AMENDED 2026-09-02 — session 7, lessons added to Part C
- **`|| true` on a measurement step manufactures a false green.** A CI mutation
  job exited ✓ in 35 seconds having generated zero mutants; the error was real
  and the shell swallowed it. Identical mechanism to D0 (210 rows, zero calls).
  What caught it was the wall clock looking implausible — not a gate. **Rule: a
  step that produces a NUMBER may never carry `|| true`. Non-zero exit from a
  measurement tool is data.**
- **The environment is an assumption until it is declared.** Three instances in
  one session: MSYS `/tmp` unreadable by Windows Python; mutmut refusing native
  Windows; a test suite that passes only from the repo root because config paths
  are relative. Same family as D7 (`signal.SIGPIPE` on Windows) and B3.
- **Assert before write, always.** The `/tmp` failure crashed at the read step,
  before `write_text` — so a source file was left untouched rather than
  truncated. The ordering, not the luck, is what made it safe.
- **A fix can introduce its own defect.** The isinstance guards added for mypy
  raised ruff TRY004 (`RuntimeError` where `TypeError` belongs). The gate ran
  after the patch and caught it pre-commit. **Re-run the checker after the fix,
  never only before.**

## AMENDED 2026-09-06 — session 9: FABRICATION INCIDENT #7
**The claim:** "Vanity Fair Jewelers has two Google listings splitting their
entity; Horizon has dual-name fragmentation" — presented in a prior session as
findings from the jeweler pipeline, quoted forward across two sessions, and
used in outreach ranking before verification.
**The probes (all 2026-09-06):**
- grep both names, jeweler_openai_run1_v1.jsonl: 0 hits, POPULATION 90 rows +
  errors sibling, STATUS=COMPLETE
- repo-wide grep: "vanity" = "vanity metrics" prose in PR files only;
  "horizon" = 0 hits in pr_agency_run4.jsonl
- domain extraction on jeweler file: 0 business domains in any response;
  sole .com hit ("chat.com" x90) is the surface string "chat.completions"
  clipped by the probe regex — an extraction false positive INSIDE the
  fabrication probe itself (D5 class, second-order instance)
- Places search, Long Island: no "Vanity Fair Jewelers"; no clean "Horizon"
  match. The businesses themselves are unestablished, not just the findings.
**Mechanism:** invented detail was PRECISE ("two Google listings") and
FLATTERING to the pipeline ("found without trying"). Precision is not
provenance. Same class as incidents #5 (fabricated citations) and #6
(fabricated transcript): vivid, checkable-sounding, never checked.
**Propagation:** assistant repeated it as [MEASURED] twice in session 9
before probing — charter §7 violation on the assistant side, caught by
operator-run greps, zero cost beyond embarrassment because it was caught
BEFORE any outreach sent.
**Rule sharpened:** a finding quoted from a prior session is [QUOTED] until
its file is opened this session. OUTREACH MAY NEVER RIDE ON [QUOTED].
**Consequences applied:** both names off the outreach list; real-jeweler
alternates rebuilt from Places ground truth (SVS Oceanside, HL Gross Garden
City, Matthew James Valley Stream) [REPORTED: Places, 2026-09-06 — verify
before any send]; weekend run queue unchanged.

## AMENDED 2026-09-08 — surface-presence layer, first measurement
| Item | Value | Tag |
|---|---|---|
| Tool | study2/surface_presence.py, 15/15 tests on operator machine; canon referral_surfaces_v0.1 sha256 8655137737de2e0e… | [MEASURED] |
| Behavior modes, run4, per family | buyer_intent NAMES 7/41 REFERS 28/41 (SPARSE) · category NAMES 25/41 · comparison NAMES 12/25 · long_tail NAMES 0/42 (SPARSE) · problem NAMES 0/42 REFERS 21/42 (SPARSE) | [MEASURED: surface_presence_run4_v2.json] — unvalidated parse, 5-name seed firms list, NAMES is a lower bound |
| Top surfaces at buyer_intent | journalist_matching 16/41 · media_database 14/41 · review_marketplace 9/41 · directory 8/41 · peer_referral 8/41 | [MEASURED: same file] |
| FP probe | "Credible PR" case-insensitive: 0 hits of any case in 191 clean rows — reproduces the sealed 0/191 by a second implementation | [MEASURED: probe 2026-09-08] |
| Buyer_intent naming, refined | 7/41 genuine (Reputation Ink 4, Reputation Rhino 3); Clarity PR remains category-only (22/22 hits in category) — sealed finding confirmed, not amended | [MEASURED] |
| Caveat | problem-family journalist_matching 18/42 equals criteria_miner's owned_media_diy 18/42 — two keyword parses over one corpus, shared-assumption rule: consistency, not confirmation | [DERIVED] |

## AMENDED 2026-09-08 — four-engine delivery verified; repo map probed
| Item | Value | Tag |
|---|---|---|
| Four-engine claim (Max email) | VERIFIED: anthropic 88/90 · gemini 88/90 · openai 90/90 · perplexity 84/90 clean; MATCH 350/350 clean rows, 0 mismatch, all DISTINCT; fourth engine = Gemini | [MEASURED: verify_evidence.py on delivery files, 2026-09-08] |
| run4 force-add directive (02) | STALE — file already tracked (git ls-files confirms); directive predates the commit that picked it up | [MEASURED: probe 2026-09-08] |
| Repo map | aivis local=origin e7cdb02 · aivis-method local=origin 9b2f3fa · evidence-verify local=origin 5ca720e; all trees clean; load-bearing single-disk exposure closed by e7cdb02 | [MEASURED: git ls-remote, 2026-09-08] |
