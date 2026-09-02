# 17 · B0 SCREEN KIT v1 — outreach, opener, and the sealed prediction
## 2026-09-02 · RUNG R0 until the first message is sent · recipient: five named strangers
## Serves M1–M5 in 05 §3 and E02–E06 in 08. M0 (the inbound) is CLOSED and is NOT one of these five.

**The gate this serves, quoted exactly from 05 §0:**

    B0  In 5 screened conversations, >= 2 of 5 raise evidence, reproducibility, method
        or trust UNPROMPTED, before aivis is described.

Three words in that sentence do all the work and each one defeats the gate if ignored.

**UNPROMPTED** — they raise it, not you. If you ask "how do you know that's right?", any answer
they give is prompted and the conversation scores zero on P1 regardless of what they say. The
question ladder in §2 is built word-by-word to avoid triggering it.

**BEFORE aivis is described** — the moment you explain the instrument, the window shuts. You
may describe it afterward. Everything said after that point is unusable as B0 evidence.

**SCREENED** — 05 names the defeater: *a friend doing you a favour. The most expensive
datapoint available.* Screen rule 4 also bars anyone inbound; they self-selected for interest,
which is the opposite of what the gate measures. **Credible PR is excluded. Counting them
poisons B0.**

---

## §1 — THE OUTREACH MESSAGE (zero product claims)

Charter §6 banned for aivis until earned: *verifiable · tamper-proof · signed ·
non-repudiation · audit-grade · court-ready · accurate · any accuracy figure · ranks ·
customers · we.* None appears below. Nothing below describes the instrument at all, because
describing it before the call would shut the window before it opens.

    Subject: how the "are we in AI answers" question gets handled

    Hi <name> —

    I'm doing independent research on how <agencies / brands in this category> handle it
    when a client or a boss asks whether they show up when someone asks an AI assistant
    for a recommendation.

    This is research, not a pitch — I have nothing to sell you today, and if that ever
    changes I'll say so plainly. I'm asking because I've found very little published on
    how the question actually gets answered in practice.

    Would you have 20 minutes in the next two weeks? I'd mostly be asking questions and
    listening.

    <signature — name, no company tagline, no product line>

**Why it is this short.** Every added sentence about the instrument is a sentence that
contaminates the window. The ask is for their expertise, which is the one thing you can
request honestly at rung R1/R2 with zero delivered audits.

**Channels.** Charter §3: a batch below n=40 across ≥2 channels is UNDERPOWERED and may not be
recorded as evidence about demand in either direction. Five conversations satisfies **B0**;
it does not license a demand claim. Those are different bars and the difference is not a
rounding error.

**Spread requirement, from 05 §3 M1–M3:** at least one who already bought a competitor
(Profound, Peec, Otterly, Scrunch, Evertune), and at least one who has never heard of the
category. A sample of five enthusiasts measures enthusiasm.

**Sourcing pools, cheapest first**
1. Agencies selling "AI Search Optimization" with no instrument — the profile 07 documents.
2. Marketing leads at brands in a considered-purchase vertical.
3. **The Tempur-Pedic floor.** High-ticket buyers at point of sale, which is a data asset the
   academic field rates very low confidence on. Different population from the other two —
   record which pool each conversation came from, because pooling them hides the difference.

---

## §2 — THE CALL OPENER AND QUESTION LADDER

**Rule: questions 1–5 contain none of these words** — evidence, proof, method, methodology,
verify, accurate, trust, reproducible, data quality, confidence. Speaking any of them converts
an unprompted mention into a prompted one and costs you the datapoint.

**Open (say this, then stop talking):**

> "Thanks for the time. I'm going to ask a lot and say very little — if I go quiet it's
> because I'm writing. Start me anywhere: when a client asks whether they're showing up in
> AI answers, what happens next?"

**The ladder — first five, in order, no substitutions**

    Q1  Walk me through the last time that came up. What did you do?
    Q2  Then what happened?
    Q3  What was the hardest part of that conversation?
    Q4  If you could hand them one thing that ended the question for good, what is it?
    Q5  What would have to be true for you to spend real money on this?

**Silence is the instrument.** After each answer, count three seconds before speaking. The
unprompted mentions almost always arrive in the pause, not in the answer.

**THE WINDOW CLOSES after Q5, or the moment you describe aivis, whichever comes first.**
Write the closing timestamp down. Everything before it is B0 evidence; everything after is
context.

**After the window — now you may probe and pitch**

    Q6  Have you tried any of the tools in this space? Which, and what happened?
    Q7  When a vendor hands you a number, what do you do with it?
    Q8  Who else should I be asking?

Q7 is the one that tests the position directly, and it is deliberately outside the window —
its answer is interesting but **is not scored for B0**, because you asked it.

**Capture.** Record their responses verbatim where you can, per E01–E06's pass evidence. Write
the transcript within the hour; a transcript reconstructed at day's end is fiction, the same
defect as a spend-gate log written from memory.

