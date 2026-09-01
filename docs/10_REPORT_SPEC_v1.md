# 10 · REPORT SPEC v1 — the aivis report, designed against the top-5
## 2026-09-01 · RUNG R0 (designed, not built) · Recipients: Sep 8 meeting (specimen page), then pilot #001
## Competitor facts below are [REPORTED: web, 2026-09-01] from vendor pages and reviews — re-fetch before quoting to a buyer.

---

## §1 · WHAT THE TOP-5 REPORTS CONTAIN (the anatomy every buyer already expects)

| Element | Profound | Evertune | Peec | Scrunch | Otterly |
|---|---|---|---|---|---|
| Single composite score | Visibility Score + good/fair/poor rating | AI Brand Score 0–100 (frequency × position) | Visibility % | Visibility metrics | Visibility % |
| Share of voice vs competitors | yes, leaderboard | yes, index | yes | yes | yes |
| Average position | yes | yes (weighted in) | yes | yes | basic |
| Sentiment | yes, themed, with output examples | yes | 0–100 score | yes | basic |
| Citations / sources | citation share, source tracking | Topic/Brand Relevance per source URL | source view by domain/page type | citation analytics | basic |
| Trend over time | yes | weekly/report cadence | daily | yes | daily |
| Engines covered | ChatGPT, Perplexity, Gemini, AI Overviews+ | claims 9–11 incl. consumer surfaces | 5+ | 7+ | several |
| Runs-per-prompt ON THE REPORT | no | 100×/prompt claimed on site, ±1pt | no (~1/day implied) | no ("single runs mislead" — blog) | no |
| Interval on any customer-facing number | no | claimed | no | no | no |
| Raw transcripts available to recipient | no | no ("reporting API on roadmap") | no | no | no |
| Abstention / insufficiency refusal | no | no | no | no | no |
| Model version + temperature declared | no | partial | no | no | no |
| Recipient can verify without vendor software | no | no | no | no | no |
| Denominator printed beside every count | no | no | no | no | no |

**The read:** all five converge on the same seven-element anatomy (score, SoV, position, sentiment, citations, trend, engines). The bottom six rows are empty across the board — and the bottom six are exactly what aivis already has built or specified. The design rule follows: **match the anatomy so the report is instantly legible to a buyer trained on competitor reports; own the bottom six rows, printed on the face, not in an appendix.**

---

## §2 · THE AIVIS REPORT — page by page

Every page rule below states BUILT / PARTIAL / NOT BUILT against the repo as of `4311e3a`.

