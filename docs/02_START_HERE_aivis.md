# 02 · START HERE — aivis, as of 2026-08-27

Read this first, every session. It is the only state document. When it goes stale, amend it
by append; do not create a second one.

---

## 1. WHAT AIVIS IS

An AI-visibility measurement instrument. It runs a versioned prompt bank against AI
assistants, stores every raw response with its request payload and a SHA-256 hash, and
reports what the models say about a brand — with intervals, abstentions, and an evidence
trail the recipient can check.

**The position, stated once:** eight of nine competitors measure *demand* (what people ask),
which no third party can audit. aivis measures *supply* (what models answer), which is the
only side of this market where an adversary-proof artifact is possible.

**The rung: R1/R2.** Runs on the operator's machine. Zero customers. Zero delivered audits.

---

## 2. STATE, TAGGED

| Fact | Tag |
|---|---|
| Suite: 97 passed / 3 xfailed | [QUOTED: session-2026-08-19g] — **decayed, re-run before quoting** |
| HEAD: `606c979` on `41bc7eb`, pushed to `Rmasood1122/aivis-python-engine` | [QUOTED: 2026-08-20] — re-probe |
| Local: `~/caai-test/ai-visibility-audit`, editable install confirmed | [QUOTED: 2026-08-20] |
| API credits **exhausted** | [QUOTED: 400 invalid_request_error, req_011CeD4cHZBYXQzXLZe39kfS, 2026-08-20] |
| `BANK_SIZE=30`, five families of six | [MEASURED: config/prompts_v1.json] |
| Unit cost | [MEASURED: $0.007602 per measurement] |
| Full bank, 3 runs = 90 calls ≈ $0.68 | [EST: 90 × 0.007602] — **the 810-prompt / $6.16 figure on record is WRONG** |
| Engines wired | 1 (`ANTHROPIC_API_KEY` only) |
| RR-1a — digest binding verified on a delivered artifact | **GREEN** [MEASURED: proof_aivis_pdf_v0_3, two artifacts] |
| RR-1b — verified on an artifact with DISTINCT > 1 | **RED, BLOCKING** |
| Extractor accuracy (κ) | **never measured** |
| Delivered audits | **0** |

**Why RR-1b is red:** `smoke` is the only PDF path, runs one prompt at temperature 0, so
every artifact ever produced has DISTINCT=1. Run-ordering and newline-joining — the two
properties `bundle_digest` depends on — have never been exercised. `run_once_stub` returns a
constant and ignores its prompt, so the stub path cannot close it either.

---

## 3. THE BOARD, IN VALUE ORDER

| # | Item | Blocked on | Cost |
|---|---|---|---|
| 1 | **Answer the inbound agency** (see §5) | nothing | ~20 min |
| 2 | Five screened buyer conversations; evaluate B0 | nothing | $0 |
| 3 | Top up API credits | operator | — |
| 4 | Fix `cli.py:194-195` unlink (see 04) | a named "go" | small |
| 5 | RR-1b live run: 5 prompts × 2 runs, versioned output paths | 3 | ≈$0.08 |
| 6 | Propagate Wilson intervals (`Dimension.low/high` is `None`) | nothing | near-zero |
| 7 | Multi-prompt bank command — `cli.py` only | 3 | ≈$0.68 |
| 8 | Golden set: 100 cases, hand-labelled, no model help | nothing | 2 sittings |
| 9 | Publish κ + the labelled set + external co-labeller alpha | 8 | small |
| 10 | Recipient-side verifier — `verify_hashes()` exists, never shipped | nothing | one file |
| 11 | Method-page invariants, published and chained | nothing | writing |
| 12 | **Transcript diagnosis layer — NOT BUILT, not designed** | 7 | unknown |

**Item 12 is the newest and least understood.** Reading stored responses for recurring
causal patterns is the one analysis competitors structurally cannot perform, because none of
them keeps the text. It has a real design problem: extracting a recurring frame without an
LLM introducing exactly the unvalidated-parser error κ exists to catch.

**Pre-registered market gate (B0), sealed 2026-08-27:** in five screened conversations,
≥2 of 5 raise evidence, reproducibility, method or trust **unprompted**, before aivis is
described. If B0 fails, the position does not matter to buyers and items 3–12 are machinery
for an absent buyer.

---

## 4. OUTBOUND

    SENT TO STRANGERS ....... 0
    SUBSTANTIVE REPLIES ..... 1  (inbound, unanswered since 2026-08-27)
    POPULATION .............. all outbound about aivis, all channels, all time
    STATUS .................. n=0 is UNDERPOWERED. No demand conclusion is legal
                              in either direction.

---

## 5. THE LIVE LEAD

**Credible PR** (`crediblepr.com`) — PR/visibility agency for cosmetic practices. Sells "AI
Search Optimization" with no instrument. Approached about partnering; **not yet answered.**

