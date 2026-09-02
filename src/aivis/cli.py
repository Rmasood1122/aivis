from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import typer
from rich import print as rprint

from .evidence import evidence_appendix_lines, write_evidence_jsonl
from .models import VisibilityObj
from .parser import norm_name, parse_tool_list
from .reporter import write_simple_pdf
from .runner import run_once, run_once_stub
from .scorer import INSUFFICIENT_EVIDENCE, compute_scores
from .storage import read_jsonl, write_jsonl
from .variance import summarize_anchor

app = typer.Typer(no_args_is_help=True)


def _load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _fmt(value, spec: str) -> str:
    """
    Format a score-like value for display.

    The abstention token passes through untouched. Without this, an f-string
    such as f"{summ['raw_score']:.3f}" raises on a string, and the tempting
    repair is a try/except that falls back to a number -- which is exactly the
    bare-except default that produced 0.540 in the first place.
    """
    if isinstance(value, str):
        return value
    if value is None:
        return "n/a"
    return format(value, spec)


def _anchor_key(
    client_id: str, prompt_id: str, provider: str, model: str, temp: float | None, pv: str
) -> str:
    temp_s = "na" if temp is None else str(temp)
    return f"{client_id}:{prompt_id}:{provider}:{model}:{temp_s}:{pv}"


