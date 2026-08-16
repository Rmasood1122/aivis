═══════════════════════════════════════════════════════════════
PCOS VISIBILITY ENGINE — v1.0.2 SPECIFICATION
═══════════════════════════════════════════════════════════════
Date: 2026-02-22
Status: PRE-FREEZE
Reconciled from: v1.0.1 spec + implementation scaffold

CHANGELOG:
  v1.0   (2026-02-21): Initial specification.
  v1.0.1 (2026-02-21): 7 failure mode patches (FM1–FM7).
  v1.0.2 (2026-02-22): Reconciled with implementation scaffold.
    - Prompt texts revised (shorter base, suffix baked in)
    - Clusters renamed: R → B (buyer_intent)
    - Storage: SQLite dropped → JSONL (MVP-appropriate)
    - VISIBILITYOBJ: +4 fields (prompt_family, expected_list_min,
      parse_mode, cap_reasons) = 36 fields total
    - Confidence caps: +2 rules (parse_error_cap, list_min_cap)
    - Tech stack locked (Python 3.11, Poetry, Pydantic v2, httpx,
      Typer, Rich, ReportLab)
    - Runner stubbed for end-to-end pipeline validation before
      API wiring

═══════════════════════════════════════════════════════════════
1. TECH STACK (LOCKED)
═══════════════════════════════════════════════════════════════

Language:       Python 3.11 (>=3.11, <3.13)
Deps:           Poetry + lockfile
CLI:            Typer + Rich
HTTP:           httpx (timeouts, retries)
Validation:     Pydantic v2
Storage:        JSONL per run + aggregated JSON + CSV export
PDF:            ReportLab (pure Python, no system deps)
Env:            python-dotenv
Dev:            pytest, ruff

No database in v1. JSONL is grep-friendly, git-trackable,
and sufficient for <10 clients × 30 prompts × 5 runs.

═══════════════════════════════════════════════════════════════
2. PROMPT SET v1.0 — PROJECT MANAGEMENT SOFTWARE
═══════════════════════════════════════════════════════════════

30 prompts. 5 clusters × 6 each. Suffix baked into prompt text.

SUFFIX (embedded in every prompt):
  "Return a ranked list of up to 10 tools. For each: name,
  1-sentence why, and (if you're relying on any specific
  source) cite the domain. If unsure, say 'no citation'."

CLUSTER D — CATEGORY (direct "best X" queries)
  expected_list_min: 5

  PM-D01  Best project management software.
  PM-D02  Top project management tools.
  PM-D03  Most popular project management platforms.
  PM-D04  Best PM tools for startups.
  PM-D05  Leading project management software for teams.
  PM-D06  Top-rated project management solutions.

CLUSTER C — COMPARISON (head-to-head, alternatives)
  expected_list_min: 3

  PM-C01  Asana vs ClickUp.
  PM-C02  Linear vs Jira.
  PM-C03  Monday.com vs Trello.
  PM-C04  Best Asana alternatives.
  PM-C05  ClickUp vs Monday.com.
  PM-C06  Jira vs Linear for software teams.

CLUSTER P — PROBLEM (pain-point driven)
  expected_list_min: 5

  PM-P01  How to manage cross-functional projects.
  PM-P02  How to track sprint velocity in agile.
  PM-P03  Best tool for remote team collaboration.
  PM-P04  How to organize product roadmap.
  PM-P05  Tool for managing multiple client projects.
  PM-P06  How to improve team productivity with software.

CLUSTER B — BUYER INTENT (purchase-ready queries)
  expected_list_min: 5

  PM-B01  What PM tool should a 10-person team use?
  PM-B02  Affordable project management software for SaaS.
  PM-B03  Best free PM tool for small business.
  PM-B04  Which PM tool has the best Gantt charts?
  PM-B05  Easy-to-use PM software for non-tech teams.
  PM-B06  Scalable PM platform for growing companies.