Full teardown in `07_TEARDOWN_crediblepr.md`. The short version: they guarantee the thing
they can prove (placements) and assert the thing they can't (AI visibility). They accept
accountability in writing already. Market exclusivity means every client eventually asks
"am I winning in my market?" — a question only measurement answers.

**Screen rule 4 applies.** They came inbound, so they self-selected for interest. Record
them as a warm lead, **separately** from the five B0 conversations. Counting them poisons B0.

---

## 6. CARRY-FORWARD LEDGER

Every session appends a block here. One row per inherited item. Nothing leaves by silence.

### Inherited from the old project, 2026-08-27 (session 0 of the new project)

| Item | Status | Sessions carried |
|---|---|---|
| `cli.py` unlink defect | OPEN — armed, see 04 | 6 |
| GitHub PAT expiry ~2026-08-30 | **OPEN — 3 days out, nothing schedules it** | 3 |
| Golden set | OPEN — declared formally open 2026-08-18, never started | 9 |
| Wilson intervals discarded at dimension layer | OPEN | 8 |
| RR-1b | OPEN, BLOCKING | 7 |
| Five buyer conversations | OPEN — blocked on nothing, largest information gap | 8 |
| Proof tool lives in a different repo from the product it proves | OPEN | 7 |
| Everything in the old project's TEACH-250, 24X, register-merge, and rework-series tracks | **DROPPED-BECAUSE:** titan-gate scope, not aivis. Files remain in the old project. | — |

## AMENDED 2026-09-01 — session 4
- §2 "API credits exhausted" → LIVE [MEASURED: msg_011CecoBQr85qo7utX1NnLsK, 2026-09-01].
- §2 "RR-1b RED, BLOCKING" → SPLIT: precondition MET [MEASURED]; digest-bound DISTINCT>1 artifact NOT DONE. Full row in 03, 2026-09-01 block.
- This file now lives at aivis `docs/` and is canonical there. Append here, then re-upload to the project. 02–07 were not on disk anywhere under ~ before this session.
- Board additions: B7 (three digest implementations); error-row shared hash; `docs/08_BATTERY_v1.md` — 1 of 72 run (C01 PASS).
- Board item 1 unchanged: inbound still unanswered. OUTBOUND 0/1, population all channels all time.

