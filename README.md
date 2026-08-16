# ai-visibility-audit

PCOS Visibility Engine MVP — CLI tool that runs a frozen prompt set against AI models,
captures raw responses + hashes, parses ranked tool lists, computes variance across
5 runs, applies confidence caps, and exports auditable reports.

## Quickstart

```bash
# 1. Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# 2. Install dependencies
poetry install

# 3. Create .env with your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 4. Run tests
poetry run pytest -q

# 5. Run smoke test (uses stub runner — no API key needed)
poetry run aivis smoke --prompt-id PM-D01 --runs 5
```

## Architecture

See `SPEC_v1.0.2.md` for the full specification.

Runner is stubbed until API wiring. The entire pipeline
(parse → score → variance → PDF) runs end-to-end on stub data.
