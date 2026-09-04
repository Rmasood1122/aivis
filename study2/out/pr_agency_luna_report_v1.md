# AI VISIBILITY MEASUREMENT — Credible PR

**RUNG: R1** — this ran on the operator's machine. It has not been run by a
stranger. Every figure below is computed from the evidence file named in the
instrument record; nothing here is illustrative and there are no placeholders.

Generated 2026-09-04T10:27:36Z by make_report v0.1.0

---

## 1 · WHAT WAS MEASURED

This measures what AI assistants **answer**, not what people **ask**. It carries
no information about search volume, query frequency, or purchase intent.

| | |
|---|---|
| Evidence file | `pr_agency_luna_run1_v1.jsonl` |
| Prompt bank | `pr_agency_v1`, 30 prompts |
| Families | buyer_intent, category, comparison, long_tail, problem |
| Engines | openai |
| Model versions | gpt-5.6-luna |
| Temperature | None |
| Runs per prompt | 2, 3 |
| Rows attempted | 89 |
| Responses analysed | 89 |
| Rows lost to transport errors | 0 |
| Bundle digest (SHA-256) | `0e0772d123cd2afcfbc5e4b512b0742d3b4b3bfd3ab9d2e206e9d858b5d5c141` |

Responses per family, each rate below prints against its own count:

| family | responses |
|---|---|
| buyer_intent | 18 |
| category | 18 |
| comparison | 17 |
| long_tail | 18 |
| problem | 18 |

## 2 · WHAT THE MODEL EMPHASISED

No candidate list was supplied, so this section reports the entities the
model itself set apart in its answers (bold spans), with the number of
distinct prompts each appeared under. A name carried by one prompt is an
artifact of that prompt, not a pattern.

| emphasised | rate | 95% CI | prompts | families |
|---|---|---|---|---|
| Bospar | 23.6% (21/89) | 16.0–33.4% | 9 | 3 |
| 5WPR | 21.3% (19/89) | 14.1–31.0% | 8 | 3 |
| Edelman | 18.0% (16/89) | 11.4–27.2% | 6 | 3 |
| Channel V Media | 16.9% (15/89) | 10.5–26.0% | 7 | 3 |
| SourceCode Communications | 14.6% (13/89) | 8.7–23.4% | 7 | 3 |
| Burson | 13.5% (12/89) | 7.9–22.1% | 6 | 3 |
| Otter PR | 13.5% (12/89) | 7.9–22.1% | 6 | 2 |
| Weber Shandwick | 12.4% (11/89) | 7.0–20.8% | 6 | 3 |
| FleishmanHillard | 12.4% (11/89) | 7.0–20.8% | 6 | 3 |
| FINN Partners | 11.2% (10/89) | 6.2–19.5% | 5 | 3 |
| Method Communications | 10.1% (9/89) | 5.4–18.1% | 6 | 2 |
| Ketchum | 10.1% (9/89) | 5.4–18.1% | 6 | 3 |
| Highwire | 7.9% (7/89) | 3.9–15.4% | 4 | 2 |
| Red Banyan | 7.9% (7/89) | 3.9–15.4% | 6 | 3 |
| Week 1 | 7.9% (7/89) | 3.9–15.4% | 3 | 1 |
| Week 3 | 7.9% (7/89) | 3.9–15.4% | 3 | 1 |
| Week 2 | 7.9% (7/89) | 3.9–15.4% | 3 | 1 |
| Week 4 | 7.9% (7/89) | 3.9–15.4% | 3 | 1 |
| The Lede Company | 6.7% (6/89) | 3.1–13.9% | 4 | 2 |
| LaunchSquad | 6.7% (6/89) | 3.1–13.9% | 3 | 1 |
| Bollare | 6.7% (6/89) | 3.1–13.9% | 2 | 2 |
| Credibility | 6.7% (6/89) | 3.1–13.9% | 3 | 2 |
| Subject | 6.7% (6/89) | 3.1–13.9% | 3 | 1 |
| SimplyBe. Agency | 5.6% (5/89) | 2.4–12.5% | 3 | 2 |
| Brand Builders Group | 5.6% (5/89) | 2.4–12.5% | 2 | 1 |

**This is a discovery pass, not a score.** The extraction rule is markdown
emphasis, which captures section headings and advice alongside entities.
Read the rows before using any of them.

## 3 · RUN-TO-RUN STABILITY AT FIXED TEMPERATURE

Byte-level: **89 distinct responses out of 89**. Identical prompts at the declared temperature did not return identical text.

Decision-level stability: NOT COMPUTED (no candidate list supplied).

## 4 · LIMITATIONS CARRIED

L1. **Engine coverage.** 1 engine(s) measured: openai. Any figure here describes those engines only.

L2. **Extraction error is unmeasured.** Names are matched by a text rule with no published agreement coefficient. Every count in this report depends on that unvalidated step.

L3. **Single date.** All responses were collected in one session. Model behaviour changes between versions and over time; this is a snapshot.

L4. **No causal claim.** This is a cross-sectional measurement. It cannot show that any action moves these figures, and no published evidence establishes that these figures predict enquiries or revenue.

L5. **Prompt bank is a declared stimulus set**, not a sample of real user queries. It is not evidence about what anyone actually asked.

## 5 · HOW TO CHECK THIS

The evidence file ships with this report. Every response is stored with the
exact request payload that produced it and a SHA-256 of its own text.

```
python3 verify_evidence.py pr_agency_luna_run1_v1.jsonl --expect 0e0772d123cd2afcfbc5e4b512b0742d3b4b3bfd3ab9d2e206e9d858b5d5c141
```

The checker is stdlib-only Python and needs nothing of ours installed.
At generation time, 89 of 89 stored hashes recomputed correctly from their own
response text.

A passing check shows the file has not been altered since it was written. It
does not show that collection was honest. For that, ask for the pre-run
credential probe receipt and the console record of the run.
