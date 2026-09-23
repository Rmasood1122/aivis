# PREREG — Realtor AI-Visibility Viability Test v1

Written BEFORE any run. Thresholds below may not be edited after the first response is collected.
Any change = new version (v2) with the reason stated.

## Question
When buyers/sellers ask AI assistants for a real estate agent in Queens or Long Island,
do the engines name individual agents consistently enough to sell an "AI Visibility Report" to solo agents?

## Design
- Prompts: `queens_li_prompts_v1.jsonl` (20 prompts: 10 Queens, 10 Long Island)
- Engines: ChatGPT, Claude, Gemini, Perplexity
- Reps: 5 per prompt per engine → 400 responses
- Capture per response: engine, model string, prompt_id, rep, timestamp, response_text, citations (URLs), sha256
- Record for each engine whether web search/grounding was ON. Consumer apps search the web for local
  questions; an API call without search answers from training data only. The two are different measurements.

## Unit definitions
- **Named person**: a human name presented as a real estate agent. Candidates are extracted automatically,
  then EVERY candidate is human-verified against the NY DOS license lookup (eAccessNY) before counting.
- **Unverified person**: named, but no matching NY license found → counted separately as a possible fabrication.
- **Named brokerage**: a firm name (Compass, Douglas Elliman, Coldwell Banker, etc.).
- **Directory deflection**: the answer sends the user to Zillow / Realtor.com / Redfin / StreetEasy /
  Yelp / Google / HomeLight etc. instead of naming anyone.

## Metrics
- M1: % of responses naming ≥1 VERIFIED individual agent (overall and per engine)
- M2: consistency — # of verified agents named in ≥3 of 5 reps for the same prompt+engine
- M3: cross-engine — # of verified agents named by ≥2 engines for the same area
- M4: % of responses that are pure directory deflection
- M5: % of named persons that are UNVERIFIED (fabrication rate)
- M6: top cited source domains (only engines that return citations)

## Decision rule (fixed now)
- **GO — solo-agent product:** M1 ≥ 30% AND M2 ≥ 10 agents across the whole run AND M5 ≤ 25%
- **PIVOT — brokerage product:** M1 < 30% but brokerages named in ≥ 50% of responses
- **KILL for realtors:** M1 < 10% AND brokerages named in < 50% of responses
- **Anything between:** INCONCLUSIVE → re-run with web search ON for all engines before deciding

## Predictions (write yours before the run)
- M1 overall: ____ %
- Engine naming the most agents: ____
- M5 fabrication rate: ____ %

## Publication rules
- Public (FB group): aggregate numbers only; agent names anonymized.
- Private: a named agent may receive their own results only.
- Never claim an agent is "ranked #1 by AI"; report what was observed, with counts and dates.