CLUSTER L — LONG TAIL (niche, specific)
  expected_list_min: 5
  category_distortion_risk: true

  PM-L01  Which PM software is easiest to use?
  PM-L02  Most user-friendly project management tool?
  PM-L03  Best project management app for iPhone.
  PM-L04  Project management software with time tracking.
  PM-L05  Open source project management tools.
  PM-L06  PM tools that integrate with Slack and GitHub.

NOTE: All prompt texts above are shown WITHOUT the suffix
for readability. The suffix is appended to each in
config/prompts_v1.json.

═══════════════════════════════════════════════════════════════
3. VISIBILITYOBJ v1.0.2 — SCHEMA (36 fields)
═══════════════════════════════════════════════════════════════

CORE IDENTITY (16 fields):
  visibility_id          UUID v4
  client_id              string
  client_brand_name      string
  category               string
  prompt_id              string
  prompt_text            string (full, with suffix)
  prompt_version         string
  prompt_family          string (category|comparison|problem|
                                buyer_intent|long_tail)
  expected_list_min      integer
  model_provider         string (anthropic|openai|google)
  model_name             string
  model_version_hint     string|null
  temperature            float
  max_tokens             integer
  run_index              integer (1..5)
  executed_at_utc        ISO-8601 datetime

RAW ARTIFACT STORAGE (4 fields):
  request_payload        object (full API request body)
  raw_response_text      string
  raw_response_json      object|null
  response_hash          sha256(raw_response_text)

PARSED OUTCOME (8 fields):
  tool_list              array of ToolEntry:
    rank                 integer (1..10)
    name_raw             string (as extracted)
    name_norm            string (normalized)
    why                  string
    citation_domains     array of string
  brand_mentioned        boolean
  brand_rank             integer|null
  brand_cited            boolean
  brand_citation_domains array of string

QUALITY SIGNALS (6 fields):
  parse_success          boolean
  parse_errors           array of PE-xx codes
  list_length            integer
  has_duplicates         boolean
  output_contract_violations  array of OCV-xx codes
  parse_mode             string (list|json|unknown)

SCORING PRIMITIVES (4 fields):
  mention_score          float (0 or 1)
  rank_score             float (0.0..1.0)
  citation_score         float (0 or 1)
  stability_anchor_key   string

AUDIT FLAGS (4 fields):
  high_variance_flag     boolean
  low_confidence_cap     float (0.0..1.0)
  cap_reasons            array of string
  notes                  string|null

TOTAL: 36 fields (was 31 in v1.0, 32 in v1.0.1)
NULLABLE: model_version_hint, brand_rank,
          raw_response_json, notes

═══════════════════════════════════════════════════════════════
4. ENUMS CONTRACT v1.0
═══════════════════════════════════════════════════════════════

PARSE ERROR CODES:
  PE-01  MISSING_RANK
  PE-02  MISSING_NAME
  PE-03  MISSING_WHY
  PE-04  DUPLICATE_TOOL
  PE-05  LIST_TRUNCATED
  PE-06  UNPARSEABLE_FORMAT
  PE-07  RANK_GAP
  PE-08  NAME_AMBIGUOUS
  PE-09  CITATION_MALFORMED
  PE-10  ENCODING_ERROR

OUTPUT CONTRACT VIOLATIONS:
  OCV-01  NO_RANKED_LIST
  OCV-02  EXCEEDED_10
  OCV-03  MISSING_CITATIONS
  OCV-04  MISSING_WHY_ALL
  OCV-05  PARTIAL_COMPLIANCE
  OCV-06  REFUSAL
  OCV-07  OFF_TOPIC
  OCV-08  DISCLAIMER_ONLY
  OCV-09  BELOW_MIN_LIST
  OCV-10  MIXED_FORMAT

HARD FAIL (parse_success = FALSE):
  PE-06, OCV-01, OCV-06, OCV-07, OCV-08

SOFT FAIL (parse_success = TRUE, flagged):
  All others

═══════════════════════════════════════════════════════════════
5. SCORING v1.0.2
═══════════════════════════════════════════════════════════════

