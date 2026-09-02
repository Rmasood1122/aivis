# 16 · USE-CASE BATTERY v1 — 24 use cases of what EXISTS
## 2026-09-02 · RUNG R0 (designed, not run) · META artifact, recipient: operator
## Closes L01 in 13 ([P] bar: file exists w/ ranking rationale). Supersedes 13's 27-UC seed
## list, which mixed built capability with roadmap. Roadmap is excluded here BY CONSTRUCTION
## and enumerated in §4 so its absence is not mistaken for oversight.

**What this is.** A matrix, not a list. Four recipients × six capability classes. The count
follows from the matrix; 24 was not chosen first. Every use case names the artifact it runs
on, its status against the repo at `d2f6ffa`, the highest rung it can earn, and what defeats
it.

**The scope constraint, stated once.** A use case appears here only if the capability is on
record as BUILT. "The product could do X once Y ships" is not a use case, it is a roadmap
line. This is the same discipline the claim ladder applies to external statements, turned
inward on the product's own inventory.

**Scoring vocabulary.** Three values, no composite (04 §1):

    LIVE      runnable today on artifacts that exist, evidence named
    PARTIAL   core exists; exactly one named gap, and the gap is stated
    BLOCKED   needs a gate or build that is named, with its blocker

Report per block as `LIVE a · PARTIAL b · BLOCKED c · POPULATION 6`.

**PRE-COMMITTED EXPECTATION, sealed at design.** Fewer than 8 of 24 will grade DELIVERABLE —
meaning a named human who is not the operator receives value from it this week. The majority
will grade DEMONSTRABLE: real, checkable, but with no recipient booked. If that expectation
is wrong in the optimistic direction, the market gate is less binding than 05 claims and the
plan is re-derived. If it is wrong pessimistically, the instrument is thinner than the
document corpus suggests. **Sealed before the table below was filled.**

**On value.** Willingness-to-pay for every row below is **unmeasured**. Delivered audits = 0,
paying customers = 0. The only dollar figures on record are `[REPORTED: web, 2026-08-31]`
bands in 09 from self-interested vendor pages, already flagged as decaying. So the VALUE
column states **what decision the use case changes**, not what someone would pay. Dollar
figures appear only in §3, tagged, with their source class. A value claim without a buyer
conversation behind it is R0 and is marked as such.

---

## THE MATRIX

**Recipients** — who can receive value, ranked by proximity to a real named human:

    R-A  Agency partner        Credible PR; Tyler Tran, Max Muir; Sep 8, six days out
    R-B  Direct buyer          pilot #001; nobody named yet
    R-C  Employer / interviewer  career lanes 1 and 2 in 09
    R-D  Public / adversary    method page readers; the category; future disputes

**Capability classes** — only what is built:

    C1  supply-side measurement carrying intervals
    C2  evidence trail + recipient-side verification
    C3  refusal machinery (abstention, guards, withdrawal)
    C4  pre-registration and sealed study design
    C5  transcript retention and criteria mining
    C6  provable precedence via hash chain

---

## BLOCK A — AGENCY PARTNER (R-A) · the only block with a booked recipient

| ID | Use case | Runs on | Status | Ceiling |
|---|---|---|---|---|
| U01 | **Category baseline: which PR firms AI names, with intervals.** Their absence printed with its denominator — 0 of 191, all five families, CI 0.0–8.6%, STATUS=COMPLETE — beside boutiques that do appear (Clarity 11.5%, Reputation Ink 7.3%) | `pr_agency_run4.jsonl` (191 clean) + `make_report.py` | **LIVE** | R2 |
| U02 | **They run the checker themselves.** Report ships with the evidence file; `verify_evidence.py` is stdlib, needs no aivis install, caught 3 attack classes in a clean container | `verify_evidence.py` [D06 PASS, third party] | **LIVE** | R3 on their MATCH |
| U03 | **Refusal shown on their own data.** The D1 guard refusing first-three below five candidates, and RANK_WITHDRAWN renormalised and labelled — a vendor demonstrating what it won't say | `make_report.py` guard, `variance.py` `_composite` | **PARTIAL** — rule structural, the abstention *page* is not built | R1 |
| U04 | **Pre-registered placement study, outcomes sealed including the null.** Join 1 (do placements move AI answers) and Join 2 (does the metric move consultations — their data) | `11_PILOT_CHARTER_v1` | **LIVE** as an offer | R0 |
| U05 | **What the model says when it says a firm.** Criteria at buyer intent (pricing 75.6%, media relationships 51.2%, n=41) and the `contributor_warning` gradient: 50.0% long_tail, 28.0% comparison, **0% at buyer_intent** | `criteria_miner.py`, declared CANON | **PARTIAL** — unvalidated parse until κ publishes; the page must say so | R1 |
| U06 | **A method page they can cite, dated provably.** Invariants published and hash-chained; anonymous clone verified LINKS 2/2 | `aivis-method`, `chain_receipt.py` | **LIVE** | R2 |

