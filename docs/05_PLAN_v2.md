# AIVIS — THE TOP 0.1% PLAN, v2
## 2026-08-27 · New file, new path. v1 is NOT edited and NOT deleted — mark it SUPERSEDED
## in place when you next touch it, per G1-16. v1 remains the only record of what changed.
## Rebuilt after two independent critiques. Both are cited by number where they moved something.

---

## WHAT CHANGED FROM v1, AND WHY

Seven changes. Each names the objection that forced it, so the next reader can audit whether
the fix was warranted rather than reconstruct it.

| # | Change | Forced by |
|---|---|---|
| 1 | **Two lanes with a spend gate**, replacing an 18-step sequence | Both critiques: "the epistemic sophistication has not been allowed to restructure the operational sequence" |
| 2 | **B0 — a market gate that precedes the instrument bar** | "The bar tests whether aivis occupies its designed position, not whether the position matters" |
| 3 | **The κ protocol fully specified** — population, unit, provisional definition, labeller | "A κ of 0.75 is meaningless without these" |
| 4 | **Publish the labelled set itself**, plus an external co-labeller and a published alpha | "You made the test, you graded the test" — the sharpest objection in either document, unanswerable by v1 |
| 5 | **Method page split into invariants (now) and taxonomy (after contact)**, with the invariants hash-chained through titan-gate | Protocol age is continuous, not binary — plus a tension neither critique saw (early publication of unstable content resets the clock) |
| 6 | **Badge/referee model CUT from this plan** | "The referee model requires authority that doesn't exist at launch" — the strongest strategic observation in either critique |
| 7 | **Every technique-lift figure re-tagged `[SELF-REPORTED, UNAUDITED]`** | The corpus scored itself favourably twice; the ledger is the same class of measurement |

**One correction I am NOT making.** Both critiques imply the fix to sequencing is to run the
buyer conversations *before* the build. That serialises two activities that consume different
resources — conversations consume calendar time (finding, scheduling, waiting), building
consumes work hours. A dependency gate would idle whichever resource isn't binding. §1 uses a
**spend cap** instead, which is honest about what is actually scarce: your attention.

**Limitations first.** Every MARKET row here is still R0 — believed, not observed. That does
not change until Lane M produces transcripts. The plan is now structured so R0 failure is
detected in week one rather than after fourteen steps.

---

