# AI VISIBILITY MEASUREMENT — pr_agency_v1

**RUNG: R1** — this ran on the operator's machine. It has not been run by a
stranger. Every figure below is computed from the evidence file named in the
instrument record; nothing here is illustrative and there are no placeholders.

Generated 2026-08-29T23:54:47Z by make_report v0.1.0

---

## 1 · WHAT WAS MEASURED

This measures what AI assistants **answer**, not what people **ask**. It carries
no information about search volume, query frequency, or purchase intent.

| | |
|---|---|
| Evidence file | `pr_agency_run4.jsonl` |
| Prompt bank | `pr_agency_v1`, 30 prompts |
| Families | buyer_intent, category, comparison, long_tail, problem |
| Engines | claude |
| Model versions | claude-sonnet-4-6 |
| Temperature | 0.0 |
| Runs per prompt | 5, 6, 7 |
| Rows attempted | 210 |
| Responses analysed | 191 |
| Rows lost to transport errors | 19 |
| Bundle digest (SHA-256) | `9eb756a2ca6ae2175bfe55a09d5b2c99b30e1451c2cd60050ddc0d1e2ee4abea` |

Responses per family, each rate below prints against its own count:

| family | responses |
|---|---|
| buyer_intent | 41 |
| category | 41 |
| comparison | 25 |
| long_tail | 42 |
| problem | 42 |

## 2 · WHAT THE MODEL EMPHASISED

No candidate list was supplied, so this section reports the entities the
model itself set apart in its answers (bold spans), with the number of
distinct prompts each appeared under. A name carried by one prompt is an
artifact of that prompt, not a pattern.

| emphasised | rate | 95% CI | prompts | families |
|---|---|---|---|---|
| Edelman | 17.8% (34/191) | 13.0–23.8% | 5 | 2 |
| Clarity PR | 11.5% (22/191) | 7.7–16.8% | 4 | 1 |
| Weber Shandwick | 11.0% (21/191) | 7.3–16.2% | 4 | 1 |
| Track record | 9.4% (18/191) | 6.0–14.4% | 5 | 3 |
| 5W Public Relations | 9.4% (18/191) | 6.0–14.4% | 4 | 1 |
| Media relationships | 8.4% (16/191) | 5.2–13.2% | 4 | 3 |
| Ketchum | 7.3% (14/191) | 4.4–11.9% | 3 | 2 |
| Reputation Ink | 7.3% (14/191) | 4.4–11.9% | 3 | 3 |
| Forbes Councils | 6.3% (12/191) | 3.6–10.7% | 2 | 2 |
| Reputation Rhino | 5.8% (11/191) | 3.2–10.0% | 3 | 2 |
| Prosek Partners | 5.8% (11/191) | 3.2–10.0% | 4 | 1 |
| what to look for | 5.8% (11/191) | 3.2–10.0% | 2 | 2 |
| Forbes Agency Council | 5.8% (11/191) | 3.2–10.0% | 2 | 1 |
| Derris | 5.8% (11/191) | 3.2–10.0% | 2 | 2 |
| HARO (Help a Reporter Out) | 5.8% (11/191) | 3.2–10.0% | 6 | 3 |
| Brandstyle Communications | 5.2% (10/191) | 2.9–9.4% | 3 | 2 |
| Clutch.co | 5.2% (10/191) | 2.9–9.4% | 2 | 2 |
| case studies | 5.2% (10/191) | 2.9–9.4% | 5 | 4 |
| Karbo Communications | 4.2% (8/191) | 2.1–8.0% | 3 | 2 |
| Reputation.com | 4.2% (8/191) | 2.1–8.0% | 2 | 1 |
| Highwire PR | 4.2% (8/191) | 2.1–8.0% | 2 | 1 |
| Realistic promises | 4.2% (8/191) | 2.1–8.0% | 3 | 2 |
| Budget | 3.7% (7/191) | 1.8–7.4% | 3 | 1 |
| Burson | 3.7% (7/191) | 1.8–7.4% | 2 | 2 |
| Brand of a Leader | 3.7% (7/191) | 1.8–7.4% | 2 | 1 |

**This is a discovery pass, not a score.** The extraction rule is markdown
emphasis, which captures section headings and advice alongside entities.
Read the rows before using any of them.

## 3 · RUN-TO-RUN STABILITY AT FIXED TEMPERATURE

Byte-level: **191 distinct responses out of 191**. Identical prompts at the declared temperature did not return identical text.

Decision-level stability: NOT COMPUTED (no candidate list supplied).

## 4 · LIMITATIONS CARRIED

L1. **Engine coverage.** 1 engine(s) measured: claude. Any figure here describes those engines only.

L2. **Extraction error is unmeasured.** Names are matched by a text rule with no published agreement coefficient. Every count in this report depends on that unvalidated step.

L3. **19 of 210 rows were lost to transport errors** and are excluded from every denominator. Losses were not evenly distributed across families; the per-family counts in section 1 are the true bases.

L4. **Single date.** All responses were collected in one session. Model behaviour changes between versions and over time; this is a snapshot.

L5. **No causal claim.** This is a cross-sectional measurement. It cannot show that any action moves these figures, and no published evidence establishes that these figures predict enquiries or revenue.

L6. **Prompt bank is a declared stimulus set**, not a sample of real user queries. It is not evidence about what anyone actually asked.

## 5 · HOW TO CHECK THIS

The evidence file ships with this report. Every response is stored with the
exact request payload that produced it and a SHA-256 of its own text.

```
python3 verify_evidence.py pr_agency_run4.jsonl --expect 9eb756a2ca6ae2175bfe55a09d5b2c99b30e1451c2cd60050ddc0d1e2ee4abea
```

The checker is stdlib-only Python and needs nothing of ours installed.
At generation time, 191 of 191 stored hashes recomputed correctly from their own
response text.

A passing check shows the file has not been altered since it was written. It
does not show that collection was honest. For that, ask for the pre-run
credential probe receipt and the console record of the run.