`LIVE 4 · PARTIAL 2 · BLOCKED 0 · POPULATION 6`

---

## BLOCK B — DIRECT BUYER (R-B) · no named recipient

| ID | Use case | Runs on | Status | Ceiling |
|---|---|---|---|---|
| U07 | **Single-market visibility baseline with intervals on the face.** Wilson live and verified on a real page: `100% [95% CI 64.6%-100.0%, n=7]` | CLI + bank; `variance.py` | **PARTIAL** — multi-prompt bank command (I-9) not built; key rotation precedes any live run | R1 |
| U08 | **Deliverable arrives with its own audit kit.** Evidence file + public checker + bundle digest printed and independently recomputed | `evidence.py`, `verify_evidence.py` [B01 PASS] | **LIVE** | R2 |
| U09 | **"We refuse to score this."** `INSUFFICIENT_EVIDENCE` as the only legal abstention token; unparseable runs excluded rather than folded in as zeros | `scorer.py`, `variance.py` `_rates` | **LIVE** structurally | R1 |
| U10 | **Before/after measurement against a pre-committed minimum detectable change** | charter + bootstrap pipeline | **PARTIAL** — MDC never computed (C10 unrun); publishing a before/after without it cannot distinguish null from underpowered | R0 |
| U11 | **Verbatim excerpts with row hashes** — the transcript-keeping advantage made visible; no competitor keeps the text | evidence rows [10 §2 Page 3: BUILT, data] | **LIVE** | R1 |
| U12 | **Re-verification years later.** Stored raw text + stored hash + a stdlib checker means the artifact stays checkable after the vendor is gone | `verify_evidence.py`, chain | **LIVE** | R2 |

`LIVE 4 · PARTIAL 2 · BLOCKED 0 · POPULATION 6`

---

## BLOCK C — EMPLOYER / INTERVIEWER (R-C) · lanes 1 and 2 in 09

| ID | Use case | Runs on | Status | Ceiling |
|---|---|---|---|---|
| U13 | **Separation stated honestly.** Bootstrap B=20,000: Purple 77.0 [72.8–80.8], and P(Casper>Tempur)=0.870 reported as **not separated** — the finding no composite-score vendor can print | 03 Part A, reproducible | **LIVE** | R1 |
| U14 | **Tamper demo.** Flip one byte of `response_text`; the checker goes MATCH → MISMATCH. Found by writing the checker to break the emitter (D6) | `verify_evidence.py` [A05, D06] | **LIVE** | R2 |
| U15 | **The hallucination answer, with receipts.** Six fabrication incidents with mechanisms, plus D0 (210 rows, zero calls) and tonight's CI false green (✓ in 35s, zero mutants, swallowed by `\|\| true`) | 03 Part C, 13 ledger | **LIVE** | R1 |
| U16 | **Pre-registration that actually bound.** Sealed `fec11fb2…` before the run; outcome C fired, with a correction published against the operator's own expectation | `14_PREREG_pr_agency_v1` | **LIVE** | R1 |
| U17 | **Labelling-ops kit.** Sealed sample reproducible byte-identical from a published seed; preflight hash verification 100/100 | `kappa_sample.py`, `verify_kappa_sample.py` [B06, B07 PASS] | **LIVE** — but the κ **value** is unmeasured, and that is the gap the interviewer will find | R2 |
| U18 | **Engineering surface that survives review.** 115/3 suite, 90% line coverage, ruff 0, mypy 0, CI green, 326-pin lockfile, mutation workflow that fails honestly | repo at `d2f6ffa` | **LIVE** | R2 |

`LIVE 6 · PARTIAL 0 · BLOCKED 0 · POPULATION 6`

---

## BLOCK D — PUBLIC / ADVERSARY (R-D)