## §0 — PRE-REGISTRATION v2 (sealed before the plan below)

    B0  MARKET GATE — evaluated FIRST, and everything else is contingent on it.
        In 5 screened conversations, >= 2 of 5 raise evidence, reproducibility, method
        or trust UNPROMPTED, before aivis is described.
        FAILS  -> the position does not matter to buyers. B1-B5 become irrelevant
                  regardless of whether they are occupied. Re-derive from the transcripts.
        PASSES -> proceed, and the instrument bar below becomes worth clearing.

    B1  a published extractor-accuracy figure (Cohen's kappa)          0 of 9 vendors hold this
    B2  an interval on every customer-facing number                    1 of 9  (Evertune)
    B3  a published abstention rate                                    0 of 9
    B4  full declared surface (model version + temperature)            0 of 9
    B5  recipient-executable verification of the delivered artifact    0 of 9
    B6  one stranger who ran it and paid (rung R4)                     the only bar that
                                                                       requires permission

    POPULATION   9 named vendors; 6 profiled [CITED: 2026-08-18], 3 named-only [UNVERIFIED]
                 and excluded from every rate above.
    MEASURED_BY  B0: five sealed prediction files, one per conversation, written before each.
                 B1-B5: the 7-dimension vendor gate re-run, aivis scored by the same rule.
                 B6: pilots/pilot_001_delivered_v1.json + cleared payment.
    DECAY        Every "0 of 9" and "1 of 9" above rests on a scan dated 2026-08-18.
                 **GATING, not advisory: re-fetch all nine vendor pages before any external
                 use of these counts.** If any vendor has since published a kappa, an
                 abstention rate, or a surface declaration, the bar changes and this plan
                 is re-derived, not patched.

**Why B0 is new and why it goes first.** v1's bar could not fail in a way that invalidated the
strategy — only in a way that invalidated the execution. That is a circular bar. B0 is the
non-circular one: it can come back NO, and if it does, the whole architecture is answering a
question nobody asked.

---

## §1 — THE STRUCTURAL FIX: TWO LANES, ONE SPEND GATE

```xml
<operating-structure>
  <lane id="M" name="MARKET" resource="calendar time" cost="$0">
    Runs continuously from day one. Never blocked by anything in Lane I.
    Produces: transcripts, sealed predictions, one delivered pilot, one payment.
  </lane>

  <lane id="I" name="INSTRUMENT" resource="work hours" cost="~$1 in API + build time">
    Runs in parallel, governed by the spend gate below.
    Produces: an artifact a stranger can hold and check.
  </lane>

  <spend-gate>
    <rule>No more than 12 build-hours in Lane I until Lane M has produced 2 completed
          conversations. No more than 30 until it has produced 5.</rule>
    <why>A dependency gate would idle the build while waiting on replies, which wastes the
         non-binding resource. A spend cap constrains the resource that is actually scarce
         and cannot be replenished: operator attention.</why>
    <enforcement>Hours logged per lane in the session-state doc. An unlogged hour counts
          as a Lane I hour — the conservative default, because Lane I is the one that
          feels productive and therefore the one that overruns.</enforcement>
    <defeated-by>Logging generously. If the log is written from memory at session end it
          is fiction. Log at lane switch or not at all.</defeated-by>
  </spend-gate>

  <the-observation-both-critiques-missed>
    A qualified buyer contacted this project unprompted and is currently unanswered.
    E5's seat is not empty because buyers are hard to reach. It is empty because one
    arrived and documents were written instead. M0 exists for exactly this.
  </the-observation-both-critiques-missed>
</operating-structure>
```

---

## §2 — THE PANEL, v2 (unchanged in composition; one change in status)

E1 statistician · E2 forensic auditor · E3 distributor · E4 adversary · E5 buyer.
Five vetoes, each with a scope and a named blind spot; a step ships when all five clear.
Full definitions stand from v1 §1 and are not restated.

**The one change:** v1 admitted E5 was a fiction and proceeded anyway. v2 gives the fiction an
**expiry**: E5's seat is filled by M1–M3 or Lane I stops at the spend cap. A panel that can
reach consensus without its buyer is a machine for building things nobody wants, and the only
fix is a deadline on the emptiness.

**Blind-spot cross-check, restated because it is now load-bearing:** E3 (ship it) is checked by
E2 (defend it later); E4 (refuse everything) is checked by E5 (does it change a decision).
With E5 empty, E4 is unchecked — which is precisely how a plan grows from 18 steps to more.

---

## §3 — THE PLAN

### LANE M — MARKET (runs from today, $0, no gate green required)

    M0  ANSWER THE INBOUND PARTNER                                          ← TODAY
    DOES        converts a live inbound into the first real datapoint in the project's history
    DONE-WHEN   a reply is sent, and their response is recorded verbatim
    RECIPIENT   the named person at that company
    COST        ~20 minutes. No credits, no code, no gate.
    CONTENT     zero product claims. The banned list governs: no "verifiable",
                "tamper-proof", "signed", "accurate", "audit-grade", "customers", "we".
                Sayable: per-run raw responses and request payloads are stored with hashes
                [MEASURED: internal, dev artifact].
    VETOES      E5, E2
    DEFEATED-BY counting them as one of the five screened conversations. They are inbound,
                which means they self-selected for interest — the opposite of the screen's
                requirement. Record them SEPARATELY, as a warm lead, not as evidence
                about demand. Conflating the two poisons B0.

    M1-M3  THREE SCREENED CONVERSATIONS
    DOES        starts filling E5's seat
    DONE-WHEN   three qualifying conversations completed, each with runs/buyer_pred_<n>_v1.json
                sealed BEFORE the call
    RECIPIENT   three named humans
    COST        $0
    SPREAD      >=1 who already bought a competitor; >=1 who has never heard of the category
    DEFEATED-BY a friend doing you a favour. The most expensive datapoint available.

    M4-M5  TWO MORE, AND EVALUATE B0
    DONE-WHEN   five complete; B0 evaluated against the sealed predictions
    KILL RULE   P1 = 0/5 AND P4 <= 1/5  ->  positioning falsified. Stop Lane I.
                Pre-committed. It costs nothing to honour and everything to ignore.

    M6  DELIVER PILOT #001 (gated on I-9 and I-10, and on 13a being live and dated)
    DONE-WHEN   pilots/pilot_001_delivered_v1.json exists AND payment clears -> rung R4 -> B6
    RECIPIENT   the pilot buyer
    DEFEATED-BY delivering before the method page is public. The report becomes an ordinary
                vendor PDF and the entire position is forfeited on its first outing.

---

### LANE I — INSTRUMENT (governed by the spend gate)

**Tier 0 — unblock (nothing works without these)**

    I-1  Restore API credits.        Blocked since 2026-08-20. Precondition, not a claim.
    I-2  Fix cli.py:194-195 — the unconditional unlink() of the default evidence file.
         Needs a named "go". A test must assert the refusal, or the defect returns
         on the next refactor exactly as the regeneration bomb did.
    I-3  RR-1b live run: first artifact with DISTINCT > 1. ~$0.08 [EST: 10 x $0.007602].
         DEFEATED-BY the stub — run_once_stub ignores its prompt and returns a constant,
         so stub mode gives DISTINCT=1 forever. A green from the stub is a false green.

**Tier 1 — make the numbers real**

    I-4  Propagate the Wilson intervals. Dimension.low/high stops being None while the
         docstring claims otherwise. Near-zero cost — the values are computed and discarded.
         DEFEATED-BY putting the interval on the dimension but not on the page the buyer reads.

    I-5  Build the golden set — see §4, which now governs this step entirely.

    I-6  Measure and publish kappa — see §4.

    I-7  Order-flip the rank metric. Print the DELTA, not just the two rankings; the delta
         is the measurement. If it is large, RANK_WITHDRAWN stays, and that is a finding.

    I-8  parse_gate_v0_1.py — refuse export above the parse-error threshold. The threshold
         must come from I-3's observed distribution, not from the [UNVERIFIED] 10% guess
         (one datapoint of 2-of-5 rows cannot set a threshold).

    I-8b SAMPLING: raise N to 7 immediately — you are currently below your own cited floor,
         which is the one indefensible position. Then derive the real N from a minimum
         detectable change and publish both the N and the MDC.
         **v1 left this vague; the critiques were right to flag it.** Target: N such that
         a 10-point shift in mention rate is detectable at the bank's per-prompt n.
         Compute it, do not assert it. ABSTAIN and publish N=7 with its actual MDC if the
         computation is not done in time.

**Tier 2 — the artifact**

    I-9   Multi-prompt bank command. cli.py ONLY (anti-scope: if reporter/variance/
          evidence/runner must change, the scope was wrong and this reopens).
          ~$0.68 for 30 prompts x 3 runs [EST: 90 x $0.007602 — the 810/$6.16 figure on
          record is WRONG; BANK_SIZE=30].
          DEFEATED-BY any convenience sort. Run order is the property being proven.

    I-10  Recipient-side verifier. verify_hashes() already exists and has never left the
          building. One file, stdlib only.
          DEFEATED-BY requiring the aivis package. If verification needs the vendor's
          software it is not independent, and B5 is not met.

    I-11  bank_version on every row and every PDF, PLUS refusal of cross-version comparison.
          The field without the guard just documents the fabrication.

    I-12  Sign RR-1 through RR-5 on the pilot artifact. Five GREEN or no ship. An AMBER is
          a RED with better manners.
          DEFEATED-BY signing after sending. A gate evaluated after delivery is a postmortem.

---

### LANE P — THE PUBLIC RECORD (split; see §5)

    13a  THE INVARIANTS — publish this week, before anything else in Lane P
    CONTENT     declared surface (model IDs, temperature 0.0, runs-per-prompt) · the
                abstention rule · the claim-ceiling policy and the banned-word list · what
                the product refuses to claim and what would unlock each term
    WHY NOW     none of this changes with buyer contact. It is value-derived, not
                market-derived, so publishing it early costs nothing and starts the clock.
    RECIPIENT   the public; every future prospect; every future adversary
    COST        writing time only

    13b  THE TAXONOMY — publish AFTER M1-M5
    CONTENT     categories, construction rules, counts per category, versioning and
                rotation policy, extraction rules
    WHY LATER   this is the part buyers reshape. Publishing it now and revising it after
                the conversations means the version that predates any dispute is the
                REVISED one, with age zero. **Neither critique saw this; both advised
                publishing the whole page immediately, which would have reset the clock
                they were trying to start.**
    NOTE        taxonomy public, full instantiated bank to the audited party only.
                Ratified decision D2 — no gaming detector exists, so a fully public bank
                is optimisable against and undetectably so.

    14   PUBLISH THE ABSTENTION RATE. Near-zero cost, zero competitors hold it (B3).

---

## §4 — THE κ PROTOCOL, FULLY PRE-REGISTERED

v1 said "100 cases, κ≥0.75 to ship" and stopped. Both critiques were right that this is not a
pre-registration. Sealed now, before any labelling begins:

```xml
<kappa-protocol seal-date="2026-08-27">
  <population>
    100 responses sampled from LIVE bank runs, stratified across all five prompt families
    (20 per family). Not curated. Not selected for clarity. The sampling script and its
    seed are published with the result.
    <defeated-by>Sampling after seeing which responses the extractor handles well.
                 Draw the sample BEFORE running the extractor on any of it.</defeated-by>
  </population>

  <unit>
    Mention-level: one judgement per (response x candidate domain) pair, which is the
    decision the extractor actually makes. NOT response-level, NOT anchor-level — those
    give different numbers and the difference is not a rounding error.
    Candidate domains come from extract_domain_candidates, so refusals are labelled too.
  </unit>

  <labelling>
    Rules written and dated BEFORE the first label. No model assistance of any kind —
    a golden set labelled by the thing it audits measures agreement with itself, and this
    is the single most likely way this plan fails silently.
  </labelling>

  <independence>
    <problem>"You made the test, you graded the test, and you're telling us you got a
             good grade." v1 had no answer. This is the answer.</problem>
    <answer-1>PUBLISH THE LABELLED SET ITSELF — all 100 raw responses, all labels,
              all disagreements. Self-labelling only defeats you if the labels are hidden.
              Published, "trust my grade" becomes "here is my exam, mark it yourself."
              This is the evidence-trail move applied to the golden set, and no vendor
              in the category does it.</answer-1>
    <answer-2>ONE NAMED EXTERNAL LABELLER independently labels 25 of the 100.
              Publish Krippendorff's alpha between the two labellers ALONGSIDE kappa.
              Two numbers, one of which the operator did not produce alone.</answer-2>
    <cost>answer-1: zero. answer-2: one afternoon of someone else's time.</cost>
  </independence>

  <thresholds>
    kappa &lt; 0.60          nothing ships. The parser is the product until it clears.
    0.60 &lt;= kappa &lt; 0.75  PROVISIONAL, meaning exactly: reports may ship carrying the
                          kappa and the label "Directional, not Decision-grade."
                          The public index may NOT launch. No badge, no cohort, no index.
    kappa &gt;= 0.75         shippable; the index becomes available.
    <sealed>These three lines are sealed as of this document's date and may not be
            revised after seeing a result. Revising a bar after the measurement is
            exemplar X4's negative case.</sealed>
  </thresholds>

  <publication>
    Published whatever the value, with the confusion matrix, the sampling seed, the
    labelled set, and the alpha. A low kappa published cleanly is worth more than a high
    kappa nobody can check — and it is the only version of this the category cannot copy
    quickly, because copying it requires admitting a number.
  </publication>
</kappa-protocol>
```

---

## §5 — PROVABLE PRECEDENCE (the fix neither critique could see)

Both critiques correctly identified that protocol age is continuous, and that two weeks of
precedence is nearly worthless against precedent cases whose protocols were years old.

Both then treated this as an unfixable constraint. It is not, because **you own titan-gate.**

    ASSERTED precedence:  "we published this on 2026-09-01"  — the challenger may disbelieve it
    PROVABLE precedence:  a hash-chained, signed receipt for the method page, emitted at
                          publication, verifiable by anyone offline, showing the document's
                          digest and its position in a chain that cannot be back-dated

**Two weeks of provable precedence beats two years of assertable precedence**, because the
precedent cases' advantage was never the calendar — it was that nobody doubted the date.
titan-gate manufactures exactly that property, and this is the first substantive reason the
two products belong to each other rather than merely coexisting in one operator's week.

    ACTION   emit a titan-gate receipt for 13a at publication. Publish the receipt beside
             the page and the verification recipe with it.
    HONEST   titan-gate's W8 (ed25519 default) is not landed. Until it is, this is a
             hash chain, not a signature, and the language stays "tamper-evident" —
             never "signed", never "non-repudiation". The upgrade path is real and named.

---

## §6 — WHAT WAS CUT, AND WHY

**The badge / referee model is removed from this plan.** It was Step 18 in v1.

The critique that killed it: LMArena, Consumer Reports and Nielsen all held authority
**before** the dispute. Their artifacts worked because the institution was already trusted.
aivis would be attempting to build authority **through** the dispute, which is a materially
different and much harder problem. A badge nobody wants is not a marketing engine; it is a
graphic.

**The free public index survives, but reframed.** Its function in v2 is not distribution — it
is **manufacturing the precedent artifact**. Four quarterly editions, each hash-chained to the
last, is what creates the protocol age that §5 makes provable. Distribution, if it comes, is a
side effect. Gated behind κ ≥ 0.75, because an index built on an unmeasured extractor is
precisely the category's existing sin at larger scale.

Revisit the badge model when, and only when, the index has been cited by someone who is not
you. That is the falsifiable precondition v1 lacked.

---

## §7 — ADVERSARY PASS: THE ONE NEW ANSWER

v1's §7 stands for Profound, Evertune, Athena, Scrunch, Peec and Otterly. One objection was
missing, and it was the strongest available:

> **"Why should I trust your κ when you computed it yourself, on a test you wrote,
> graded by you, against labels only you have seen?"**

**v1's answer:** none. Conceded silently by omission.

**v2's answer, from artifacts that will exist:** the 100 labelled cases are published in full
with their raw responses, so the test is markable by the challenger. An external labeller
covered 25 of them and the inter-labeller alpha is published beside the κ. The sampling seed
is published, so the draw is reproducible. **This does not eliminate the objection — it
converts it from "trust me" into "check me", which is the only move available to a measurement
product without an accreditor.** If a challenger re-labels the set and gets a different κ,
that is a finding aivis publishes, not a dispute it litigates.

---

## §8 — VERIFICATION CHAIN (gating, not advisory — v1's error)

v1 listed these as checks to run "before acting" and then acted. In v2 no Lane I hour is
spent until 1–4 pass, and no external claim is made until 7 passes.

1. `BANK_SIZE` — the corpus contains both 30 and 810. The 810/$6.16 figure is wrong.
   Every cost estimate above is provisional until this is computed.
2. Credits restored? One live call. All of Lane I Tier 0+ is inert otherwise.
3. `cli.py:194-195` unlink — still present? It has been off every board since 2026-08-20.
4. `verify_hashes()` — still exists, still recomputes from stored raw text? Last confirmed
   2026-08-19; a probe older than one session is re-run.
5. GitHub PAT — noted as expiring ~2026-08-30. It is 2026-08-27.
6. Is the proof tool still in a different repo from the product it proves? If yes, drift
   between checker and emitter remains undetectable — the best available explanation for
   the historical unreproducible `True`.
7. **Re-fetch all nine vendor pages.** Every "0 of 9" in §0 is from 2026-08-18. If any
   vendor has published a κ, an abstention rate, or a surface declaration since, the bar
   changes and this plan is re-derived rather than patched. **Neither critique questioned
   a single one of these numbers — structural critique is cheap, factual re-verification
   is not, and their silence is not endorsement.**

---

## §9 — FALSIFIERS

- **B0 fails** (fewer than 2 of 5 raise evidence/trust unprompted) → the position does not
  matter to buyers. Stop Lane I. Re-derive from the transcripts, do not average them with
  the prior hypothesis.
- **κ below 0.60** → the extractor is the product. Publish the number, stop everything else.
- **Two lanes collapse into one** (five sessions pass with zero Lane M hours logged) → the
  spend gate is decoration and must become a boot check that refuses to open Lane I.
- **A funded vendor publishes a κ and an evidence trail first** → the position is occupied
  and the only remaining edge is provable protocol age. This is why 13a ships this week.
- **The index is never cited by a stranger** → the distribution thesis is dead; aivis is a
  service business delivering audits one at a time, which is a smaller but real outcome.
- **Consolidation closes the window** → Adobe/Semrush $1.9B, Profound at $1B as acquirer,
  Lorelight shut down concluding AI visibility is a feature not a company. Outside the
  plan's control; named so its absence is not mistaken for safety.

---

## §10 — TECHNIQUE LEDGER, RE-TAGGED

**All lift figures below are `[SELF-REPORTED, UNAUDITED]`.** They come from corpus
measurements produced by the same system they evaluate, and this corpus has scored itself
favourably twice on record. They are direction, not magnitude. v1 quoted them as measurements;
that was the same error the plan charges vendors with.

| Technique | Lift `[SELF-REPORTED]` | Used in |
|---|---|---|
| XML tag trees | 5.17× | §1, §4 |
| Structured output w/ legal ABSTAIN | 3.73× | I-8b's ABSTAIN branch |
| Pre-registration / rubric | 3.09× | §0, §4 — both sealed before reasoning |
| Contrastive few-shot pairs | 6 uses in 14,984 | v1 §3, unchanged and still governing |
| Red-team / shortest defeater | 0.74× | DEFEATED-BY throughout |
| Self-consistency, ABSTAIN on disagreement | 0 prior uses | v1 §2, thesis unchanged |
| Order-bias reversal | 0 prior uses | v1 §4; one placement was order-sensitive |
| Adversary pass, artifact-or-concede | — | §7 |
| Definitions before weights | — | §0 |

**On the 0.74× red-team figure.** Critique 2 called "it scores below baseline so I'll use more
of it" a rationalization, and the phrasing deserved that. But "use less" is equally wrong. A
lift averaged across all conversation types says nothing about the conditional lift on the
artifact class where an unnamed failure is expensive. Red-teaming a haiku returns nothing;
red-teaming a release gate may return a great deal. Averaged, 0.74×. **The correct move is
neither more nor less — it is to measure it conditionally**, on plans and gates only. That is
a real work item and it is not in this plan, deliberately, because it is Lane I work with no
recipient. Logged here so it is not lost by silence.

---

## THE ONE-LINE PLAN, v2

**Answer the buyer today. Publish the invariants this week and chain them so the date is
provable. Publish the accuracy number and the exam it was graded on. Make the artifact
checkable without your software. Build only as fast as the conversations justify.**

Eight of nine competitors measure the side of this market that cannot be audited. That
remains the position — v1 had it right. What v1 had wrong was the order, and the order was
the whole thing.

---

*Nothing deleted, nothing overwritten. Steps touching existing files (I-2, I-4, I-7, I-8,
I-9, I-11) require a named "go" before execution. v1 stands as the record of what changed.*
