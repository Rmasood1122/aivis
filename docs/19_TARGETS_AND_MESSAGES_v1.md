# 19 · TARGETS AND MESSAGES v1 — nine use cases, nine buyer hypotheses, three messages
## 2026-09-02 · pairs with 16 (use-case battery), 17 (screen kit), 18 (sourcing brief)
## §1 is MEASURED against the repo. §2 is R0 THROUGHOUT — hypotheses, not findings.
## §3's messages are screening messages, not sales messages. §4 says when that changes.

---

## §1 — THE NINE HIGHEST-VALUE USE CASES, COMMERCIAL AUDIENCE

Drawn from `16_USECASE_BATTERY_v1.md`, statuses carried over unchanged. The employer-facing
cells (U15, U18) are excluded here — they are career evidence, not a service line, and
presenting them to a company misrepresents what they are.

| Rank | ID | Use case | Status |
|---|---|---|---|
| 1 | U01 | **Category baseline with intervals.** Who AI assistants name in a category, at what rate, with the denominator and confidence interval printed beside every number — including absences (0 of 191, CI 0.0–8.6%, STATUS=COMPLETE) | **LIVE** R2 |
| 2 | U02 | **The recipient checks it without our software.** Report ships with its evidence file; the checker is stdlib Python, no install, ran clean in a third-party container | **LIVE** R2 |
| 3 | U11 | **Verbatim excerpts with row hashes.** The exact text the model produced, kept and quotable. No competitor in the nine retains the text | **LIVE** R1 |
| 4 | U09 | **It refuses to score when it shouldn't score.** `INSUFFICIENT_EVIDENCE` as the only legal abstention; unparseable runs excluded, never folded in as zeros | **LIVE** R1 |
| 5 | U04 | **Pre-registered before/after study on a real intervention.** Outcomes committed in writing before the first measurement, including the null | **LIVE** as offer, R0 |
| 6 | U13 | **Honest non-separation.** Bootstrap B=20,000; where two brands are not statistically separated, the report says so rather than ranking them | **LIVE** R1 |
| 7 | U12 | **Re-verifiable years later.** Raw text plus stored hash plus a public checker means the artifact outlives the vendor relationship | **LIVE** R2 |
| 8 | U05 | **What the model says at buyer intent, versus everywhere else.** Criteria rates by prompt family; the `contributor_warning` gradient (50% long-tail → 0% buyer intent) | **PARTIAL** — unvalidated parse until κ publishes; must be labelled so |
| 9 | U24 | **Publication date provable, not asserted.** Hash-chained receipts anyone verifies offline | **PARTIAL** — chain head has no external anchor yet |

**The two-line version for any conversation:** every vendor in this category hands over a
number. This hands over the number, the transcripts it came from, and a checker that proves
the file wasn't altered — and it declines to answer when the data won't support an answer.

---

## §2 — NINE BUYER HYPOTHESES · ALL R0, NONE TESTED

**Read this before using any row below.** B0 is 0 of 5. Zero buyer conversations have been
run. Every entry is a *guess with a reason attached*, and the reason is named so it can be
checked rather than believed. The column that matters is the last one.

| # | Company type | Why they might care | Evidence class |
|---|---|---|---|
| 1 | **PR / marketing agencies selling "AI Search Optimization" with no instrument** | They already accept written accountability and assert a thing they cannot show. Market exclusivity means every client eventually asks "am I winning here?" | **strongest** — one such firm approached us unprompted; teardown in 07 |
| 2 | **Agencies whose competitor already uses a free AI audit as a lead magnet** | The wedge is live in their market now; someone is taking meetings with it | [MEASURED: web, 2026-08-27] one named competitor doing exactly this |
| 3 | **Cosmetic / aesthetic practices** | High-ticket considered purchase; a single booked consultation justifies the spend | R0 — inferred from 07's vertical, no practice has been asked |
| 4 | **Agencies that already bought Profound / Peec / Otterly / Scrunch** | They have a dashboard and no way to check it. The objection "how do we know this number is right" needs an existing number to attach to | R0 — 04 documents the vendors, not any customer's dissatisfaction |
| 5 | **Mattress, furniture, and considered-purchase retail** | We already hold a 194-row corpus in this category and know the brand landscape | R0 as demand; the *data* is [MEASURED] |
| 6 | **Practices and firms under market-exclusivity contracts** | Exclusivity is sold as dominance; dominance is a measurable claim, and nobody measures it | R0 — structural inference from 07 |
| 7 | **Brands in regulated or claim-sensitive categories** (medical, financial, supplements) | If a model misstates a claim about them, the exposure is not just marketing | **R0 and weakest** — no evidence any such brand has noticed |
| 8 | **B2B SaaS above ~$5k ACV** | Buyers ask assistants for shortlists; being absent from the shortlist is invisible until measured | R0 |
| 9 | **Investors / acquirers diligencing AI-visibility vendors** | Adobe/Semrush at $1.9B, Sitecore/Scrunch, Profound at ~$1B as an acquirer. Diligence needs someone who can grade a methodology | R0 — consolidation is [REPORTED]; the demand is invented |

