# 07 · TEARDOWN — Credible PR (crediblepr.com)

**Date:** 2026-08-27 · **Method:** direct page fetch + link-structure inspection + web search.
**Rung: R2** — every finding below is checkable by a stranger from public sources in under an
hour. Nothing here required access to their systems.

**This is not an AI-visibility audit.** No audit was run: no API credentials in the container
(401, zero credential env vars, probed 2026-08-27), so no live multi-engine measurement was
possible. This is a **claims-and-surface teardown** — the Tier-2 service the plan names, and
the first one ever run on a real company.

---

## 0. WHAT THEY ARE

PR / visibility agency for cosmetic and aesthetic practices. Six services: top-tier media
placements, AI Search Optimization, Google Maps SEO, Google Ads, Meta Ads, podcast
placements. Market exclusivity — one cosmetic practice per market. 30-day guarantee on
placements. Positioning line: *Authority + Trust + Positioning.*

---

## F1 · The featured-media evidence is contributor-channel, not editorial
**[MEASURED: URL structure of their own proof links, fetched 2026-08-27]**

Their own citations carry the answer:

- USA Today piece sits at `/story/special/contributor-content/`
- Forbes piece sits at `/sites/<contributor-name>/` — the contributor network, not staff editorial
- Yahoo Finance item matches the title and URL pattern of syndicated release content

**This is legal, widespread, and not an accusation.** But it is load-bearing, and their own
guarantee proves it: **you cannot guarantee editorial coverage in Forbes within 30 days.** No
agency can. A guarantee of that kind is only structurally possible through a paid or
contributor channel. **The guarantee is the disclosure.**

Context [MEASURED: web search 2026-08-27]: "Contributor Content" is a documented gray area —
publications have been asked to clarify what the label means and whether compensation is
involved, and the FTC has held that where an advertisement strongly resembles editorial
content, disclaimers may not overcome the deceptive net impression.

---

## F2 · The whole product rests on one unmeasured assumption
**[UNVERIFIED — nobody has measured this, in this vertical or any other]**

The pitch requires that contributor-channel placements carry weight with AI retrieval
comparable to editorial. **Nobody knows if they do.** They might carry more (volume,
keyword-dense, widely syndicated) or far less (models increasingly weight source authority
and may discount contributor networks).

**This is the most valuable open question in the engagement.** It is measurable. Nobody in
this vertical is measuring it. Pitch it as the open question, **never as a finding.**

---

## F3 · Claim rungs, under the project's own ladder

| Claim | Rung | Note |
|---|---|---|
| "Guaranteed features in Forbes, USA Today" | **R3+** | Checkable, evidenced, and they carry the risk |
| "Show up first when prospects ask AI for recommendations" | **R0** | No measurement, no before/after, no instrument |
| "Schema updates *can* influence Perplexity within 2–4 weeks" | **~R1** | Genuinely hedged. Credit where due — more careful than most of this category |
| "Reserved for one cosmetic practice per market" | structural | Verifiable by contract |

**The gap between row 1 and row 2 is the business risk: they guarantee what they can prove
and assert what they cannot.**

---

## F4 · The vertical's ranking signals are purchasable, and AI engines ingest them
**[MEASURED: search result, 2026-08-27]**

A search of this competitive set surfaced *"Top 5 Best Reputation Management Companies for
Plastic Surgeons Ranked in 2026"* — naming a firm #1, distributed via **EINPresswire**. A
paid press release, formatted as an industry ranking.

**Models read that.** In this category, AI-visibility rankings are already being shaped by
content that costs money and looks like research. Not a hypothetical gaming vector — live,
now, and the strongest available argument for an instrument that publishes its method.

---

## 5. THE COMPETITIVE SET

Nearest five by service overlap [REPORTED: web search 2026-08-27, not verified page-by-page]:

| Agency | Note |
|---|---|
| **Society22PR** | Plastic-surgery PR; leads with $67M client revenue and 25,000+ procedures |
| **Medical Marketing Firm** | **The one that matters.** AI-native, sells AEO explicitly, and already offers a *"Free AI Marketing Audit"* as its lead magnet |
| True North Social | SEO/PPC for plastic surgeons |
| Brenton Way | Broad plastic-surgery marketing |
| Reputation Pros / Keever SEO | Suppression and reputation management |

**In this vertical the AI audit is already the wedge.** Someone is using it to take meetings
and almost certainly cannot back it with evidence. That is simultaneously the competitive
threat and the confirmation that the wedge works.

---

## 6. THE STRATEGIC READ

**Credible PR is not a subject for an audit. They are the buyer profile.**

- They sell AI Search Optimization with **no instrument**
- They already accept accountability in writing (a 30-day guarantee)
- Market exclusivity means every client eventually asks *"am I actually winning in my
  market?"* — a question only measurement answers
- A direct competitor is already using a free AI audit to open conversations

**Screen rule 4 applies.** They came inbound, so they self-selected for interest. Record as a
**warm lead, separately from the five B0 conversations.** Counting them poisons B0.

To run a real audit for them: a cosmetic-practice prompt bank (their vertical, not
mattresses), the multi-prompt bank command, and credits. **≈$0.70 per practice** at 30
prompts × 3 runs on one engine.

---

## 7. THE BIG BUILD, IF THEY PARTNER

**A before/after cohort study on placements they are already selling.**

They control the intervention. A practice gets a placement on a known date. That is a natural
experiment sitting unused across their entire book of business, and nobody in this category
has run it.

    measure AI recommendation rate before placement
    placement lands, date recorded
    re-measure at 30 / 60 / 90 days
    control against untreated competitors in the same market and the practice's own pre-period

**Join 1** — does the intervention move the metric? (Answers F2.)
**Join 2** — does the metric move consultations? *They* have the consultation data.

**Join 2 is the high-value one.** A surgeon does not buy AI visibility; they buy booked
consultations. Every vendor in this category sells a proxy that has never been connected to
revenue.

### Why the pairing is required
Profound has money and an instrument and **no intervention** — they observe, they don't
cause. Agencies have the intervention and the outcome data and **no instrument, and no
appetite to publish a null.** aivis has the instrument and **no clients.** Each party alone
is missing something the others cannot hand over quickly.

### The three ways it fails
1. **Confounding.** Six services running at once makes attribution impossible. The study
   needs staggered delivery on a subset — an operational concession that costs them real
   money. **That, not the code, is the hard part.**
2. **Power.** Twenty practices with a noisy outcome detects only large effects. Pre-register
   the minimum detectable change *before* the first measurement, or a null result cannot be
   distinguished from insufficient data. These are not the same thing.
3. **Both joins can come back null.** If placements don't move AI recommendations, their AI
   pitch dies. If AI recommendations don't predict consultations, **the whole category's
   premise dies — including aivis's.** That second result would be the most valuable finding
   anyone has produced in this space and very hard to sell.

**Pre-commit in writing to what happens under each outcome, before anyone sees a number.**
Otherwise the golden set gets recut until the grade improves.

**Timeline:** Join 1 is a quarter minimum. Join 2 is two to three. Anyone promising faster is
selling cosmetics.

---

## 8. STATUS

**Unanswered as of 2026-08-27.** The reply costs ~20 minutes, needs no credits, no code, and
no gate green. The outreach-without-claims template applies: **zero product claims**, the ask
is for their expertise. Under §6 of the charter, the banned list governs.

`OUTBOUND: 0/1`