| ID | Use case | Runs on | Status | Ceiling |
|---|---|---|---|---|
| U19 | **Supply-side measurement published with denominators on every count** — the side of the market where an adversary-proof artifact is possible | `make_report.py`, corpora | **PARTIAL** — B03 (orphan-count grep) unrun | R1 |
| U20 | **The recipient-side verifier as a public artifact.** B5 on the bar; 0 of 9 vendors hold it | `evidence-verify` v0.3.0, Apache | **LIVE** | R2 |
| U21 | **Published abstention rate.** B3 on the bar; 0 of 9 vendors; structurally unavailable to a dashboard business | rule specified | **BLOCKED** — rate never computed (B04 unrun) from a named population. **Cheapest unoccupied square on the board** | R1 when run |
| U22 | **Publishing a null cleanly.** Pre-registration is what makes a null credible rather than a retreat; the causal null is the stated moat | `14_PREREG` pattern | **LIVE** as capability | R1 |
| U23 | **An answer to the category-wide attack** (Brainlabs 2026-04-20; five of six vendors silent) built from artifacts that predate the dispute | 04 §F5, method page | **PARTIAL** — the full answer needs a published κ | R1 |
| U24 | **Provable, not assertable, precedence.** A hash-chained receipt anyone verifies offline, so the publication date is not a claim | `chain_receipt.py` [F02 PASS] | **PARTIAL** — chain HEAD lives only in operator-controlled repos; no external anchor (carried OPEN) | R2 |

`LIVE 2 · PARTIAL 3 · BLOCKED 1 · POPULATION 6`

---

## §2 — TOTALS AND THE SEALED EXPECTATION, EVALUATED

    LIVE 16 · PARTIAL 7 · BLOCKED 1 · POPULATION 24

**But LIVE is not DELIVERABLE.** LIVE means the capability runs. DELIVERABLE means a named
human who is not the operator receives it this week. Applying that filter:

**DELIVERABLE now: 6 of 24** — U01, U02, U04, U05, U06 (all R-A, Sep 8, a booked meeting with
named humans), and U18 (any employer, an existing public repo).

**The sealed expectation said fewer than 8. Result: 6. The expectation held.**

The distribution is the finding, and it is not flattering: **every deliverable use case except
one belongs to a single meeting six days away.** Block C grades LIVE 6 of 6 and DELIVERABLE 1
of 6 — the artifacts are real and no employer has been shown them. Block B has zero
deliverables because it has zero named humans. That is E5's empty seat measured from a
different direction than 05 measured it, and it agrees.

---

## §3 — VALUE, WITH ITS PROVENANCE

Every figure `[REPORTED: web, 2026-08-31, vendor pages — self-interested]` from 09, decaying,
**re-search before quoting to anyone**:

| Use-case cluster | Reported market band | What is actually known |
|---|---|---|
| U01+U05 audit-shaped delivery | one-time audits $1,500–$7,500 agency tier; $8,000–$25,000 engagement grade | that buyers pay *someone*; not that they would pay aivis |
| U04+U10 pilot engagement | charter proposes $2,500/qtr founding, $5,000/qtr list | a **proposal**, not a price. WTP predictions sealed `7e97fcfd`, unopened |
| U13–U18 career lanes | evals roles $44k–$190k; SE $130–170K base mid | postings, not offers; zero applications on record |

**The honest line:** the strongest value argument in this file is not a price. It is that
**U02 is a bar zero of nine funded vendors clear**, and U21 is a second one costing a sentence
to occupy. Whether buyers price that is exactly what B0 tests, and B0 is 0 of 5 at 11 sessions
carried.

---

## §4 — EXCLUDED BY CONSTRUCTION (not built; would be fabrication to list above)

Multi-engine comparison (1 of 5 wired) · any accuracy or κ-labelled statement (κ never
measured) · the abstention page · report layout pages 1–5 as a single emit · public index
(gated κ ≥ 0.75 + external citation) · transcript diagnosis layer (board #12, not designed) ·
attribution kit · second-opinion audit service (illegal until κ, abstention and verifier all
ship — running it first makes you the thing you are charging others with) · mutation score
(B6 quote-ban armed, H03 abstained).

---

## §5 — DEFEATED-BY

- **Reading LIVE as DELIVERABLE.** Sixteen capabilities run; six reach a human this week. The
  gap between those numbers is the entire market problem and this file exists to keep it visible.
- **Quoting §3's bands to a buyer.** They are self-interested vendor pages, one week old, and
  none was verified against a live posting.
- **Letting U05 travel without "unvalidated parse."** Criteria rates are a parser output and
  the parser has never been graded. Strip the caveat and this becomes the category's own sin.
- **Counting the Sep 8 meeting as a B0 conversation.** They came inbound and self-selected for
  interest. Screen rule 4; conflating them poisons the gate.
- **Building anything new off this file.** It is an inventory of what exists. Every gap it
  names is already on a board with a gate, and 10 §6's build order still governs.

---
USECASE BATTERY v1 · RUNG R0 · 0 of 24 exercised · POPULATION 24 · repo state `d2f6ffa`