**Where to spend first:** rows 1, 2 and 4. Row 1 is the only one with any real-world signal
behind it, and rows 2 and 4 are adjacent to it. Rows 7 and 9 are the kind of plausible-sounding
target that fills a deck and returns nothing — they are listed so their weakness is on record,
not because they are recommended.

---

## §3 — THREE MESSAGES

**All three are screening messages.** None contains a product claim, and none contains any of
the ten forbidden words — *evidence, proof, method, methodology, verify, accurate, trust,
reproducible, data quality, confidence.* If any of those appears in an outbound message, then
when the recipient raises the same idea on the call, they are echoing us, and the conversation
produces nothing. That is the whole reason these read plainly.

### MESSAGE A — agencies selling AI visibility (hypotheses 1, 2)

    Subject: how the "are we in AI answers" question gets handled

    Hi <FirstName> —

    I'm doing independent research on how agencies handle it when a client asks whether
    they show up when someone asks an AI assistant for a recommendation.

    This is research, not a pitch — I have nothing to sell you today, and if that ever
    changes I'll say so plainly. I've found very little published on how the question
    actually gets answered in practice, which is why I'm asking people who face it.

    Would you have 20 minutes in the next two weeks? I'd mostly be asking questions.

### MESSAGE B — brands and practices, no prior AI exposure (hypotheses 3, 5, 6, 8)

    Subject: quick research question about how customers find you

    Hi <FirstName> —

    I'm doing independent research on how <practices / brands> in your category think about
    where new customers come from — specifically what happens now that people ask AI
    assistants for recommendations before they ever search.

    Not a pitch, nothing to sell. I'm trying to understand whether this is something you
    think about at all yet, including if the answer is no — that's a useful answer.

    Would you have 20 minutes? I'd mostly be listening.

**Note the deliberate move:** *"including if the answer is no — that's a useful answer."*
Group B qualifies by never having considered this. Inviting the no both raises the response
rate and keeps the person honest instead of performing familiarity.

### MESSAGE C — already bought a competitor tool (hypothesis 4)

    Subject: research — what happened after you bought an AI visibility tool

    Hi <FirstName> —

    I noticed you've worked with tools that track brand visibility in AI answers. I'm doing
    independent research on what actually happens after a team buys one — what gets used,
    what gets ignored, and what you ended up doing with the numbers.

    Not a pitch and not a competitor sales call. I have nothing to sell you today.

    Would you have 20 minutes? I'd mostly be asking questions.

**Careful with C.** Only send it where the tool purchase is publicly visible on their profile
or site. Guessing and being wrong opens the conversation with a correction.

---

## §4 — WHEN THESE BECOME SALES MESSAGES

Not yet, and the sequence is not arbitrary:

1. **B0 evaluated** — five screened conversations, P1 counted against the sealed rule. Until
   then the messages are the measurement instrument and a pitch destroys the instrument.
2. **κ published with its labelled set** — until extraction error is measured, no accuracy
   language of any kind is available, and §1's U05 travels only with its caveat.
3. **One delivered pilot with cleared payment** — this unlocks the words *we* and *customers*.
   Delivered audits today: 0.

Until all three, the terms *verifiable · tamper-proof · signed · audit-grade · accurate ·
customers · we* stay out of every outbound message. Available and earned right now:
**tamper-evident, hash-verified.**

**The specific trap.** The most tempting pitch is *"other vendors can't prove their numbers."*
That is the audit-the-auditors move, and 04 §4 marks it unavailable until κ, the abstention
rate, and the verifier have all shipped — one of three is done. Leading with it while our own
extractor accuracy is unmeasured invites one question we cannot answer, from the most
qualified prospect in the room.

---

## §5 — DEFEATED-BY

- **Quoting §2 as if it were research.** Nine hypotheses, zero conversations. Saying "these
  are the companies that need this" out loud converts a guess into a claim.
- **Mixing a pitch into a screening message** because the recipient seems warm. One pitch and
  that conversation stops counting toward B0.
- **Sending Message C on a guess** about what they bought.
- **Dropping U05's "unvalidated parse" label** because it weakens the slide.
- **Treating five conversations as demand evidence.** Charter §3's floor is n=40 across ≥2
  channels. B0 is a gate; a demand claim is a different bar.

---
TARGETS AND MESSAGES v1 · §1 MEASURED · §2 R0 throughout · §3 zero-claim · 0 of 5 conversations