RANK SCORE: (11 - R) / 10  (linear decay, R=1→1.0, R=10→0.1)
WEIGHTS: mention 0.50, rank 0.40, citation 0.10

CONFIDENCE CAP RULES (applied in order, min wins):
  1. Mention unstable    → cap = mention_rate
  2. rank_spread > 2     → cap = min(cap, 0.70)
  3. list_stability < 0.7 → cap = min(cap, 0.60)
  4. list_stability < 0.5 → cap = min(cap, 0.50)
  5. Any parse error      → cap = min(cap, 0.60)
  6. list_length < min    → cap = min(cap, 0.70)

high_variance_flag = TRUE if cap < 1.0
cap_reasons = array of which rules fired

COMPOSITE: raw_score × low_confidence_cap = capped_score

═══════════════════════════════════════════════════════════════
6. STORAGE CONTRACT v1.0
═══════════════════════════════════════════════════════════════

data/
  audits/
    visibility_runs.jsonl     One VISIBILITYOBJ per line
  aggregates/
    {client}_{date}.json      Variance summaries per anchor
  reports/
    {client}_{date}.pdf       Client-facing report

JSONL FORMAT: each line is a complete VISIBILITYOBJ serialized
as JSON. No partial writes. Append-only during audit cycle.

AGGREGATE FORMAT: JSON object keyed by stability_anchor_key,
each value is a variance summary dict.

═══════════════════════════════════════════════════════════════
7. REPO STRUCTURE (LOCKED)
═══════════════════════════════════════════════════════════════

ai-visibility-audit/
├── pyproject.toml
├── README.md
├── .gitignore
├── .env                      (not committed)
├── config/
│   ├── prompts_v1.json       (30 prompts + metadata)
│   ├── scoring_v1.json       (weights, caps, rank map)
│   └── models.json           (provider config)
├── schemas/
│   └── visibilityobj_v1.json (optional JSON Schema)
├── src/aivis/
│   ├── __init__.py
│   ├── cli.py                (Typer commands)
│   ├── settings.py           (env loading)
│   ├── models.py             (Pydantic data models)
│   ├── runner.py             (API execution)
│   ├── parser.py             (tool list extraction)
│   ├── scorer.py             (mention/rank/citation)
│   ├── variance.py           (stability + caps)
│   ├── storage.py            (JSONL read/write)
│   └── reporter.py           (PDF generation)
├── tests/
│   ├── test_parser.py
│   └── test_variance.py
├── scripts/
│   └── run_smoke_test.sh
└── data/                     (gitignored)
    ├── audits/
    ├── aggregates/
    └── reports/

═══════════════════════════════════════════════════════════════
8. FREEZE STATUS
═══════════════════════════════════════════════════════════════

FROZEN:
  ✓ Tech stack
  ✓ Repo structure
  ✓ Prompt texts + suffix + IDs
  ✓ VISIBILITYOBJ schema (36 fields)
  ✓ Enums (PE-01..10, OCV-01..10)
  ✓ Storage format (JSONL)
  ✓ Rank score formula
  ✓ Name normalization pipeline
  ✓ Report sections (8)

NOT FROZEN (adjustable after pilots):
  ~ Score weights (0.50/0.40/0.10)
  ~ Confidence cap thresholds
  ~ Long-tail contribution weighting

═══════════════════════════════════════════════════════════════
9. NEXT ACTION: WIRE REAL API
═══════════════════════════════════════════════════════════════

Runner is stubbed. Entire pipeline (parse → score → variance
→ PDF) runs end-to-end on stub data. This validates:
  - Schema correctness
  - Parser reliability
  - Variance computation
  - Cap logic
  - Report generation

To go live: replace run_once_stub() in runner.py with real
httpx call to Anthropic API. Single function swap. No other
changes needed.

═══════════════════════════════════════════════════════════════
END OF v1.0.2 SPECIFICATION
═══════════════════════════════════════════════════════════════