@app.command()
def run(
    client_id: str = "demo",
    client_brand: str = "Asana",
    category: str = "Project Management Software",
    prompt_id: str = "PM-D01",
    prompt_version: str = "v1.0",
    model_provider: str = "anthropic",
    model_name: str = "claude-sonnet-5",
    temperature: float | None = None,  # temp-v1: API deprecated the param for claude-sonnet-5 (req_011Cedo5EDzMLp2paBDkgRXm); None -> omitted, provider default, declared per-row in request_payload
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

    # Execute -- stub or live
    if live:
        rr = run_once(prompt_text, model=model_name, temperature=temperature, max_tokens=max_tokens)
    else:
        rr = run_once_stub(prompt_text)

    raw = rr.raw_text

    # Parse
    tool_list, meta = parse_tool_list(raw)
    parse_ok = bool(meta["parse_success"])

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

    # Score. D6: an unparseable response abstains instead of scoring.
    scoring_cfg = _load_json(Path("config/scoring_v1.json"))
    if not isinstance(scoring_cfg, dict):
        raise TypeError("config/scoring_v1.json must be a JSON object, not a list")
    scores = compute_scores(
        brand_mentioned=brand_mentioned,
        brand_rank=brand_rank,
        brand_cited=brand_cited,
        rank_map=scoring_cfg["rank_map"],
        parse_success=parse_ok,
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
        model_version_hint=getattr(rr, "model_version_hint", None),
        temperature=temperature,
        max_tokens=max_tokens,
        run_index=run_index,
        executed_at_utc=datetime.now(UTC),
        request_payload=rr.request_payload,
        raw_response_text=raw,
        raw_response_json=rr.raw_json,
        response_hash=_sha256(raw),
        tool_list=tool_list,
        brand_mentioned=brand_mentioned,
        brand_rank=brand_rank,
        brand_cited=brand_cited,
        brand_citation_domains=brand_domains,
        parse_success=parse_ok,
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

    if parse_ok:
        rprint(
            f"[green]OK[/green] {prompt_id} run={run_index} "
            f"brand={'YES' if brand_mentioned else 'NO'} "
            f"rank={brand_rank} parse={vo.parse_success} "
            f"tools={vo.list_length}"
        )
    else:
        rprint(
            f"[yellow]ABSTAIN[/yellow] {prompt_id} run={run_index} "
            f"score={INSUFFICIENT_EVIDENCE} "
            f"parse_errors={','.join(meta['parse_errors']) or 'none'} "
            f"(row stored, evidence retained)"
        )


@app.command()
def smoke(
    prompt_id: str = "PM-D01",
    runs: int = 7,
    client_id: str = "demo",
    client_brand: str = "Asana",
    live: bool = False,
    out: Path = Path("data/audits/smoke_runs.jsonl"),
    aggregate_out: Path = Path("data/aggregates/smoke_aggregate.json"),
    pdf_out: Path = Path("data/reports/smoke_report.pdf"),
    evidence_out: Path = Path("data/reports/smoke_evidence.jsonl"),
    force_overwrite: bool = False,
):
    """Run a single prompt N times, compute variance, generate PDF. Use --live for real API."""
    # guards-v1: evidence files are never overwritten by default (B1/A04)
    if out.exists():
        if not force_overwrite:
            rprint(
                f"[red]REFUSED[/red] {out} exists. Evidence is never overwritten by "
                f"default. Pass --force-overwrite or a versioned --out path."
            )
            raise typer.Exit(code=1)
        out.unlink()  # explicit, operator-flagged

    rprint(f"[cyan]Running {prompt_id} x {runs} ({'LIVE' if live else 'STUB'})...[/cyan]")

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
    if not isinstance(scoring_cfg, dict):
        raise TypeError("config/scoring_v1.json must be a JSON object, not a list")
    summ = summarize_anchor(objs, scoring_cfg)

    # Write aggregate. This is written in both branches: an abstention is a
    # result and belongs on disk with the same provenance as a score.
    aggregate_out.parent.mkdir(parents=True, exist_ok=True)
    aggregate_out.write_text(json.dumps(summ, indent=2, default=str), encoding="utf-8")

    # D6: no parseable run means no measurement, which means no PDF. A report
    # is a claim; there is nothing here to claim.
    if summ.get("abstained"):
        rprint(f"\n[bold red]ABSTAINED[/bold red] score={INSUFFICIENT_EVIDENCE}")
        rprint(f"  reason: {summ.get('abstain_reason')}")
        rprint(
            f"  runs attempted: {summ['run_count']}  "
            f"scored: {summ['runs_scored']}  abstained: {summ['runs_abstained']}"
        )
        rprint(f"[magenta]Aggregate -> {aggregate_out}[/magenta]")
        rprint(
            f"[yellow]No PDF written to {pdf_out}. "
            f"There is no measurement to report.[/yellow]"
        )
        # B3: an abstention is a result; its evidence ships anyway.
        write_evidence_jsonl(evidence_out, objs)
        rprint(f"[magenta]Evidence -> {evidence_out}[/magenta]")
        raise typer.Exit(code=2)

    # Generate PDF
    lines = [
        f"Prompt: {prompt_id}",
        f"Brand: {client_brand}",
        f"Runs attempted: {summ['run_count']}",
        f"Runs scored: {summ['runs_scored']}",
        f"Runs abstained: {summ['runs_abstained']}",
        "",
        "=== MENTION ===",
        (
            f"  Mention rate: {_fmt(summ['mention_rate'], '.0%')} "
            f"[95% CI {summ['mention_rate_ci95'][0]:.1%}-{summ['mention_rate_ci95'][1]:.1%}, "
            f"n={summ['runs_scored']}] (stable={summ['mention_stable']})"
        ),
        "",
        "=== RANK ===",
        f"  Rank values: {summ['rank_values']}",
        f"  Rank spread: {summ['rank_spread']} (stable={summ['rank_stable']})",
        "",
        "=== LIST STABILITY ===",
        (
            f"  Mean Jaccard: {_fmt(summ['list_stability_score'], '.2f')} "
            f"(stable={summ['list_stable']})"
        ),
        "",
        "=== SCORING ===",
        f"  Raw score: {_fmt(summ['raw_score'], '.3f')}",
        f"  Confidence cap: {_fmt(summ['confidence_cap'], '.2f')}",
        f"  Capped score: {_fmt(summ['capped_score'], '.3f')}",
        f"  High variance: {summ['high_variance']}",
        f"  Cap reasons: {', '.join(summ['cap_reasons']) or 'none'}",
    ]

    # B3: the evidence trail rides inside the customer artifact.
    lines += evidence_appendix_lines(objs)

    write_evidence_jsonl(evidence_out, objs)
    write_simple_pdf(pdf_out, "AI Visibility Smoke Report", lines)

    rprint("\n[bold]Results:[/bold]")
    for ln in lines:
        rprint(f"  {ln}")

    rprint(f"\n[magenta]Aggregate -> {aggregate_out}[/magenta]")
    rprint(f"[magenta]Evidence -> {evidence_out}[/magenta]")
    rprint(f"[magenta]PDF -> {pdf_out}[/magenta]")
