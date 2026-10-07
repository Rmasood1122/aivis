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

## AMENDMENT v1.1 — 2026-10-06, written BEFORE the seal and before any full-run response
Status of evidence at this point: 5 smoke rows exist (NYC01 only; 4 clean, 1 error), collected
2026-10-07T01:11–01:31Z. No full-run row exists. Thresholds in "Decision rule" are unchanged.
Where this block and the text above disagree, this block governs.

1. **"Web search ON" is restated as "web-search tool OFFERED".** The engine decides whether to use it.
   In the realtor run, Claude returned zero citations on 29 of 100 rows with the tool in the payload
   [MEASURED: realtor_v1/runs, recount 2026-10-06]. In this test's smoke, Gemini returned 0 citations on
   its one row. Therefore: every per-engine line prints the share of rows with ≥1 citation; no row is
   described as "live search" unless it carries a citation; the row field `web_search` is NOT used as
   evidence (it read true on 100 Perplexity rows that had no search tool in the payload) — the payload's
   `tools` entry and the citation count are.
2. **Output cap raised to 4,096 tokens** (`run_market_v2.sh`). At 2,048, 4 of 100 ChatGPT realtor
   answers ended without terminal punctuation [MEASURED: same recount]; the ChatGPT smoke answer here ran
   6,998 characters. `per_response.csv` flags every answer that ends without terminal punctuation.
3. **Perplexity model string is `perplexity/sonar`.** `sonar` returns HTTP 400 "not supported"
   [MEASURED: smoke 2026-10-07T01:12Z; retry with `perplexity/sonar` clean, 15 citations].
4. **Runner is `run_market_v2.sh`.** `run_market_v1.sh` is superseded and left in place.
5. **The seal hashes git blobs, not disk bytes** (`seal_v1.sh make` / `check`). The `sha256sum` command
   in "Seal" above is superseded: on Windows git rewrites text files with CRLF at checkout, so disk
   hashes differ between machines. The sealed set is: this file, the four banks, the generator, the
   analyzer, its tests, `run_market_v2.sh`, `seal_v1.sh`. `make` refuses while any prediction is blank.
   A full run refuses unless `check` passes — the gate tests that the seal is true, not that it exists.
6. **Correction to "Unit definitions".** "the realtor run produced 872 candidates" cites an intermediate
   count. The population that was verified against was 1,008 candidates, 367 of them in ≥3 responses
   and 45 in ≥10 [MEASURED: realtor_v1/results_v1c/person_candidates.csv, 2026-10-06].
7. **Extractor and metrics code: `analyze_restaurant_run_v1.py`,** committed with this amendment.
   - Built from: the 4 clean smoke rows (console previews; three of them truncated at 1,200 characters)
     and, for markdown structure only, the 399 realtor rows. Smoke rows are excluded from every metric.
   - Method: structural discovery (list heads, line-leading bold, table name column, leaf headings,
     inline bold), then a case-sensitive word-boundary pass over all responses for names discovered
     structurally somewhere. A one-word name needs structural discovery in ≥3 responses before it is
     counted from prose.
   - Checked against an independent list: of 68 human-verified agent names in the realtor project, 62
     are found under the same key and the other 6 under a longer form of the same name (the realtor
     regex had truncated them); of 107 top-tier candidates on that data, 6 are not a person, firm or
     site ("Office", "Track Record", "Armen", "Notable Agents", "Profile", "Marketing Plan")
     [MEASURED: 2026-10-06, read in full]. That is a structure check on a different vertical. It is NOT
     an accuracy figure for restaurants; none exists. Status stays UNVALIDATED_PARSE_PENDING_KAPPA.
   - Known limits: a name no engine ever places in a list head, table, heading or bold span is missed;
     a prose match can hit a phrase that is not the restaurant; a table with no recognisable name
     column is read from its first text column; first-named needs a structurally placed name.
8. **Verdict `noise` added** to open / closed / not_found / wrong_area: a candidate that is not a
   place at all (a label or phrase the extractor let through). Noise is excluded from every metric and
   from the R5 denominator, and its count is printed beside R5. This raises R5; it cannot lower it.
