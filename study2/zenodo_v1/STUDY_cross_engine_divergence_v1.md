# Cross-Engine Divergence in AI Assistant Recommendations:
# 23 PR Firms, Four Engines, One Night

**Author:** Rehan Masood (independent) · **Collection date:** 2026-09-08 ·
**Deposit version:** v1 · **License:** CC BY 4.0

## Abstract
Thirty prompts a prospective client might put to an AI assistant about public
relations firms were run three times each against four engines (Claude, ChatGPT,
Gemini, Perplexity) on a single night, yielding 350 clean responses of 360
attempted. Presence of 23 candidate firms, declared before the run, was measured
by case-insensitive whole-name matching. The engines materially disagree on which
firms they name: pairwise overlap of each engine's five most-named firms ranges
from 1/5 to 4/5 (mean 2.5/5, response-level). One firm (Edelman) appears in every
engine's top five; no other firm does. Every raw response ships with this deposit,
with its request payload and SHA-256 hash, plus a stdlib-only checker, so all
figures are recomputable by the reader.

## Provenance and disclosure
Data were collected in the course of a commissioned category-baseline engagement;
the subject of that engagement is not a finding of this study. The author sells
measurement services; the author does not sell optimization, content, or placement
services for any firm measured here. Extractor accuracy (inter-rater kappa) is
UNMEASURED as of this deposit; a labelled agreement set is in preparation and will
be published. Until then, all presence figures are unvalidated pattern matches
against the declared 23-name list. A pre-deposit scan of all stored responses
found no personal data: two email addresses total, both public institutional
inboxes; zero personal phone numbers; zero credentials.

## Method
- BANK: pr_agency_v1 — 30 prompts, five families of six (buyer-intent, category,
  comparison, long-tail, problem). Family structure and counts are public; the
  instantiated prompt texts are withheld (a fully public bank is optimizable-
  against, undetectably). Three buyer-intent prompts are quoted verbatim as specimens of register in
  the engagement report, available on request.
- RUNS: 3 per prompt per engine; 360 attempted, 350 clean, 10 transport errors
  excluded from every rate. Errors were not evenly distributed across families;
  rates in the evidence print against per-family denominators.
- SURFACES (declared): Claude claude-sonnet-5 (temperature rejected by API,
  omitted and declared) · ChatGPT via OpenAI alias chat-latest (concrete snapshot
  not disclosed by the API at call time) · Gemini gemini-3.8-flash, temp 0.0
  (free tier: inputs/outputs may be used by Google to improve its models; the
  bank contains only generic prospect questions, no client data) · Perplexity
  sonar, temp 0.0. All are developer-API surfaces; consumer apps add search and
  memory. Copilot excluded (no public API); Grok excluded (<3% share, REPORTED
  2026-09-08).
- EXTRACTION: regex whole-name match, case-insensitive, against the 23 firms
  declared before the run. Deliberately biased toward finding: the ordinary
  phrase "credible pr" in a sentence counts as a hit for the firm of that name.
- EVIDENCE: per-response JSONL rows (request payload, response text, SHA-256);
  per-file bundle digest = SHA-256 over newline-joined row hashes in run order.
  verify_evidence.py (stdlib only) recomputes both; expected digests below.

## Findings [MEASURED: recomputed from the evidence files 2026-09-09]
1. CLEAN COUNTS: Claude 88/90 · ChatGPT 90/90 · Gemini 88/90 · Perplexity 84/90.
2. TOP-5 BY OVERALL PRESENCE (response-level):
   Claude: Bospar 17/88, Weber Shandwick 13/88, Edelman 13/88, Ketchum 9/88,
   FleishmanHillard 8/88.
   ChatGPT: Otter PR 19/90, 5WPR 19/90, FINN Partners 15/90, SourceCode 14/90,
   Edelman 12/90.
   Gemini: Edelman 24/88, Otter PR 18/88, 5WPR 16/88, LaunchSquad 14/88,
   Bospar 13/88.
   Perplexity: 5WPR 13/84, Edelman 10/84, Weber Shandwick 9/84, Otter PR 9/84,
   FINN Partners 8/84.
3. PAIRWISE TOP-5 OVERLAP: Claude-ChatGPT 1/5 · Claude-Gemini 2/5 ·
   Claude-Perplexity 2/5 · ChatGPT-Gemini 3/5 · ChatGPT-Perplexity 4/5 ·
   Gemini-Perplexity 3/5. Mean 2.5/5.
4. UNIQUE PRESENCE: Edelman is the only firm of 23 appearing in all four
   engines' top five. Seven firms are named at least once on all four engines,
   so mere four-engine presence is not rare; four-engine top-five presence is
   unique in this sample.
5. CONCENTRATION: Gemini's leader (Edelman, 24/88) exceeds its runner-up by 6
   responses; no other engine's first-to-second gap exceeds 4 (Claude 4,
   ChatGPT 0, Perplexity 3).
6. ZERO ROWS: 3 of 23 declared candidates (Reputation Rhino, Credible PR,
   Brandstyle) were named zero times on every engine — including the subject of
   the commissioning engagement — demonstrating that zeros are findable under
   this instrument and that the candidate list was not built to flatter its
   subject.

## Limitations (read first; they bound every figure above)
- Extractor unvalidated: no kappa published yet; figures are pattern matches.
- Samples of 84-90 clean responses per engine: most cross-engine differences
  sit inside overlapping 95% Wilson intervals. Divergence is reported as
  observed, not established.
- One night, one bank, one collection: no trend claim, no stability claim.
- Developer-API surfaces only: consumer apps differ (search, memory).
- No demand or causal claim: this measures what models answer, not what people
  ask, and says nothing about what moves these rates.
- No cross-version validity: figures are pinned to the model versions above and
  are not comparable to measurements on other versions.

## Files in this deposit
- STUDY_cross_engine_divergence_v1.md (this document)
- multi_anthropic_run3_20260908.jsonl · multi_openai_run3_20260908.jsonl ·
  multi_gemini_run3_20260908.jsonl · multi_perplexity_run3_20260908.jsonl
- verify_evidence.py (stdlib checker)
Expected digests:
  anthropic 5ac8d9d86829da414c3a2baaf122bb504cda7c551a562161846e72ab92cf9bed
  openai    82660a1f5d5e9782ac1fe0e03e6642214af2ae98d136badc8da1bd1a012be696
  gemini    81fc2f91615cfe583592a4871129a2f8be05596854af5b15c9d9fbf69190707f
  perplexity 442259f4cf0fcdde35093602296ef3a556d0ee0943bf4f13bb57ecd263870615
Verification: python verify_evidence.py <file> --expect <digest> ; expected verdict line: VERDICT PASS. A hash proves the file was not altered after collection, not
that collection was honest; the method page and chain receipts at
github.com/Rmasood1122/aivis-method carry the protocol and its dated history.