### Page 1 — The Answer Page
- Headline mention rate per engine, **with Wilson interval beside every number** [PARTIAL: computed, discarded at dimension layer — board #6]
- Position-in-answer (first-three rate) **only where candidate list ≥ 5** — the D1 guard, already structural [BUILT]
- **The face block, top-right, no competitor has it:** `ENGINES n · PROMPTS n · RUNS/PROMPT n · CLEAN n of ATTEMPTED n · MODEL IDS · TEMP · BANK vX · RUNG` [PARTIAL: data exists per row; layout not built]
- Rung printed. SPECIMEN banner iff any ⟦placeholder⟧ present [BUILT as policy, D02]

### Page 2 — Competitive Set
- Mention + first-three per brand, per family, **denominator on every row** (the D3 lesson: errors cluster by family)
- Separation stated honestly: bootstrap-style "not separated" where CIs overlap — the P(Casper>Tempur)=0.870 class of finding, which no composite-score vendor can print without breaking their own product [PARTIAL: method proven on mattress data]
- **No composite score. Ever.** The SRS=100−PS catch is the reason, and one sentence on the page says so.

### Page 3 — What the Model Says When It Says You
- Criteria rates from `criteria_miner` against a DECLARED canon, labelled **unvalidated parse** until κ is published [PARTIAL: tool built, κ pending]
- 2–3 verbatim response excerpts with row hashes — the transcript-keeping advantage made visible [BUILT: data]

### Page 4 — Abstentions and Refusals
- The abstention rate with its population — B3, the square no dashboard business can occupy [PARTIAL: rule specified, page not built]
- Everything the report refuses to claim, and what would unlock each claim (mirrors the public invariants) [BUILT: policy]

### Page 5 — Check This Yourself
- The evidence file ships with the report. `verify_evidence.py` is public, stdlib, no aivis install [BUILT, R2-verified by a third party 2026-09-01]
- Bundle digest printed; three-line verification recipe; chain receipt for the method page [BUILT]
- Printed limitation, verbatim from the checker: a hash proves the file wasn't altered after collection, not that collection was honest. Printing the limit IS the differentiator.

---

## §3 · ENGINE MATRIX — honest surfaces only

| Engine | Access | Surface declared on report | Status |
|---|---|---|---|
| Claude | Anthropic API | model id, temp 0.0 | WIRED |
| ChatGPT | OpenAI API | "developer API, not consumer app — consumer app adds search/memory" | NOT BUILT |
| Gemini | Google API | same declaration | NOT BUILT |
| Grok | xAI API | same | NOT BUILT |
| Perplexity | Perplexity API | same; most research-relevant engine | NOT BUILT |
| Copilot | no public API | **EXCLUDED, stated on face with reason** | excluded v1 |

The declaration is the moat move: competitors blur API vs consumer surfaces (Evertune explicitly pools both). aivis declares its surface and prints the gap as a limitation. Cheaper than browser automation and more honest than pooling.

**Cost, full 5-engine report:** 5 engines × 30 prompts × 7 runs = 1,050 calls ≈ $8.00 [EST: extrapolating $0.007602/call [MEASURED: Claude only] to other engines — re-measure per engine, C02-style, before quoting margin to anyone].

---

## §4 · BUILD DELTA — what stands between today and this report

| Gap | Board item | Cost class |
|---|---|---|
| Wilson intervals to the page | #6 | near-zero |
| Multi-prompt bank command | #7 (I-9) | small, ~$0.68 test |
| Engine adapters ×4 | new | the real build; gated on spend gate |
| Abstention page | 14 | writing + small code |
| κ published (unlocks "parse" → measured) | #8–9 / Ahmad | one external pass |
| Report layout (pages 1–5) | new | one emit script on make_report.py's pattern |

**Sequencing rule:** the Sep 8 specimen needs NONE of the engine adapters. `pr_agency_run4.jsonl` (191 clean rows, their vertical, sealed pre-reg) + `make_report.py` = a real one-engine report with zero placeholders. Multi-engine is the roadmap page inside that report, not its prerequisite.

---

## §5 · DEFEATED-BY

- **A composite score sneaking in** because buyers ask for "one number." The answer is the per-engine mention rate with its interval; the refusal is the product.
- **Shipping 5 engines at N=1 to match coverage claims.** Peec's exact failure. Fewer engines at N=7 beats more at N=1, and the face block makes the difference visible.
- **The specimen leaking as real.** SPECIMEN banner, ⟦brackets⟧, never quoted — charter §5b already governs.
- **Quoting §1's competitor table externally without re-fetching.** It is [REPORTED: 2026-09-01] and decays like everything in 04.

---
REPORT SPEC v1 · R0 · recipient: Sep 8 specimen, then pilot #001 · Lane I hours: log them

## AMENDED 2026-09-01 — §6 BUILD ORDER v1 (approved session 5, G0 override logged)
NOW (no gate, serves Sep 8):
  - Wilson intervals -> product layer (board #6, near-zero)
  - Pilot charter append: stagger replaced by natural timing variation
  - Key rotation check at console.anthropic.com, then RR-1b bridge (battery B01)
ON FIRST BUYER SIGNAL naming an engine:
  - One adapter (OpenAI), N>=7, declared surface
ON SIGNED FOUNDING ENGAGEMENT:
  - Attribution kit intake artifact; remaining adapters as named
NEVER WITHOUT ITS GATE:
  - Second-opinion service (kappa published first)
  - Index (kappa >= 0.75 AND external citation)