9. **"≤2 responses are excluded from every metric" is applied literally:** R1 and first-named (R7) are
   computed on names in ≥3 responses, like R2, R3 and R4.
10. **R3 counts distinct names.** A multi-location brand that qualifies in several areas counts once.
    Tiers are market-wide response counts.
11. **R2 denominators.** "≥3 of 5 reps" is evaluated on the clean rows that exist. The summary prints how
    many prompt+engine cells have exactly 5 clean reps. Error rows are not topped up. An engine that
    fails outright may be re-run to a new file (`RUN_TAG`), which replaces the failed file in the
    analysis; the analyzer refuses the same engine+prompt+rep twice.
12. **No decision until every row of the verification sheet has a verdict** — tier A and the tier B
    sample both. Verdicts for names not on the current sheet are refused, so a merge list written after
    checking cannot silently change which names were verified.
13. **`merges_v1.csv`** has columns `from_key,to_key`; rules that match nothing are printed.
14. **Verification sample:** drawn by the analyzer (`random.Random(20261006).sample` over the sorted 3–9
    band); the written `verify_sheet.csv` is the record, and the Python version is printed beside it.

## AMENDMENT v1.2 — 2026-10-06, written BEFORE the seal and before any full-run response
Reason: the analyzer was run for the first time on the four complete smoke answers (operator machine,
Python 3.13.5, 2026-10-07 ~02:00Z). Evidence is still the same 5 smoke rows; no full-run row exists.
Thresholds in "Decision rule" are unchanged. Where this block and anything above disagree, this governs.

1. **What the first full-row check found** [MEASURED: operator console, candidates.csv of
   `smoke/extract_check_v1`, read in full]: 68 distinct candidates, of which at least 10 are not a
   single restaurant — six award-category heads ("Best Brunch", "Best Deli", "Best Bakery",
   "Best Burger", "Best Diner", "Best American Restaurant"), "Wanderlog's Picks", and three strings
   holding two or more restaurants written together. One more ("The Bomb") is a sandwich, not a place.
   Every one occurred in a single response, so none reached the ≥3 floor at n=4; in a full run the
   award heads would have.
2. **Extractor changed in response — a post-hoc change to the instrument, disclosed here, made
   before the seal.** (a) A bare bold head ending in a colon, or a head ending in a list word
   ("Picks", "Favorites", "Winners" …), hands its place to the names nested under it. (b) An unordered
   bullet with no separator counts only under such a head, and never if it is one word. (c) A bold
   span on a line that opens with a food label ("What to get:", "Highlights:") is a dish and is
   skipped. (d) A table cell holding three or more comma-separated entries is read as that many names.
   (e) Names written together ("A, B, C", "A & B") are split only when the market's own answers show
   the parts are places: two parts need both seen alone; three or more may carry one unseen part of
   two or more words. "Sal, Kris & Charlie's Deli" and "Tootles & French" stay whole. (f) A one-word
   colon-terminated head seen twice in one answer is a label; a multi-word one needs three.
   A name beginning "Best" is NOT rejected on that ground: Best Pizza is a restaurant in Williamsburg
   and this bank asks about pizza there.
3. **What is and is not known after the change.** 46 tests pass, including fixtures built from the
   printed lines of that ChatGPT answer. On the realtor rows the changed extractor still finds 62 of 68
   human-verified names under the same key (the other 6 under a longer form) and 6 of its 106 top-tier
   candidates are not a single person, firm or site [MEASURED: 2026-10-06]. The changed extractor has
   NOT yet been run on the complete smoke answers; that result is to be read by the operator before
   sealing. Status stays UNVALIDATED_PARSE_PENDING_KAPPA. No accuracy figure exists.
4. **Output cap raised again, to 8,192 tokens** (item 2 of v1.1 said 4,096). The Gemini smoke answer
   ended mid-structure ("…\n\n---\n\n###") at 4,211 characters under the 2,048 cap, with 0 citations
   [MEASURED: operator console]. Whether 8,192 is enough for Gemini is unverified until a Gemini smoke
   row under the new cap ends cleanly; `per_response.csv` flags every answer that does not.
