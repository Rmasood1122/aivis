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
