# 04 · VENDOR SCAN — the nine, and where the position is

## ⚠ DECAY WARNING — read before quoting anything below

Every vendor fact here was gathered **2026-08-18** by research agents fetching vendor pages,
**not re-verified page-by-page by this author**. Source classes: [V] vendor-claimed,
[I] independent, [C] competitor-authored.

**Every "0 of 9" and "1 of 9" count in this file is GATING, not advisory: re-fetch all nine
vendor pages before any external use.** If any vendor has since published a κ, an abstention
rate, or a surface declaration, the position changes and the plan is re-derived, not patched.

Three consecutive external reviewers of this material questioned **zero** of these numbers.
Structural critique is cheap; factual re-verification is not. Their silence is not
endorsement.

---

## 1. THE SEVEN DIMENSIONS, DEFINED BEFORE ANY VENDOR WAS SCORED

| dim | operational definition |
|---|---|
| SAMPLING | Does the vendor publish runs-per-prompt **as a number**? (Cadence alone — "daily" — is NO.) |
| UNCERTAINTY | Does any **customer-facing** metric carry an interval or margin of error? |
| METHODOLOGY | Does a page exist a second implementer could reproduce the metric from? |
| SURFACE | Are model versions and/or inference parameters (temperature) disclosed? |
| CITATIONS | Is there a published policy for validating cited URLs / hallucinated links? |
| RANK VALIDITY | If rank metrics ship, is any validity argument published? |
| EVIDENCE TRAIL | Can a customer obtain **per-run raw responses**? |

No weighting is applied. Per the ESG decomposition (measurement 56%, scope 38%, weights 6%),
a weighted composite would be the least informative thing buildable from this data.

---

## 2. THE NINE

**Deeply profiled (6):**

| Vendor | Scale | Position |
|---|---|---|
| **Profound** | $155M+ raised, ~$1B val, 700+ enterprises, ~10% of the Fortune 500, <120 staff [I: Fortune 2026-02-24]. $99–$399/mo + enterprise | Distribution leader. Does **not** publish run counts, model versions, temperature, or CIs. Variance discussion lives in a blog, not on dashboards. The Index extrapolates "400M+ conversations" from opt-in panels to population claims. |
| **Evertune** | $15M A, "700+ advertisers" [V]. $800/mo + ent | **The methodology leader and the real threat.** Publishes 100×/prompt/model across 11+ models, ±1pt overall / ±2pt topic, full ±44→±10 ladder. **No evidence trail** — "reporting API is on our roadmap." One quarter of work from occupying the whole position. |
| **Peec AI** | $21M A, ~$100M+ val, 3000+ claimed | ~1 chat/prompt/model/day implied by pricing. "100% authentic data" at n≈1 — a sampling-disclosure failure in one sentence. |
| **Otterly.AI** | bootstrapped, ~7 staff [I-est]. $29–$489 | "#1 rated" from review counts, shipped as a measurement claim. |
| **Scrunch AI** | $19M, 500+ brands, acquired by Sitecore | Best-in-trio methodology FAQ. Publishes that "single runs can be misleading" **while shipping no N**. Their blog is aivis's best sales collateral. |
| **Athena HQ** | $2.2M, YC W25, 80+ cos | "95%+ Accuracy Rate" with **no artifact**. QVEM "50+ sources" unnamed. |

**Named only, [UNVERIFIED], excluded from every rate:** Rankscale · Zeo Radar · Gumshoe.

---

## 3. THE FINDINGS THAT MATTER

**F1 · The four-way conjunction is unoccupied.** Published uncertainty **and** per-run raw
evidence **and** abstention **and** declared surface. Nobody holds all four. aivis holds
three internally, with DELIVERED = 0 as the entire remaining distance.

**F2 · G7 — abstention — is the most protected square on the board.** Six funded vendors,
**zero** published abstention rates, zero sufficiency-refusal mechanisms found. It costs a
sentence to occupy and is **structurally impossible for a dashboard business**: a dashboard
that periodically goes blank is a churn event, and their revenue depends on daily engagement.

**F3 · Evertune's depth makes runs=5 indefensible; their missing trail makes them beatable.**
You cannot out-sample 100×/prompt across 11 models. You do not have to. Depth is purchasable
at $0.007602 × runs; a retrofitted evidence substrate is not.
The counter-position, exact: **"they tell you the margin; we show you the transcript."**

**F4 · Stay out of the prompt-volume war.** Every competitor fights on demand estimation,
where nobody can be audited. aivis measures supply, hash-verified — the only side where an
adversary-proof artifact is possible.