5. **Spelling variants are not merged by the analyzer** ("AbuQir" / "AbuQir Seafood", "Ruta Oaxaca" /
   "Ruta Oaxaca Mexican Cuisine", "Vesta Trattoria & Wine Bar" / "& Winebar" were all seen). They are
   merged only through `merges_v1.csv`, written by hand after the run and committed with the results.

## AMENDMENT v1.3 — 2026-10-06, written BEFORE the seal and before any full-run response
Evidence is now 6 smoke rows (NYC01 only; 5 clean, 1 error); no full-run row exists. Thresholds unchanged.

1. **The v1.2 extractor on the four complete smoke answers** [MEASURED: operator console, 2026-10-07
   ~02:10Z, candidate list read in full]: 63 distinct candidates. The ten junk names of v1.2 item 1 and
   "The Bomb" are gone. Two candidates are not a restaurant: "Sal" and "Kris & Charlie's Deli". Both come
   from one defect introduced by v1.2 item 2(d): a table cell was cut at every comma, which cut the real
   name "Sal, Kris & Charlie's Deli"; the fragment was then matched inside that real name in two other
   answers and reached 3 of 4 responses. A defect created by a fix, caught by re-running the check.
2. **Change:** v1.2 item 2(d) is withdrawn. A table cell is kept whole at discovery and cut afterwards
   by `best_split()`, which prefers parts the market's answers gave on their own; a name given whole in
   any ordinary list is one place and is never cut. 48 tests pass, one of them this exact case. On the
   realtor rows the top tier is unchanged from the v1.2 extractor (106 candidates, same names)
   [MEASURED: 2026-10-06]. This version has NOT yet been run on the complete smoke answers;
   `check_smoke_extract_v1.py` prints PASS or FAIL for the defects named in v1.2 and v1.3, and the
   operator runs it before sealing. That script is a convenience, not part of the instrument.
3. **Gemini under the 8,192 cap** [MEASURED: operator console, smoke 2026-10-07T02:10Z]: 4,954 characters,
   ends on a full stop. The cap was the cause of the earlier cut. Citations: 0 on both Gemini smoke rows,
   against 99 of 99 in the realtor run with the same runner and model. Per v1.1 item 1, Gemini rows
   without a citation are reported as answers with no search evidenced, and that share is printed.
4. **Count of post-hoc instrument changes before the seal: three** (v1.1 build, v1.2, v1.3), each made
   after reading smoke output. After the seal the analyzer does not change; a change is a v2.

## AMENDMENT v1.4 — 2026-10-06, written BEFORE the seal and before any full-run response
Evidence unchanged: 6 smoke rows, no full-run row. Thresholds unchanged.

1. **The v1.3 extractor on the four complete smoke answers** [MEASURED: operator console, 2026-10-07
   ~02:17Z, candidate list read in full]: 63 distinct candidates. "Sal" and "Kris & Charlie's Deli" are
   gone and the real name is whole. Two candidates are duplicates carrying a trailing bracket —
   "Dar Lbahja (Moroccan)" and "Sami's Kabab House (Afghan)" — beside "Dar Lbahja" and
   "Sami's Kabab House". Cause: parts cut from a table cell by `best_split()` skipped the tidy step every
   other name goes through. Second defect in a row created by the preceding fix.
2. **`check_smoke_extract_v1.py` printed CHECK PASS on that list.** It tested for the defects named so
   far and nothing else. The duplicates were found by reading the names, not by the script. The script now
   also fails on a trailing bracket, and its header says what PASS does not mean.
3. **Change:** cut parts are tidied like any other head. 49 tests pass, one of them this case; realtor
   top tier unchanged (106, same names) [MEASURED: 2026-10-06]. NOT yet re-run on the complete smoke
   answers.
4. **Known and left as is** [MEASURED: same list]: spelling and suffix variants are separate candidates —
   "AbuQir" / "AbuQir Seafood", "Ruta Oaxaca" / "Ruta Oaxaca Mexican Cuisine", "Vesta Trattoria & Wine Bar"
   / "& Winebar", "7th Street Burger Astoria", "Ibn Hamido Seafood NYC". They are folded only through
   `merges_v1.csv`. Until merged, a restaurant's count is split across its spellings and is a lower bound.
5. **Post-hoc instrument changes before the seal: four** (v1.1 build, v1.2, v1.3, v1.4).