---

## §3 — THE SEALED PREDICTION FILE

One per conversation, sealed **before** the call: `runs/buyer_pred_<n>_v1.json`. Sealing
after is worthless — the entire function is to stop the bar moving once you have heard the
answer, which is exemplar X4's negative case.

**⚠ P1 AND P4 ALIGNMENT — READ BEFORE FIRST USE.** 05 §3's kill rule reads
`P1 = 0/5 AND P4 <= 1/5 -> positioning falsified`, so P1 and P4 already carry definitions in
the sealed B0 pre-registration dated 2026-08-27. **I do not have those definitions in view.**
Open the sealed file and confirm the two below match it. If they differ, **the sealed original
governs and these are discarded** — aligning to the seal is correct; rewriting the seal is the
failure.

    P1  they raise evidence, reproducibility, method or trust UNPROMPTED, inside the window
    P2  they can name what they currently do about AI visibility, concretely
    P3  they have paid, or seriously evaluated paying, any vendor in this category
    P4  they state a number, a budget, or a range without being asked for one
    P5  they ask you a question about how something would be measured
    P6  they name a person internally who would have to approve spend

**Calibration rule, binding.** If every confidence in a file lands within five points of every
other, the file is REJECTED and rewritten. Uniform confidence is not a prediction, it is a
refusal to predict, and it is a documented habit on this project. Spread them or don't seal.

**Scoring.** After the call, append outcomes and compute the Brier score
(`mean((confidence - outcome)^2)`, outcome 1 or 0). Lower is better; 0.25 is what you get for
guessing 50% on everything. Across five conversations the Brier trend matters more than any
single call, because it measures whether you understand this market or only believe you do.

**Template** — copy to `runs/buyer_pred_1_v1.json` and fill before dialling:

```json
{
  "conversation_id": 1,
  "sealed_at_utc": "",
  "target_role": "",
  "target_org_class": "agency | brand | point-of-sale buyer",
  "sourcing_pool": "cold-outbound | referral | floor",
  "inbound": false,
  "already_bought_competitor": null,
  "heard_of_category": null,
  "window_closes_after": "Q5 or first description of aivis",
  "predictions": [
    {"id": "P1", "statement": "raises evidence/reproducibility/method/trust unprompted, in-window", "confidence": null, "outcome": null},
    {"id": "P2", "statement": "names concretely what they do about AI visibility today", "confidence": null, "outcome": null},
    {"id": "P3", "statement": "has paid or seriously evaluated paying a vendor in this category", "confidence": null, "outcome": null},
    {"id": "P4", "statement": "states a number, budget or range unasked", "confidence": null, "outcome": null},
    {"id": "P5", "statement": "asks how something would be measured", "confidence": null, "outcome": null},
    {"id": "P6", "statement": "names an internal approver for spend", "confidence": null, "outcome": null}
  ],
  "brier_score": null,
  "transcript_path": "",
  "notes_written_within_hour": null
}
```

**Seal it before the call:**

```bash
: sacrificial
cd ~/caai-test/ai-visibility-audit
sha256sum runs/buyer_pred_1_v1.json
git add runs/buyer_pred_1_v1.json
git commit -m "seal: buyer_pred_1 before conversation 1 (B0/M1)"
git push
```

The git date is the seal. F01 tests exactly this property — `seal < run` — for every study on
record, and a prediction file is a study with n=1.

---

## §4 — EVALUATING B0 AFTER FIVE

Count P1 across the five files. `>= 2 of 5` → B0 PASSES, the instrument bar becomes worth
clearing, Lane I's spend cap lifts. `< 2 of 5` → **B0 FAILS: the position does not matter to
buyers.** 05 §9 is unambiguous — stop Lane I, re-derive from the transcripts, and do not
average the result with the prior hypothesis.

`P1 = 0/5 AND P4 <= 1/5` → positioning falsified outright. Pre-committed, and it costs nothing
to honour and everything to ignore.

**Publish the result either way.** A B0 failure caught at five conversations is the cheapest
falsification available to this project and is worth more than a green one, because the
alternative is discovering it after the instrument is finished.

---

## §5 — DEFEATED-BY

- **A friend doing you a favour.** Named in 05 as the most expensive datapoint available.
- **Counting Credible PR.** Inbound, self-selected, excluded by screen rule 4.
- **Speaking a window word.** One "how do you know?" in Q1–Q5 and P1 is unscoreable.
- **Sealing after the call**, or writing the transcript tomorrow.
- **Uniform confidences.** A file where everything is 80% predicts nothing and cannot be Brier-scored meaningfully.
- **Five conversations quoted as demand evidence.** Charter §3 sets that floor at n=40 across ≥2 channels. B0 is a gate, not a market study.
- **Describing the instrument early because the silence is uncomfortable.** The silence is the measurement.

---
B0 SCREEN KIT v1 · RUNG R0 · 0 of 5 conversations · POPULATION 5 · sealed predictions 0
