# PREREG — Restaurant AI-Recommendation Test v1 (NYC → MA → DE → CT)

**RUNG R0 — designed, not run. 0 of 1,600 planned responses collected. DRAFT until sealed (see "Seal").**
Written 2026-10-06, before any run. Template: `realtor_v1/PREREG_realtor_test_v1.md`, with its v1.1/v1.2
amendments built in up front instead of discovered afterwards.
Once the first full-run response is collected, nothing above the "Predictions" line may be edited.
Any change = v2 with the reason stated.

## Two questions, and only one of them is answerable by this instrument

**Q1 — measurable here.** When people ask AI assistants where to eat in a given area, which restaurants do
the engines name, how often, and how stable is that roster across repetitions and across engines?

**Q2 — NOT measurable here.** "What percentage of their business do those restaurants gain from AI
recommendations?" aivis records what models *say*. It observes no diner, no visit and no cheque. No
number from Phase 1 is, or can be converted into, a share of anyone's business. Q2 needs first-party
data held by each restaurant; that is Phase 2 below, and it is a recruitment task, not a run.

## Phase 1 design
- Banks: `nyc|ma|de|ct_restaurant_prompts_v1.jsonl`, 20 prompts each, emitted by
  `gen_restaurant_banks_v1.py`. 10 areas × 2 intents per market; 10 intents, each asked twice per market.
  The slot → intent mapping is identical in all four markets, so markets compare slot-for-slot.
- No prompt names a restaurant, chef, chain, guide or review site.
- Engines: ChatGPT, Claude, Gemini, Perplexity. **Web search ON for all four.** Consumer apps search the
  web for local questions; a no-search API call measures training data, which is a different quantity.
  Every row records `web_search` and the resolved model string.
- Reps: 5 per prompt per engine → 400 responses per market, 1,600 across four markets.
- Order: NYC first, alone. MA, DE, CT run only after the NYC decision rule has been evaluated.
- Runner: `run_market_v1.sh` → `run_bank_multi_v2.py`. Each row: engine, model, prompt_id, rep, timestamp,
  request payload, response_text, citations, sha256. `verify_evidence.py` must PASS on every run file.
- **What this samples:** 10 named areas per market and 10 dinner/brunch intents, in English, from the API
  with search enabled. It is not "restaurants in Massachusetts" and may not be described that way.

## Unit definitions
- **Candidate**: a string the extractor reads as a specific eating establishment recommended for the
  prompt's area.
- **Verified restaurant**: a candidate confirmed, by a human opening a primary source (the restaurant's
  own site or its Google Maps listing; URL recorded), to be an open establishment in that area on the
  check date.
- **Closed**: confirmed to have existed, confirmed permanently closed. **Not found**: no evidence it
  exists. **Wrong area**: real and open, but not in the area asked about. These three are counted
  separately and none counts as verified.
- **Name merging**: case, punctuation, a leading "the" and a trailing "restaurant/pizzeria/& co" are
  normalised automatically. Any further merge (nicknames, a brand with several locations) is listed line
  by line in `merges_v1.csv`. A multi-location brand counts once per area.
- **Verification tiers, fixed now** (the realtor run produced 872 candidates; all-candidate verification
  was infeasible and had to be amended after the fact): within each market, verify ALL candidates named in
  ≥10 of 400 responses; verify a random 40 from the 3–9 band, seed = 20261006; candidates in ≤2 responses
  are excluded from every metric. All metrics on verified names are therefore LOWER bounds.
- **Extractor**: must be committed before the first *full* run. Smoke rows may be used to develop it —
  that use is disclosed here, in advance. Its output carries UNVALIDATED_PARSE_PENDING_KAPPA.

## Metrics (every count printed with its denominator)
- R1 — % of responses naming ≥1 verified restaurant, overall and per engine.
- R2 — repetition stability: # verified restaurants named in ≥3 of 5 reps for the same prompt + engine.
- R3 — cross-engine agreement: # verified restaurants named by ≥3 of 4 engines for the same area.
- R4 — concentration: share of all verified mentions in a market taken by its 10 most-named restaurants.
- R5 — bad-recommendation rate: (closed + not found + wrong area) ÷ candidates checked, per tier.
- R6 — cited source domains, per engine (which sites the engines lean on when they name a place).
- R7 — first-named count: how often each restaurant is the first one named in a response.

