from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich import print as rprint

from .models import VisibilityObj
from .parser import norm_name, parse_tool_list
from .reporter import write_simple_pdf
from .runner import run_once, run_once_stub
from .scorer import compute_scores
from .storage import read_jsonl, write_jsonl
from .variance import summarize_anchor

app = typer.Typer(no_args_is_help=True)


def _load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _anchor_key(
    client_id: str, prompt_id: str, provider: str, model: str, temp: float, pv: str
) -> str:
    return f"{client_id}:{prompt_id}:{provider}:{model}:{temp}:{pv}"


@app.command()
def run(
    client_id: str = "demo",
    client_brand: str = "Asana",
    category: str = "Project Management Software",
    prompt_id: str = "PM-D01",
    prompt_version: str = "v1.0",
    model_provider: str = "anthropic",
    model_name: str = "claude-sonnet-5",
    temperature: float = 0.0,
    max_tokens: int = 2048,
    run_index: int = 1,
    live: bool = False,
    out: Path = Path("data/audits/visibility_runs.jsonl"),
):
    """Execute a single prompt run and store the result. Use --live for real API."""
    prompts = _load_json(Path("config/prompts_v1.json"))
    p = next((x for x in prompts if x["id"] == prompt_id), None)
    if not p:
        raise typer.BadParameter(f"Unknown prompt_id: {prompt_id}")

    prompt_text = p["text"]
    expected_list_min = int(p["expected_list_min"])
    prompt_family = p["family"]

    # Execute — stub or live
    if live:
        rr = run_once(prompt_text, model=model_name, temperature=temperature, max_tokens=max_tokens)
    else:
        rr = run_once_stub(prompt_text)
    raw = rr.raw_text

    # Parse
    tool_list, meta = parse_tool_list(raw)

    # Brand match
    brand_norm = norm_name(client_brand)
    brand_rank = None
    brand_cited = False
    brand_domains: list[str] = []
    for t in tool_list:
        if t.name_norm == brand_norm:
            brand_rank = t.rank
            brand_domains = t.citation_domains
            brand_cited = len(brand_domains) > 0
            break
    brand_mentioned = brand_rank is not None

    # Score
    scoring_cfg = _load_json(Path("config/scoring_v1.json"))
    scores = compute_scores(
        brand_mentioned=brand_mentioned,
        brand_rank=brand_rank,
        brand_cited=brand_cited,
        rank_map=scoring_cfg["rank_map"],
    )
    mention_score = scores.mention
    rank_score = scores.rank
    citation_score = scores.citation

    # Build object
    vo = VisibilityObj(
        visibility_id=str(uuid.uuid4()),
        client_id=client_id,
        client_brand_name=client_brand,
        category=category,
        prompt_id=prompt_id,
        prompt_text=prompt_text,
        prompt_version=prompt_version,
        prompt_family=prompt_family,
        expected_list_min=expected_list_min,
        model_provider=model_provider,
        model_name=model_name,
        model_version_hint=getattr(rr, 'model_version_hint', None),
        temperature=temperature,
        max_tokens=max_tokens,
        run_index=run_index,
        executed_at_utc=datetime.now(timezone.utc),
        request_payload=rr.request_payload,
        raw_response_text=raw,
        raw_response_json=rr.raw_json,
        response_hash=_sha256(raw),
        tool_list=tool_list,
        brand_mentioned=brand_mentioned,
        brand_rank=brand_rank,
        brand_cited=brand_cited,
        brand_citation_domains=brand_domains,
        parse_success=bool(meta["parse_success"]),
        parse_errors=meta["parse_errors"],
        list_length=len(tool_list),
        has_duplicates=bool(meta.get("has_duplicates", False)),
        output_contract_violations=meta["violations"],
        parse_mode=meta["parse_mode"],
        mention_score=mention_score,
        rank_score=rank_score,
        citation_score=citation_score,
        stability_anchor_key=_anchor_key(
            client_id, prompt_id, model_provider, model_name, temperature, prompt_version
        ),
        high_variance_flag=False,
        low_confidence_cap=1.0,
        cap_reasons=[],
    )

    write_jsonl(out, [vo])
    rprint(
        f"[green]OK[/green] {prompt_id} run={run_index} "
        f"brand={'YES' if brand_mentioned else 'NO'} "
        f"rank={brand_rank} parse={vo.parse_success} "
        f"tools={vo.list_length}"
    )


@app.command()
def smoke(
    prompt_id: str = "PM-D01",
    runs: int = 5,
    client_id: str = "demo",
    client_brand: str = "Asana",
    live: bool = False,
    out: Path = Path("data/audits/smoke_runs.jsonl"),
    aggregate_out: Path = Path("data/aggregates/smoke_aggregate.json"),
    pdf_out: Path = Path("data/reports/smoke_report.pdf"),
):
    """Run a single prompt N times, compute variance, generate PDF. Use --live for real API."""
    # Clear previous smoke data
    if out.exists():
        out.unlink()

    rprint(f"[cyan]Running {prompt_id} × {runs} ({'LIVE' if live else 'STUB'})...[/cyan]")
    for i in range(1, runs + 1):
        run(
            client_id=client_id,
            client_brand=client_brand,
            prompt_id=prompt_id,
            run_index=i,
            live=live,
            out=out,
        )

    # Load and compute variance
    rows = read_jsonl(out)
    if not rows:
        raise RuntimeError("No rows produced")

    objs = [VisibilityObj.model_validate(r) for r in rows]
    scoring_cfg = _load_json(Path("config/scoring_v1.json"))
    summ = summarize_anchor(objs, scoring_cfg)

    # Write aggregate
    aggregate_out.parent.mkdir(parents=True, exist_ok=True)
    aggregate_out.write_text(json.dumps(summ, indent=2, default=str), encoding="utf-8")

    # Generate PDF
    lines = [
        f"Prompt: {prompt_id}",
        f"Brand: {client_brand}",
        f"Runs: {summ['run_count']}",
        "",
        "=== MENTION ===",
        f"  Mention rate: {summ['mention_rate']:.0%} (stable={summ['mention_stable']})",
        "",
        "=== RANK ===",
        f"  Rank values: {summ['rank_values']}",
        f"  Rank spread: {summ['rank_spread']} (stable={summ['rank_stable']})",
        "",
        "=== LIST STABILITY ===",
        f"  Mean Jaccard: {summ['list_stability_score']:.2f} (stable={summ['list_stable']})",
        "",
        "=== SCORING ===",
        f"  Raw score: {summ['raw_score']:.3f}",
        f"  Confidence cap: {summ['confidence_cap']:.2f}",
        f"  Capped score: {summ['capped_score']:.3f}",
        f"  High variance: {summ['high_variance']}",
        f"  Cap reasons: {', '.join(summ['cap_reasons']) or 'none'}",
    ]

    write_simple_pdf(pdf_out, "AI Visibility Smoke Report", lines)

    rprint(f"\n[bold]Results:[/bold]")
    for ln in lines:
        rprint(f"  {ln}")
    rprint(f"\n[magenta]Aggregate → {aggregate_out}[/magenta]")
    rprint(f"[magenta]PDF → {pdf_out}[/magenta]")
