# 14 · SEALED PRE-REGISTRATION — PR agency visibility run
## v1 · sealed 2026-08-29, BEFORE any call is placed
## RUNG: R0 until the run exists. Nothing below is a measurement.

---

## WHAT IS BEING MEASURED

Whether AI assistants name PR agencies when asked buyer-language questions about
getting press coverage — and if so, which ones.

**Unit of observation:** one (prompt × run) response.
**Outcome 1:** mention rate — share of responses naming an agency at all.
**Outcome 2:** first-three-by-string-position — NOT a rank. The order a model lists
names in prose is not a ranking, and the project's claim ladder bans "rank" until an
order-flip delta exists. The metric is named for what it is, everywhere it appears.

**Design:** one engine (claude-sonnet-4-6), temperature 0.0, 30 prompts × 7 runs = 210
calls, open-ended retrieval. No prompt names a candidate agency.

**Cost:** ≈$1.60 [EST at $0.007602 per measurement — read the real figure off the console].

---

## THE FOUR OUTCOMES, COMMITTED BEFORE THE RUN

Sealed so that no result can be reframed after the fact as a reason to open a
conversation. Whichever occurs, the response is written here already.

### A · The models do not name agencies at all
Responses return advice ("build relationships with journalists", "write a press
release") rather than vendors. Agency mention rate near zero across all five families.

**Plausibly the single most likely outcome.** Read: AI visibility carries little or no
weight in this category's buying process. This kills the AI Search Optimization pitch
AND kills aivis's value in this vertical simultaneously.

**Response:** publish it. Nobody in the category will publish a null and it is
immediately checkable by anyone with an API key. Tell Credible PR plainly.

### B · Credible PR appears; the competitive set does not
Their placements are reaching the models and their competitors' are not.

**Response:** their product is supported and there is nothing to sell them. Say so.
A vendor who reports a finding against their own interest is making the only
credibility move available at rung R1.

### C · Nobody in the boutique set appears; only large national firms do
Contributor-channel and boutique placements are not reaching model retrieval at this
scale. Directly relevant to 07 F2.

**Response:** the finding Credible PR most needs and least wants. Deliver it with the
limitations leading, not trailing.

### D · Mixed, no clean pattern
Some names appear at low rates, no separation.

**Response:** report the rates with Wilson intervals and ABSTAIN on mechanism.
ABSTAIN is a complete output.

---

## ABSTENTION RULES, SEALED

Output ABSTAIN with the reason rather than a weak answer when:

- fewer than 15 distinct agency names appear across the whole run — below that, the
  first-three metric collapses toward the mention rate (defect D1, measured 2026-08-29)
- an agency's rate interval straddles the comparison it is being used to support
- the seeded candidate list and a manual scan of the raw text disagree on which names
  are present — the extractor is unvalidated and the disagreement is the finding

---

## WHAT MAY NOT BE CLAIMED FROM THIS RUN, UNDER ANY OUTCOME

- **No causal claim.** This is cross-sectional. It cannot show that placements cause
  or fail to cause model recommendation. Published evidence on that link is
  observational (Martinez, arXiv:2607.14035). Write "associated with", "co-occurs
  with", never "drives", "causes", "gets you ranked".
- **n=1 agency.** One organisation, one engine, one day. Not evidence about the
  category.
- **Banned vocabulary** (charter §6): verifiable · independently verifiable ·
  tamper-proof · signed · non-repudiation · audit-grade · court-ready · accurate and
  any accuracy figure · ranks / rank score · customers · we.
  Available: tamper-evident, hash-verified.
- **No accuracy figure.** Extractor accuracy has never been measured. Every name count
  below rests on an unvalidated extraction step, and that sentence ships with the run.

---

## PRE-RUN CHECKLIST — all four are defects measured 2026-08-29

| # | Fix | Why |
|---|---|---|
| 1 | `max_tokens` raised from 1024 | D2: table-formatted responses truncated mid-name; tail rates became floors |
| 2 | Bank ids unique | D-collision: `{p["id"]: family}` last-writer-wins mislabelled 24% of the mattress rows |
| 3 | Candidate list ≥ 15 names | D1: a short candidate list makes first-three identical to mention |
| 4 | Manual scan of raw text for unseeded names | D5 / the Saatva lesson: the seeded list will miss whoever the models actually name |

Item 4 is not optional. In the 2026-08-29 mattress run, the highest-scoring brand
absent from the seeded roster (Saatva, 83.3% mention) was invisible to the extractor
and would have been invisible in the report.

---

## SEED CANDIDATE LIST — starting point only, not the roster

Credible PR · Society22PR · Medical Marketing Firm · True North Social · Brenton Way ·
Reputation Pros · Keever SEO · Edelman · Weber Shandwick · Ketchum · FINN Partners ·
Otter PR · Elevate PR · Ascend Agency · Pressfarm · Publicize · NetReputation ·
Ripley PR · BPM-PR · Facteur PR · Cosmetic PR

n=21. [UNVERIFIED] — assembled from 07 §5 (dated 2026-08-27, itself now amended) plus
names surfaced in a 2026-08-29 web search. Not re-verified page by page. The real
roster comes from the responses, not from this list.

---

## AMENDMENT TO 07 REQUIRED BEFORE THIS RUN

07 describes Credible PR as serving cosmetic practices with one-per-market exclusivity.
Three sources dated 2026-08-29 describe a broader audience: beauty experts, attorneys,
entrepreneurs, founders, and service-based businesses. Either 07 over-narrowed from a
single page or the company has repositioned. The bank above is built for the broader
reading. [REPORTED: web search 2026-08-29 — Inc. profile, company homepage, Haute Living]

---

RUN LOG
    RUNS ........ 0
    STATUS ...... R0. Sealed, never executed.