### Carry-forward, session 4 (2026-09-01)
| Item | Status | Carried |
|---|---|---|
| `cli.py` unlink (B1) | OPEN — armed, untouched | 6 at 08-27, unlogged since |
| GitHub PAT (B2) | OPEN — pushes work 08-31, 09-01; expiry date unread | 3 at 08-27, unlogged since |
| Golden set / κ | OPEN — sample sealed, tools pushed f7deb78, 5 operator attempts voided, external labeller message drafted not sent | 9 at 08-27, unlogged since |
| Wilson intervals at dimension layer | OPEN — untouched | 8 at 08-27, unlogged since |
| RR-1b | SPLIT — see 03 2026-09-01 block | 7 at 08-27, unlogged since |
| Five buyer conversations | OPEN — 0 of 5 | 8 at 08-27, unlogged since |
| Proof tool in a different repo (B3) | OPEN — untouched; B7 is its sibling | 7 at 08-27, unlogged since |
| Inbound reply (board #1) | OPEN — six days on 09-02 | since 08-27 |
| B4 `_patch_v1` | OPEN — present untracked in working tree [MEASURED: git status 2026-09-01] | 4 queues, then dropped; re-listed |
| B5, B6 | OPEN — untouched | re-listed |
| NEW: B7, error-row shared hash, 13_HANDOFF absent, key rotation status unknown, `README.md.pre_*` and `_*_backup*` untracked and unlisted | OPEN | 0 |
| API credits | DONE — live | — |
| Battery 08 | 1 of 72 run | 0 |

### Carry-forward, session 5 (2026-09-01)
| Item | Status | Carried |
|---|---|---|
| Inbound reply (board #1) | OPEN — draft exists in session 5, unsent | since 08-27 |
| Ahmad κ message | BLOCKED-ON: repo is private, needs collaborator add; command itself verified correct | 1 |
| Battery 08 | 10 of 72 run, ledger pushed 20193ea; A04 sole FAIL | — |
| B06 spec-recording gap | DONE — invocation recorded in results ledger | 1 |
| A08 spec | AMENDED in ledger: 0 hits excluding enumerated notices | 1 |
| cli.py unlink (B1/A04) | OPEN — armed, FAIL on record, awaiting "go" | 7 |
| Key rotation check | OPEN — precedes any live run | 2 |
| Five buyer conversations (B0) | OPEN — 0 of 5 | 9 |
| Wilson intervals | OPEN — untouched | 9 |
| RR-1b digest-bound artifact | OPEN — cheapest remaining rung-changer | 8 |
| B2 PAT | OPEN — pushes work through 09-01; expiry date itself still unread | 4 |
| B3 proof tool separate repo | OPEN — B7 is its sibling | 8 |
| B4 _patch_v1 untracked | OPEN — armed, left in place | re-listed |
| B5 accepted_non_claims | OPEN — never reviewed | re-listed |
| B6 mutation score | OPEN — may not be quoted until re-run | re-listed |
| B7 three bundle_digest impls | OPEN — caller ordering unverified; public copy tested session 5 | 1 |
| Error rows share one hash | OPEN — DISTINCT quotes must say "clean" | 1 |
| 13_HANDOFF | ABSENT from disk and project | 1 |
| README.md.pre_* and _*_backup* | OPEN — untracked, left in place | 1 |
| F03 note | session 5's first carry-forward block dropped these 9 rows; completed same session by this append | — |
| 10_REPORT_SPEC_v1 | DONE — committed cf7854a, hash-verified handoff | 0 |
| Named PR report | DONE — 1710ec9; absence row 0/41 CI 0.0-8.6 printed; Clarity 11.5% reproduced 3 routes | 0 |
| Mattress report 20260901 | DONE — digest 781a341e new to record; D5 colour-Purple caveat until kappa | 0 |
| Composite ruling (v2 band: annex or nowhere) | OPEN — operator decision | 0 |
| 10_REPORT_SPEC_v1 | DONE — committed cf7854a, hash-verified handoff | 0 |
| Named PR report | DONE — 1710ec9; absence row 0/41 CI 0.0-8.6 printed; Clarity 11.5% reproduced 3 routes | 0 |
| Mattress report 20260901 | DONE — digest 781a341e new to record; D5 colour-Purple caveat until kappa | 0 |
| Composite ruling (v2 band: annex or nowhere) | OPEN — operator decision | 0 |
### Carry-forward close, session 5 (2026-09-01, part 2)
| Item | Status | Carried |
|---|---|---|
| make_pdf.py + true PDF | DONE — reconciled 3 routes; problem+long_tail 0/84 all candidates | 0 |
| 11_PILOT_CHARTER_v1 | DONE — 0a03f22; stagger fix (natural timing) OPEN as append | 0 |
| Build order v1 | DONE — appended to 10, commit 12a8f49 | 0 |
| WTP predictions (6 confidences, rows 1-6) | OPEN — unsealed | 0 |
| G0 override | LOGGED — build session next | — |
| Inbound reply / Ahmad add / key rotation | OPEN — unchanged, still outrank build | 5 days |

## AMENDED 2026-09-02 — session 6 close
RR-1b CLOSED on the product path: smoke_report_20260901_live_v1.pdf, DISTINCT=7,
digest two-route verified. Board #6 (Wilson) DONE end-to-end; original description
corrected: nothing was discarded in the product, the interval never existed there.
Battery 10 -> 14 of 72. Suite 104/3. Surface change: API rejects temperature for
claude-sonnet-5; invariant amended + chain receipt 728d9410... pushed (aivis-method
9b2f3fa). Cross-surface DISTINCT comparisons refused per amendment.
OUTBOUND 2/2 [MEASURED: Gmail]: meeting-time exchange with Tyler 09-01; Sep 8
12:30 PST confirmed; invite ACCEPTED via Calendar API [MEASURED]. Meeting intel:
Calendly intake shows Max's frame is SELLING partner services to Rehan ($2K-$10K
bands pre-collected) — prep accordingly.
### Carry-forward, session 6 (2026-09-02)
| Item | Status | Carried |
|---|---|---|
| Inbound reply (board #1) | DONE — logistics reply sent, meeting confirmed; discovery content rides Sep 8 | closed at 5 days |
| Sep 8 invite acceptance | DONE — needsAction -> accepted | 0 |
| B1 unlink / A04 | DONE — guard + test, 5fc559b | closed at 7 |
| D0 zero-clean DONE lie | DONE — 38b906e | closed |
| RR-1b | DONE — see above | closed at 8 |
| Wilson intervals | DONE — 0cba4ae, 56db675, live-verified | closed at 9 |
| B07 kappa preflight | DONE — 93ac50c | closed |
| B2 PAT | DOWNGRADED — no expiry header on gh token; pushes green 4 days past estimate; gh-vs-push token identity [UNVERIFIED] | residual |
| Charter v2 meeting copy | DONE — f264ae4 | 0 |
| 03_measure D0 + temp-v1 | DONE — 38b906e, 3c068e1 | 0 |
| KEY ROTATION CHECK | OPEN — overridden for tonight's run (logged); REQUIRED before next live run; .env still PASTE_NEW_KEY_HERE | 3 |
| Ahmad collaborator add | OPEN — Ahmad away ~3 days; add anyway when username known so return is unblocked | 2 |
| Five B0 conversations | OPEN — 0 of 5, blocked on nothing | 10 |
| WTP predictions seal | OPEN — seal BEFORE Sep 8 or the meeting contaminates them | 1 |
| B3/B7 digest impls · B4 _patch_v1 · B5 non_claims · B6 mutation | OPEN — unchanged | carried |
| chain HEAD external anchor | OPEN — 728d9410... lives only in operator-controlled repos; chain_receipt's own warning applies | 0 |
| .pre_* backups (now +3 from this session) · error-row shared hash · 13_HANDOFF absent | OPEN | carried |
| Project copy of 02 stale | OPEN — re-upload after this append | 1 |

## AMENDED 2026-09-02 — session 6 part 2 (FAANG battery)
docs/13_FAANG_BATTERY_v1.md created (66a16da), 24 of 72 measured same night.
Verdict pre-committed NOT-production-grade stands; measured deficit list, ranked:
(1) summarize_anchor complexity rank E + parse_tool_list D — refactor needs "go"
(2) runner.py coverage 32% — the live-API path is the least-tested file
(3) no lockfile, caret ranges — the typer-lesson class is live (K07 FAIL)
(4) ruff 17 errors (8 autofixable, needs "go") · mypy 7 (cli.py:223 real)
(5) key rotation still [UNVERIFIED] — precedes next live run
NEW INFRA: GitHub Actions CI live and green (first run 20s) · tag v0.1.0 ·
suite flake 0/10 · coverage 80% line/branch measured.
FALSIFIED + CORRECTED: 03 SE ".env chmod 600" was never effective (NTFS);
icacls shows ACLs were adequate all along. PROCESS DEFECT LOGGED: a ledger row
claimed "fixed" in the same paste as its failing verification — new rule:
claims never ride in the same paste as their probe.
DEFERRED (expensive tier): H03 mutation/B6 rerun · J03-J05 fault injection ·
H08 fuzzing · L01 use-case file (27 UCs seeded in 13).

## AMENDED 2026-09-02 — session 7 close (FAANG-deficit session)
Scope was 13's ranked deficit list; all 7 items resolved. HEAD ba0b399, CI green,
suite 115/3 (was 104/3), coverage TOTAL 90% line (was 80%), ruff 0, mypy 0.
Battery 13: 24 -> 31 of 72. Battery 08: unchanged at 14 of 72.
No live API calls this session, so the key-rotation gate was never triggered;
it still precedes any live run.
THREE ENVIRONMENT-ASSUMPTION DEFECTS, same class, all found tonight:
  (1) MSYS /tmp != Windows C:\tmp — Windows Python could not read a bash-written
      temp file. Assert-before-write ordering made it a harmless crash.
  (2) mutmut refuses to run natively on Windows (points to WSL); WSL present but
      no pip and sudo auth failed. Moved to CI on ubuntu-latest.
  (3) tests/test_cli_brand_match.py passes only from repo root — relative config
      path assumes a CWD. Surfaced under mutmut. H03's blocker.
FALSE GREEN CAUGHT: mutation run 33586594787 exited ✓ in 35s having generated
ZERO mutants ("No such option: --paths-to-mutate", mutmut 3.x moved paths to
config), swallowed by '|| true'. Caught by wall-clock implausibility, NOT by a
gate. D0's mechanism in CI form. Fix pushed 9721c73; rerun then failed HONESTLY.

### Carry-forward, session 7 (2026-09-02)
| Item | Status | Carried |
|---|---|---|
| Five B0 conversations | OPEN — 0 of 5, blocked on nothing, outranks all build work | 11 |
| KEY ROTATION CHECK | OPEN — .env still PASTE_NEW_KEY_HERE; precedes any live call | 4 |
| Ahmad collaborator add | OPEN — username still unknown | 3 |
| G12 study2 backup pair | OPEN — still tracked; only src/aivis untracked this session | 0 |
| H03 mutation score / B6 quote-ban | ABSTAIN — blocked on defect (3); workflow file exists, one-command retry | B6 re-listed |
| B3/B7 three bundle_digest impls | OPEN — untouched | carried |
| B4 _patch_v1 untracked+armed · B5 accepted_non_claims | OPEN — untouched | carried |
| error-row shared hash · chain HEAD external anchor | OPEN — untouched | carried |
| Project copy of 02 stale | OPEN — re-upload after this append | 2 |
| G01 ruff | DONE — 9 -> 0, 2e395b9 | closed |
| G02 mypy | DONE — 7 -> 0 incl. the real cli.py:223 arg-type, 2e395b9 | closed |
| G03 complexity | DONE — summarize_anchor E->B 18161a4, parse_tool_list D->C a210ca2 | closed |
| K07 lockfile | DONE — 326 pins, 72eced9 | closed |
| runner.py coverage | DONE — 32% -> 97%, 11 mocked tests, 8d69a7b | closed |
| G12 src/aivis untrack + ignore | DONE — f57e59e, files on disk and in history | closed |
| G10 duplicate code | PARTIAL — parser failure-returns unified; B7 digest trio untouched | 0 |
| NEW: mutation.yml workflow | DONE — 268ea0f, fixed 9721c73; measurement steps must never carry '|| true' | 0 |
| NEW: agent scratch left in place | _agent_variance_tail_v1.py, _agent_parser_tail_v1.py, _agent_lint_patch_v1.py — untracked, per §1 | 0 |

## AMENDED 2026-09-04 — session 9 (Luna run + canon versioning)
Session-8 line "Claude names small boutiques; both ChatGPT models name global
incumbents, no boutiques" is SUPERSEDED — it was measured under asymmetric
extraction (run4 canon contained no incumbent names). Under shared canon v2
(study2/config/canon_pr_agency_v2.json, 23 names), Claude buyer_intent is led
by Weber Shandwick and Edelman (14.6% each, n=41). Surviving divergence:
Luna names Bospar/5WPR/Otter/Method (0/41 on Claude, CI-separated); Claude
names Reputation Ink/Rhino (0/18 on Luna, NOT separated at these n).
Luna run: 89/90 clean, verified two-route (digest 0e0772d1…), two idle
discontinuities (3h18m, 26m) in wall clock, ~19min active.
Key rotation: SPLIT — .env carries a real key [MEASURED: grep 09-04];
currency vs the 08-29 exposure [UNVERIFIED — console check pending].
NEW OPEN: make_report attempt-count blind to .errors.jsonl sibling
(prints attempted=clean on split-file runs) — needs "go".
NEW FILES: canon_pr_agency_v1/v2.json · canonv2 reports ×2 ·
cross_engine_buyer_intent_v1.md · pr_agency_luna_run1_v1.jsonl (+.errors).
[MEASURED: session 9 console record]

### Carry-forward, session 9 close (2026-09-04)
| Item | Status | Carried |
|---|---|---|
| Luna bank run | DONE — 89/90 clean, two-route digest 0e0772d1, discontinuities noted | closed at 1 |
| Canon v1/v2 files + canonv2 reports x2 | DONE — pushed 20b53ae | 0 |
| Cross-engine buyer_intent artifact | DONE — pushed 20b53ae | 0 |
| Session-8 finding amended (asymmetric canon) | DONE — appended above, pushed | 0 |
| Sep 8 demo v1 | DONE — 7e5a634, banned-words 0, all numbers measured | 0 |
| WTP prediction seal | DONE — f8b4cbd, sealed 4 days pre-meeting; confidences adopted from assistant evidence read unedited — note at Brier scoring | closed at 3 |
| Key rotation | SPLIT — real key in .env [MEASURED]; currency vs 08-29 exposure [UNVERIFIED, console] | 6 |
| Five B0 conversations | OPEN — 0/5, drafts ready, outranks all build | 13 |
| B0 sends (5 LinkedIn pastes) | OPEN — variants A/B/C written + checked this session | 0 |
| Credible PR slide deck (inbox, 08-27 email) | OPEN — read before Sep 8 | 0 |
| Vendor-page re-fetch (gating if demo §04 shown) | OPEN | carried |
| Ahmad collaborator add | OPEN — username still unknown | 5 |
| make_report attempt-count blind to .errors.jsonl | OPEN — needs "go" | 0 |
| Luna evidence single-disk (study2/data gitignored) | OPEN — decide: force-add / copy / accept | 0 |
| wtp template runs/wtp_pred_sep8_v1.json | NOTE — untracked scaffolding, left in place; cat> onto it post-creation logged as lock brush, zero loss | 0 |
| D08 chain fix · G10 fork · B4/B5/B6/B7 · VOID move · C07 sleep | OPEN — unchanged | carried |

## AMENDED 2026-09-04 — session 9, part 2: B0 OUTBOUND SENT
First B0 outreach in project history. 5 messages sent via LinkedIn DM,
2026-09-04, to existing connections screened as strangers (no prior
exchanges):
| # | Recipient | Segment | Variant |
|---|---|---|---|
| 1 | Doug Simon (D S Simon Media) | competitor-adjacent / agency | 2 or 5 |
| 2 | Mitesh Shah (Acuity Digital) | agency operator | 5 |
| 3 | Parth Suba (AI Search architect) | competitor-adjacent | 2 |
| 4 | Serge Isac (Meanwhile, skincare) | category-naive brand-side | 3 |
| 5 | Sevilay E. (SDT Dental Studio) | category-naive practice owner | 4 |
OUTBOUND: 7/2 — population: all outbound about aivis, all channels, all
time (2 prior Gmail/Tyler + 5 LinkedIn today). Replies unchanged at 2
(both Tyler logistics; 0 B0 replies yet).
RULES ARMED: a reply outranks all build work, within the hour ·
buyer_pred_<n>_v1.json sealed BEFORE any call that gets scheduled ·
Max Muir excluded from B0 (warm lead, screen rule 4).

## AMENDED 2026-09-07 — session 9 close (appended at session 10 boot)
Perplexity adapter live: src/aivis/perplexity_adapter.py (sha256 9009572a...4744b)
+ run_bank_perplexity_v1.py. Citations/search_results/usage stored per row;
sha256-over-response_text unchanged; verify_evidence.py passes pplx rows.
Runs: cosmetic_tristate_pplx_run1 90/90 ($0.4937) · jeweler_pplx_run1 90/90
($0.4859) · smoke pr_agency 10/10. Pplx C02 ~= $0.0054/call [MEASURED: 190 rows].
Findings [MEASURED 2026-09-06, sonar, T=0.0, 3 runs/prompt]: Credible PR 0/90
responses AND 0/1,754 cited sources (378 domains). Jeweler: SVS 30/90, Jared
19/90, Solomons 11/90, HL Gross 11/90, Loucri 8/90, London 7/90, Tri-County
5/90 (site 32 reads — read-not-named), Matthew James 0/90.
FABRICATION INCIDENT #7 logged+pushed de83a4f ("Vanity Fair Jewelers split
listings" — real seed + invented detail). Rule: prior-session findings are
[QUOTED] until file opened this session; outreach never rides on [QUOTED].
B1 guard FIRED in production (refused jeweler re-run overwrite).

### Carry-forward, session 9 (2026-09-06/07)
| Item | Status | Carried |
|---|---|---|
| Five B0 conversations | OPEN — 0 of 5 | 13 |
| ANTHROPIC key rotation | OPEN — precedes any Anthropic live run | 6 |
| Ahmad collaborator add | OPEN — username unknown | 5 |
| jeweler verify_evidence + backup cloud/USB push | PENDING CONFIRM — single-disk until done | 0 |
| 10 staged sends (Carson, Lou, Matthew James, Tri-County, London, Solomons*, 3 texts, recruiter) | OPEN — *Solomons banned-word fix required pre-send | 0 |
| Bridal + kitchen&bath banks (committed by texts 7-8) | OPEN — build+seal+run this week | 0 |
| Sep 8 demo/one-pager update w/ tristate numbers + intervals | OPEN — due TODAY, mtg is TOMORROW Tue 3:30 EDT | 0 |
| WTP seal | UNTOUCHED — stays sealed until post-meeting | 0 |
| B3/B7 · B4 · B5 · H03 · chain external anchor · study2 gitignored data | OPEN — unchanged | carried |
| Project copies of 02/03 stale | OPEN — re-upload after this append | 0 |

## AMENDED 2026-09-07 — session 10 (Sep 8 prep + first send)
KEY ROTATION CLOSED [MEASURED: new key prefix NjV..., live 200
msg_011CeowRHp4tGdrZ4QGfMriv; old dt_tskt9 prefix gone from .env; old-key
revocation at console assumed, unprobed]. Anthropic surface reopened.
JEWELER VERIFY: PASS on data/audits/jeweler_pplx_run1_v1.jsonl [MEASURED].
TRISTATE RE-DERIVED IN-SESSION: Credible PR 0/90 responses [95% CI 0.0-4.1]
AND 0/1754 citations [0.0-0.2], 378 domains; naive grep "credible" found 4,
all read as adjective ("most credible names"), entity count 0 — the 4->0
read is the live kappa argument. New Skin Image 0/90 [0.0-4.1]; long island
27/90, carle place 3/90.
CLAUDE RE-DERIVED: 0/191 overall, 0/41 buyer_intent (PR-IN clean rows = 41,
reconciles session-5 figure) [MEASURED: pr_agency_run4.jsonl].
ARTIFACTS: aivis_demo_sep8_v2.html (v1 + Perplexity section, v1 untouched) ·
aivis_crediblepr_onepager_sep8_v1.html. Banned-word grep both: one-pager 0
hits; demo 4 hits all read in context = refusal statements (claim-ceiling +
not-claimed cards), CLEAN. PDF print of one-pager pending.
SENT: New Skin Image text to Olga (0/90 + 27/90, zero claims, "nothing for
sale"). OUTBOUND 3/2 [population all channels all time].
GAP FOUND: jeweler_openai_run1_v1.jsonl absent from ~/aivis_backup_20260906
(pplx trio present) — add before cloud/USB push. Backup push still PENDING.

## AMENDED 2026-09-08 — session 10/11 close (delivery night)
DELIVERED 0 -> 1: 4-engine report v2 + four evidence files + checker EMAILED to Max Muir.
OUTBOUND: sent +2 this arc (logistics reply 09-02 counted prior; report email 09-08 new).
Recompute both integers from population at next boot per §3.
EVIDENCE (all MEASURED 2026-09-08, one collection night, all verify PASS):
  multi_anthropic_run3 88/90 clean (claude-sonnet-5, temp rejected+declared) 5ac8d9d8...
  multi_openai_run3 90/90 (chat-latest alias; snapshot undisclosed by API) 82660a1f...
  multi_gemini_run3 88/90 (resolved gemini-3.8-flash; free tier declared) 81fc2f91...
  multi_perplexity_run3 84/90 (sonar; 6 errors clustered in comparison - D3 again) 442259f4...
FINDING: Credible PR 0/350 responses, 0/120 prompts, four engines, incl. all buyer-intent.
  Comparably-sized firms register (Otter PR 19/90, SourceCode 14/90 ChatGPT) - zero discriminates.
  Engine leaderboards diverge: Claude->Bospar, ChatGPT->Otter/5WPR, Gemini->Edelman-heavy.
ARTIFACTS: make_pdf2 (1-engine designed), make_pdf3 (4-engine v1), make_pdf4 (v2, post-critique:
  prompt-level sampling unit, verbatim prompts, cross-version refusal, matcher-bias note,
  cost anchor removed). run_bank_multi_v1.py (4 engines, honest terminal check).
  All pushed through 17235f9; evidence force-added ca3dcde (gitignore blanket caught by hand).
DEFECTS CAUGHT BY GATES THIS ARC (none reached recipient): discovery-mode silent subject skip ·
  placeholder-as-name (assistant) · deprecated model alias (gpt-5.3-chat-latest listed but 404) ·
  silent runner killed twice -> progress lines · bank schema guess · banned words in quoted
  excerpts · commit msg described absent files · TWO defective assistant probes ($3 bash-expansion
  gate always-false; \$3 regex never-match). NEW RULE: string gates in bash double quotes are
  untrustworthy near $; use heredocs.
5-EXPERT CRITIQUE: effective-n accepted+fixed (prompt is sampling unit); "page 6 truncated" and
  "no small firm registers" checked FALSE against the artifact; consumer-surface gap and
  annex/sales split logged as v3 items, not blockers.
OPEN, priority order: (1) Max reply - outranks everything, within the hour, per §3.
  (2) Ahmad collaborator add - 12+ sessions. (3) B0 five conversations - 0/5, 12+ sessions.
  (4) v3 report items: search-grounded surfaces (gpt-5-search-api seen in probe), annex split,
  per-client productization. (5) K06 formal pass on 4 new evidence files before any further
  external share (Claude-bank precedent scan was clean). (6) pr_agency_run4.jsonl still
  uncommitted under same gitignore blanket - force-add next repo touch. (7) One-pager print.
NOT COUNTED TOWARD B0: Max remains inbound/warm. 0/5 stands.

### Carry-forward, session 8 (2026-09-08)
| Item | Status | Carried |
|---|---|---|
| Report to Max/Tyler | SENT 2026-09-08 — four-engine claim needs evidence-file verification before it is defended in any follow-up | 0 |
| Surface-presence layer | DONE — study2/surface_presence.py, 15/15 tests, run4 measured per family, 03 amended, commit 6dfd3f8 pushed | 0 |
| "Four engines" verification | OPEN — fourth engine's run file not yet opened in-session | 0 |
| Subject-presence measurement (presence.json) | OPEN — afternoon of manual checks (HARO/Qwoted, PRSA, Clutch, Muck Rack); converts buyer_intent table into the Max follow-up page | 0 |
| Canon-v2 firms list → _v3 rerun | OPEN — 5-name seed means NAMES is a lower bound, OTHER inflated | 0 |
| Ahmad κ email | OPEN — his email known (ahmadaiengineer859@gmail.com), draft text written, unsent; unblocks the entire κ lane | 4 |
| Five B0 conversations | OPEN — 0 of 5, outranks all build work | 12 |
| B3/B7 digest impls (surface_presence computes canon hash only, not bundle_digest — not a 4th impl) · B4 · B5 · B6/H03 · chain HEAD anchor · backup push | OPEN — unchanged | carried |
| Project copies of 02 AND 03 stale | OPEN — repo is ahead (03 has a 2026-09-06 block absent from project) | 3 |

## AMENDED 2026-09-09 — session 9
- Engines wired: 4 (Claude, ChatGPT via chat-latest, Gemini, Perplexity), evidence
  files multi_{anthropic,openai,gemini,perplexity}_run3_20260908.jsonl, all four
  digests bound in the delivery PDF [MEASURED: D07 4/4].
- Max Muir deliverable is out/aivis_crediblepr_report_4engine_20260909_v3.pdf
  (emitter study2/make_pdf5.py, 9091f44). v1/v2 SUPERSEDED, on disk, never sent.
  D04/D05/D07 PASS on the v3 bytes.
- A08 spec amended (see 08 ledger 2026-09-09); harness encoding defect logged,
  patch awaiting "go".

### Carry-forward, session 9 (2026-09-09)
| Item | Status | Carried |
|---|---|---|
| D04 banned-word FAIL on v2 PDF | DONE — semantic false positive ("signed client"); reworded in new emitter make_pdf5.py; v3 re-graded PASS on shipping bytes | 0 |
| Harness cp1252 truncation (A08 false "0 hits") | DONE — encoding fix at aivis_battery_v2.py:80, pushed 321ea5b; A08 spec amended with enumerated classes, reference route = grep -a | 0 |
| Max Muir deliverable | STAGED — v3 PDF + 4 evidence files + verifier in ~/Downloads/maxmuir_package; SEND OPEN, outranks all build | 1 |
| Zenodo deposit | BUILT — study2/zenodo_v1 (8257afc), findings recomputed, K06 clean, 4x VERDICT PASS; chain receipt seq 3 (aivis-method a41c271); PUBLISH OPEN (draft/DOI pending) | 0 |
| Germovic (Edelman) email | DRAFTED — corrected unique-top-5 claim [MEASURED]; sends after DOI; not a B0 screen | 0 |
| Evidence files single-disk | DONE — in git history via study2/zenodo_v1 commit 8257afc | closed |
| chain verify VERDICT FAIL | OPEN — seq 0 CHANGED = amendment-by-append signature, not tamper; README doc para + SUPERSEDED checker state (needs "go") | 0 |
| chain HEAD external anchor | IN PROGRESS — ec87fa32... goes in Zenodo description; DOI = anchor | carried from s6 |
| Ahmad collaborator add | OPEN — username unknown | 4 |
| Five B0 conversations | OPEN — 0 of 5, blocked on nothing | 12 |
| Key rotation / .env PASTE_NEW_KEY_HERE | OPEN — no live calls tonight (all work from stored evidence); still precedes next live run | 5 |
| Fabrication near-miss #7-class | LOGGED — "only firm named on all four engines" typed-not-computed in outreach draft; caught against open P4 table pre-send; corrected to unique-top-5 [MEASURED] | — |
| B3/B7 digest impls · B4 _patch_v1 · B5 non_claims · B6 mutation/H03 CWD fix · G10 · D08-class | OPEN — untouched tonight | carried |
| Project copy of 02 stale | OPEN — re-upload after this append | 3 |

## AMENDED 2026-09-09 — session 10: git evidence copies were not byte-identical
Session-9 row "Evidence files single-disk: DONE — in git history via 8257afc" is
CORRECTED: with core.autocrlf=true and no .gitattributes, git stored LF-normalized
blobs of CRLF-on-disk evidence JSONLs (probe: DISK 232,416 B / 90 CRLF vs BLOB
232,326 B / 0 CRLF; diff exactly CRLF-vs-LF) [MEASURED: 2026-09-09]. Disk copies
remain canonical and are the graded artifacts. Blob-version verifier verdict:
recorded in 08 ledger this session. RULE (Part C class): a backup of evidence is
verified by blob-hash comparison against the graded bytes, never by the push
succeeding — a text-mode copy is a different file. .gitattributes now pins
*.jsonl -text. Zenodo uploads FROM DISK ONLY until the re-add lands.

### Carry-forward, session 10 (2026-09-09)
| Item | Status | Carried |
|---|---|---|
| Max Muir send (v3 package) | OPEN — staged, outranks all build; v3 REMAINS the send artifact unless actively swapped for v4 (swap = new digests + new covering note, a named step) | 2 |
| v4 report | BUILT+GRADED except eyeball — 0f1409d, sha256 6387d331...b2528; D04(amended)/D05 PASS; NOT DONE until pages 5/7/8 eyeballed | 0 |
| D04 spec | AMENDED — population excludes EXHIBIT blocks; reference route in 08 ledger | 0 |
| Runner citation-field capture | OPEN — needs "go" (runner change); unlocks sources page for all future runs | 0 |
| CRLF blob defect | DONE — .gitattributes 4e8867a, renormalize cf6a698, sweep 22/22 MISMATCH 0; blob verifier 4x PASS; lesson in 08 + 02 amendments | closed same session |
| Competitor anatomy | RE-FETCHED [REPORTED: 2026-09-09] — 4 new anatomy rows (personas, actions, agent-traffic, MCP delivery); bottom-six rows still empty category-wide; Gumshoe publishing sampling methodology -> E08 must include them before any "0 of 9" quote | 0 |
| Zenodo upload / DOI | OPEN — upload FROM DISK; chain HEAD in description; gates Germovic send | 1 |
| Ahmad username · Five B0 (0/5) · key rotation · B3/B7 · B4 _patch_v1 (untracked, armed, left in place) · B5 · B6/H03 · chain SUPERSEDED state (needs go) | OPEN — unchanged | carried |
| Project copy of 02 stale | OPEN — re-upload after this append | 4 |
