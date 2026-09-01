# AI VISIBILITY MEASUREMENT — Tempur-Pedic

**RUNG: R1** — this ran on the operator's machine. It has not been run by a
stranger. Every figure below is computed from the evidence file named in the
instrument record; nothing here is illustrative and there are no placeholders.

Generated 2026-09-01T21:53:19Z by make_report v0.1.0

---

## 1 · WHAT WAS MEASURED

This measures what AI assistants **answer**, not what people **ask**. It carries
no information about search volume, query frequency, or purchase intent.

| | |
|---|---|
| Evidence file | `mattress_run2.jsonl` |
| Prompt bank | `mattress_premium_v1`, 30 prompts |
| Families | buyer_intent, category, comparison, long_tail, problem |
| Engines | claude |
| Model versions | claude-sonnet-4-6 |
| Temperature | 0.0 |
| Runs per prompt | 1, 4, 7 |
| Rows attempted | 210 |
| Responses analysed | 194 |
| Rows lost to transport errors | 16 |
| Bundle digest (SHA-256) | `781a341e31cf1906dd6ea799400af99f7dcd4617d40967e5a2e03c5c59cc31d8` |

Responses per family, each rate below prints against its own count:

| family | responses |
|---|---|
| buyer_intent | 42 |
| category | 26 |
| comparison | 42 |
| long_tail | 42 |
| problem | 42 |

## 2 · WHAT THE MODEL EMPHASISED

No candidate list was supplied, so this section reports the entities the
model itself set apart in its answers (bold spans), with the number of
distinct prompts each appeared under. A name carried by one prompt is an
artifact of that prompt, not a pattern.

| emphasised | rate | 95% CI | prompts | families |
|---|---|---|---|---|
| Purple | 65.5% (127/194) | 58.5–71.8% | 20 | 5 |
| Tempur-Pedic | 61.9% (120/194) | 54.9–68.4% | 22 | 5 |
| Saatva | 58.2% (113/194) | 51.2–65.0% | 21 | 5 |
| WinkBed | 28.9% (56/194) | 22.9–35.6% | 15 | 5 |
| Sleep Number | 27.8% (54/194) | 22.0–34.5% | 12 | 5 |
| Helix | 23.7% (46/194) | 18.3–30.2% | 10 | 5 |
| Stearns & Foster | 20.6% (40/194) | 15.5–26.9% | 9 | 4 |
| Nectar | 19.6% (38/194) | 14.6–25.7% | 9 | 5 |
| trial periods | 17.0% (33/194) | 12.4–22.9% | 13 | 4 |
| Casper | 16.5% (32/194) | 11.9–22.4% | 8 | 5 |
| Avocado | 14.9% (29/194) | 10.6–20.6% | 10 | 3 |
| Consumer Reports | 13.4% (26/194) | 9.3–18.9% | 5 | 3 |
| Sleep position | 12.9% (25/194) | 8.9–18.3% | 6 | 4 |
| Sleep Foundation | 12.4% (24/194) | 8.5–17.7% | 6 | 3 |
| Hastens | 11.9% (23/194) | 8.0–17.2% | 5 | 2 |
| Budget | 11.3% (22/194) | 7.6–16.6% | 7 | 3 |
| DreamCloud | 10.8% (21/194) | 7.2–16.0% | 9 | 5 |
| Saatva Classic | 10.8% (21/194) | 7.2–16.0% | 6 | 2 |
| Helix Midnight Luxe | 10.3% (20/194) | 6.8–15.4% | 6 | 3 |
| Warranty | 9.8% (19/194) | 6.4–14.8% | 4 | 3 |
| Firmness preference | 8.8% (17/194) | 5.5–13.6% | 4 | 2 |
| Motion isolation | 8.2% (16/194) | 5.1–13.0% | 5 | 5 |
| Pressure relief | 8.2% (16/194) | 5.1–13.0% | 5 | 3 |
| WinkBeds | 7.7% (15/194) | 4.7–12.4% | 4 | 2 |
| Price | 7.7% (15/194) | 4.7–12.4% | 4 | 3 |

**This is a discovery pass, not a score.** The extraction rule is markdown
emphasis, which captures section headings and advice alongside entities.
Read the rows before using any of them.

## 3 · RUN-TO-RUN STABILITY AT FIXED TEMPERATURE

Byte-level: **194 distinct responses out of 194**. Identical prompts at the declared temperature did not return identical text.

Decision-level stability: NOT COMPUTED (no candidate list supplied).

## 4 · LIMITATIONS CARRIED

L1. **Engine coverage.** 1 engine(s) measured: claude. Any figure here describes those engines only.

L2. **Extraction error is unmeasured.** Names are matched by a text rule with no published agreement coefficient. Every count in this report depends on that unvalidated step.

L3. **16 of 210 rows were lost to transport errors** and are excluded from every denominator. Losses were not evenly distributed across families; the per-family counts in section 1 are the true bases.

L4. **Single date.** All responses were collected in one session. Model behaviour changes between versions and over time; this is a snapshot.

L5. **No causal claim.** This is a cross-sectional measurement. It cannot show that any action moves these figures, and no published evidence establishes that these figures predict enquiries or revenue.

L6. **Prompt bank is a declared stimulus set**, not a sample of real user queries. It is not evidence about what anyone actually asked.

## 5 · HOW TO CHECK THIS

The evidence file ships with this report. Every response is stored with the
exact request payload that produced it and a SHA-256 of its own text.

```
python3 verify_evidence.py mattress_run2.jsonl --expect 781a341e31cf1906dd6ea799400af99f7dcd4617d40967e5a2e03c5c59cc31d8
```

The checker is stdlib-only Python and needs nothing of ours installed.
At generation time, 194 of 194 stored hashes recomputed correctly from their own
response text.

A passing check shows the file has not been altered since it was written. It
does not show that collection was honest. For that, ask for the pre-run
credential probe receipt and the console record of the run.