**The "most-named" table.** Per market: restaurants meeting R3, ordered by responses naming them out of
400, each with a Wilson 95% interval, engines-naming count and R7. It is labelled "most frequently named
in this sample". It is not a ranking: two restaurants whose intervals overlap are not ordered, and the
words "ranks", "rank score" and "#1" stay out until an order-flip delta exists.

## Decision rule (per market, fixed at seal)
- **STABLE TOP SET — proceed to Phase 2 recruitment:** R3 ≥ 10 restaurants AND every one of them also
  counts toward R2 AND R5 for the ≥10 tier ≤ 15%.
- **NO TOP SET:** R3 < 5. "Highest recommended" is not a real object in that market; publish the
  distribution and stop. Phase 2 is not attempted there.
- **Anything between:** INCONCLUSIVE, reported as such. No re-run with different prompts to get a set.

## Phase 2 — attribution (R0, not designed in detail; blocked on Phase 1 and on restaurant consent)
What it would take to say anything about share of business, weakest evidence first:
1. **Referral analytics** from the restaurant's own site/booking page: sessions and reservation clicks
   arriving from AI assistant domains ÷ all sessions. Sees only click-throughs. A diner who reads a
   recommendation and walks in, phones, or searches the name is invisible to it.
2. **Reservation/ordering platform source reports**, where the platform exposes a source field.
3. **A fixed-window intake question** ("How did you hear about us?", AI assistant as one option) asked
   of every party for 2–4 weeks, tallied by the restaurant. Self-report, with its usual bias.
- The best obtainable claim is of the form: "at restaurant X, N of M parties surveyed between dates A and
  B reported an AI assistant as how they found it [REPORTED: restaurant tally]". That is a share of
  *reported discovery* at *that* restaurant. It is not share of revenue (needs covers × cheque by source)
  and not caused by the recommendation (those diners may have come anyway).
- A comparison group is required: restaurants in the same areas that Phase 1 did NOT find in the top set.
  Without it, a high AI share among top-set restaurants cannot be told apart from "busy restaurants get
  mentioned everywhere".
- Underpowered below roughly ten restaurants per group; a result from two or three volunteers is an
  anecdote and may not be published as a rate.
- Standing project position, unchanged by this test: no published evidence links AI recommendation rate
  to revenue (the Q6 null). Phase 2 would be a first measurement, small and local. It may well return a
  number near zero, and that result gets reported like any other.

## Publication rules
- Public: aggregates per market and per engine; named restaurants only in the "most-named" table, with
  counts, denominators, intervals and the run date.
- Never tell a restaurant it is "ranked #1 by AI" or "the top AI-recommended". Report what was observed.
- Never state or imply a percentage of business from AI for any restaurant without that restaurant's own
  Phase 2 data, tagged [REPORTED].
- Closed / not-found names are published in aggregate only until re-checked on the publication date.

## Seal
After the operator has edited anything above and filled in the predictions, from the repo root:

    echo "sacrificial"
    sha256sum restaurant_v1/PREREG_restaurant_test_v1.md restaurant_v1/*_restaurant_prompts_v1.jsonl \
      restaurant_v1/gen_restaurant_banks_v1.py > restaurant_v1/PREREG_SEALED_v1.txt
    git add restaurant_v1 && git commit -m "restaurant_v1: seal prereg + banks before first run"

`run_market_v1.sh full …` refuses to start until `PREREG_SEALED_v1.txt` exists. Smoke runs are allowed
before the seal; they confirm the four search surfaces and nothing else.

---

## Predictions (operator, before the NYC run)
- NYC R3 (restaurants named by ≥3 of 4 engines, same area): ____
- NYC R4 (top-10 share of verified mentions): ____ %
- NYC R5 (≥10 tier, closed + not found + wrong area): ____ %
- Engine with the most distinct restaurants named: ____
- Market of the four with the smallest R3: ____