**F5 · The category-wide attack is unanswered.** Brainlabs, 2026-04-20: *"None of your AI
visibility data is accurate. Not Profound. Not seoClarity. Not Peec…"* Five of six vendors
have made **no public response**. It is a standing sales asset for whoever answers first with
artifacts.

**F6 · The market census.** Of 74 AI-visibility tools surveyed: **8%** publish a checkable
methodology, **49%** make accuracy claims with no supporting evidence, and **not one** has an
independent accuracy audit [MEASURED: citedindex.com census, 2026-08-07/16].
An independent 12-platform bake-off against 600 verified prompt-answer pairs found mention
detection averaging **81% across a 27-point spread (67–94%)**, 9% false positives, 72%
sentiment accuracy, and **no correlation between price and accuracy** across $89–$1,200/mo
products [MEASURED: gtechme.com, 2026-06-29].
The IAB's decision-grade tier requires nine thresholds including documented reproducibility.
**Nobody clears it.**

---

## 4. WHY THE COPY IS EXPENSIVE FOR THEM — the only analysis that matters

Every move below is engineering. What blocks each vendor is a **prior commitment**, not a
capability gap. Spend effort only where the move is cheap for you and expensive for them.

| Vendor | What blocks the copy |
|---|---|
| Profound | 700+ enterprise contracts. A published κ of 0.68 puts every one into renegotiation. Raw evidence exposes the gap between panel data and population claims. |
| Evertune | Has published ±1pt. Exposing the trail lets a customer **audit the precision claim**. Closest, and most to lose by completing the set. |
| Peec | ~1 run/prompt/day. An interval at n=1 is undefined. Raising N breaks the unit economics the pricing was built on. |
| Otterly | $29 entry tier. Depth costs money they never charged for. |
| Athena | Already published "95%+ Accuracy." **A vendor who claimed 95% cannot publish a real κ of 0.71.** The prior claim is the lock. |

### The four asymmetric moves, in order

1. **Publish κ with the labelled set.** One labelling pass for you. Writes a procurement
   question — *"what is your extractor accuracy, against what labelled set?"* — that four of
   five cannot answer. You never have to ask it; buyers will.
2. **Ship the recipient-side verifier.** One stdlib file; `verify_hashes()` is already
   written. Their non-disclosure is a choice, not a gap.
3. **Publish the abstention rate.** Free, and structurally unavailable to a dashboard
   business. **Cheapest square, most protected.**
4. **Audit the auditors, as a paid service.** Their marketing becomes your lead source.
   **ILLEGAL until 1–3 are done** — running it first makes you the thing you are charging
   them with.

### What "beat" can mean

Not revenue, not for years. It means **owning the definition the category is measured
against.** The precedent is the MRC stripping Nielsen's accreditation: the referee did not
outgrow Nielsen, it set a bar Nielsen had to answer to and could not.

The converting moment is not a feature comparison. It is the meeting where a CFO asks a CMO
*"how do we know this number is right?"* Nobody in the category has an answer.

**Falsifier:** if buyers do not price methodology, all of this is cost with no return. The
honest test is one conversation where "decision-grade" is quoted back at you. It costs
nothing and has never been run.

---

## 5. THE PRECEDENT CASES — why artifacts beat arguments

- **Nielsen, 2021-09-01.** MRC stripped national TV accreditation for undercounting and lack
  of transparency; the VAB estimated the undercount cost networks **$468M–$2.8B** in a year.
  Nielsen's defence was assertion. Within four months NBCU, WarnerMedia, ViacomCBS and
  Univision had signed with competitors. Reaccreditation took ~19 months.
- **Consumer Reports vs Tesla, 2018.** Measured 152 ft braking, withheld the recommendation,
  **retested the same car** after the OTA fix, published 133 ft. Won by having a fixed
  protocol it could re-run.
- **LMArena, 2025.** Every effective rebuttal was a **pre-existing artifact** — a testing
  policy published 2024-03-01 and confidence intervals already in print.

**The transferable law:** disputes are won with artifacts that existed *before* the dispute.
Nothing built after the challenge lands counts.

**The caution the precedents also carry:** in all three cases the institution held authority
*before* the dispute. aivis would be building authority *through* it, which is a materially
harder problem — and the reason any badge or referee scheme is **out of scope** until the
index has been cited by someone who is not the operator.

---

## 6. CONSOLIDATION — outside anyone's control

Adobe acquired Semrush for $1.9B. Profound at ~$1B is now an acquirer. Sitecore acquired
Scrunch. Lorelight shut down, concluding AI visibility is a feature, not a company.
**The window for an independent measurement brand is open, not permanent.**
