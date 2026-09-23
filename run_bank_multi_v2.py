#!/usr/bin/env python3
"""run_bank_multi_v2.py - v1 plus (a) citation capture, (b) optional web search, (c) JSONL prompt input.

Contract unchanged from v1: verify_evidence.py must PASS on output (sha256 = SHA-256 of response_text).
Row schema is a SUPERSET of v1: adds  rep, web_search, citations, area, intent.

Search surfaces (all [UNVERIFIED] until a --smoke run confirms them; shapes from provider docs, 2026-09):
  openai      --search -> Responses API + web_search tool; citations from output_text annotations
  anthropic   --search -> Messages API + web_search_20250305 server tool; citations from text-block citations
  gemini      --search -> generateContent + google_search tool; citations from groundingMetadata
  perplexity  ALWAYS live retrieval; citations from `citations` / `search_results` (v1 dropped these)

Usage:
  python run_bank_multi_v2.py --engine perplexity --model sonar --bank realtor_v1/queens_li_prompts_v1.jsonl \
      --runs 5 --out realtor_v1/runs/multi_perplexity_realtor_v1_YYYYMMDD.jsonl
  add --search for openai/anthropic/gemini live-web runs; add --smoke for 1 prompt x 1 run.
"""
import argparse, hashlib, json, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path


def env():
    return dict(l.strip().split("=", 1) for l in open(".env") if "=" in l and not l.startswith("#"))


def now():
    return datetime.now(timezone.utc).isoformat()


def http(url, headers, body, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={**headers, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _err(ex):
    return "HTTP %s %s" % (ex.code, ex.read().decode()[:400])


# ---------------------------------------------------------------- engines
# Each call returns (text, request_id, resolved_model, payload_sent, citations[list of {url,title}])

def call_openai(e, model, prompt, temp, maxtok, search):
    if not search:
        pay = {"model": model, "max_completion_tokens": maxtok,
               "messages": [{"role": "user", "content": prompt}]}
        if temp is not None: pay["temperature"] = temp
        try:
            d = http("https://api.openai.com/v1/chat/completions",
                     {"Authorization": "Bearer " + e["OPENAI_API_KEY"]}, pay)
        except urllib.error.HTTPError as ex:
            msg = ex.read().decode()[:400]
            if temp is not None and "temperature" in msg:
                return call_openai(e, model, prompt, None, maxtok, search)
            raise RuntimeError("HTTP %s %s" % (ex.code, msg))
        return d["choices"][0]["message"]["content"], d.get("id", ""), d.get("model", model), pay, []

    # Responses API with web search tool
    pay = {"model": model, "input": prompt, "max_output_tokens": maxtok,
           "tools": [{"type": "web_search"}]}
    if temp is not None: pay["temperature"] = temp
    try:
        d = http("https://api.openai.com/v1/responses",
                 {"Authorization": "Bearer " + e["OPENAI_API_KEY"]}, pay)
    except urllib.error.HTTPError as ex:
        msg = ex.read().decode()[:400]
        if temp is not None and "temperature" in msg:
            return call_openai(e, model, prompt, None, maxtok, search)
        if "web_search" in msg and pay["tools"][0]["type"] == "web_search":
            pay["tools"] = [{"type": "web_search_preview"}]   # older tool name
            try:
                d = http("https://api.openai.com/v1/responses",
                         {"Authorization": "Bearer " + e["OPENAI_API_KEY"]}, pay)
            except urllib.error.HTTPError as ex2:
                raise RuntimeError(_err(ex2))
        else:
            raise RuntimeError("HTTP %s %s" % (ex.code, msg))
    txt, cites = _extract_responses_shape(d)
    if not txt:
        raise RuntimeError("empty output_text: " + json.dumps(d)[:300])
    return txt, d.get("id", ""), d.get("model", model), pay, cites


def call_anthropic(e, model, prompt, temp, maxtok, search):
    pay = {"model": model, "max_tokens": maxtok, "messages": [{"role": "user", "content": prompt}]}
    if temp is not None: pay["temperature"] = temp
    if search:
        pay["tools"] = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]
    try:
        d = http("https://api.anthropic.com/v1/messages",
                 {"x-api-key": e["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"}, pay)
    except urllib.error.HTTPError as ex:
        msg = ex.read().decode()[:400]
        if temp is not None and "temperature" in msg:
            return call_anthropic(e, model, prompt, None, maxtok, search)
        raise RuntimeError("HTTP %s %s" % (ex.code, msg))
    txt, cites, seen = "", [], set()
    for b in d.get("content", []):
        if b.get("type") != "text":
            continue
        txt += b.get("text", "")
        for c in b.get("citations", []) or []:
            u = c.get("url", "")
            if u and u not in seen:
                seen.add(u); cites.append({"url": u, "title": c.get("title", "")})
    if not txt:
        raise RuntimeError("empty text, stop_reason=%s" % d.get("stop_reason"))
    return txt, d.get("id", ""), d.get("model", model), pay, cites


def call_gemini(e, model, prompt, temp, maxtok, search):
    gen = {"maxOutputTokens": maxtok}
    if temp is not None: gen["temperature"] = temp
    pay = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": gen}
    if search:
        pay["tools"] = [{"google_search": {}}]
    m = model if model.startswith("models/") else "models/" + model
    try:
        d = http("https://generativelanguage.googleapis.com/v1beta/%s:generateContent" % m,
                 {"x-goog-api-key": e["GEMINI_API_KEY"]}, pay)
    except urllib.error.HTTPError as ex:
        raise RuntimeError(_err(ex))
    cands = d.get("candidates", [])
    if not cands: raise RuntimeError("no candidates: " + json.dumps(d)[:300])
    txt = "".join(p.get("text", "") for p in cands[0].get("content", {}).get("parts", []))
    if not txt: raise RuntimeError("empty text, finishReason=%s" % cands[0].get("finishReason"))
    cites = []
    for ch in (cands[0].get("groundingMetadata", {}) or {}).get("groundingChunks", []) or []:
        w = ch.get("web") or {}
        if w.get("uri"):
            cites.append({"url": w["uri"], "title": w.get("title", "")})
    return txt, d.get("responseId", ""), d.get("modelVersion", model), pay, cites


def _extract_responses_shape(d):
    """OpenAI-Responses-style output -> (text, [{url,title}]). Tolerant of missing pieces."""
    txt, cites, seen = "", [], set()
    for item in d.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for c in item.get("content", []) or []:
            if c.get("type") == "output_text":
                txt += c.get("text", "")
                for a in c.get("annotations", []) or []:
                    u = a.get("url", "")
                    if a.get("type") == "url_citation" and u and u not in seen:
                        seen.add(u); cites.append({"url": u, "title": a.get("title", "")})
    if not txt and d.get("output_text"):
        txt = d["output_text"]
    return txt, cites


def call_perplexity(e, model, prompt, temp, maxtok, search):
    key = e.get("PERPLEXITY_API_KEY") or e.get("PPLX_API_KEY")
    if not key: raise RuntimeError("no PERPLEXITY_API_KEY/PPLX_API_KEY in .env")
    hdr = {"Authorization": "Bearer " + key}
    # 2026-09: Sonar moved to the Agent API (/v1/responses). Shape [UNVERIFIED]; smoke prints raw keys.
    pay = {"model": model, "input": prompt, "max_output_tokens": maxtok}
    if search:
        pay["tools"] = [{"type": "web_search"}]   # [MEASURED 2026-09-23] without this the Agent API does NOT search
    if temp is not None: pay["temperature"] = temp
    try:
        d = http("https://api.perplexity.ai/v1/responses", hdr, pay)
    except urllib.error.HTTPError as ex:
        msg = ex.read().decode()[:400]
        if temp is not None and "temperature" in msg:
            return call_perplexity(e, model, prompt, None, maxtok, search)
        if "max_output_tokens" in msg:
            pay.pop("max_output_tokens", None)
            try:
                d = http("https://api.perplexity.ai/v1/responses", hdr, pay)
            except urllib.error.HTTPError as ex2:
                raise RuntimeError(_err(ex2))
        else:
            raise RuntimeError("HTTP %s %s" % (ex.code, msg))
    txt, cites = _extract_responses_shape(d)
    # Agent API returns sources as an output item of type "search_results" [MEASURED 2026-09-23]
    if not cites:
        seen = set()
        def walk(o):
            if isinstance(o, dict):
                u = o.get("url") or o.get("uri")
                if isinstance(u, str) and u.startswith("http") and u not in seen:
                    seen.add(u); cites.append({"url": u, "title": str(o.get("title") or o.get("name") or "")})
                for v in o.values(): walk(v)
            elif isinstance(o, list):
                for v in o: walk(v)
        for item in d.get("output", []) or []:
            if item.get("type") == "search_results":
                walk(item)
    # legacy fields, if the Agent API still returns them
    if not cites:
        for sr in d.get("search_results", []) or []:
            if sr.get("url"): cites.append({"url": sr["url"], "title": sr.get("title", "")})
    if not cites:
        cites = [{"url": u, "title": ""} for u in d.get("citations", []) or []]
    if not txt:
        raise RuntimeError("unrecognised Agent API shape; top-level keys=%s; body=%s" % (
            sorted(d.keys()), json.dumps(d)[:600]))
    return txt, d.get("id", ""), d.get("model", model), pay, cites


ENGINES = {
    "openai":     (call_openai,     0.0),
    "anthropic":  (call_anthropic,  None),   # claude-sonnet-5 rejects temperature [MEASURED 2026-09-02]
    "gemini":     (call_gemini,     0.0),
    "perplexity": (call_perplexity, 0.0),
}


# ---------------------------------------------------------------- prompts

def load_prompts(path):
    """Returns (bank_version, [(id, family, text, extra_dict)]). Accepts v1 bank .json or a .jsonl."""
    p = Path(path)
    if p.suffix == ".jsonl":
        rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        out = [(r["prompt_id"], r.get("region", "default"), r["text"],
                {"area": r.get("area"), "intent": r.get("intent")}) for r in rows]
        return p.stem, sorted(out, key=lambda t: t[0])
    b = json.loads(p.read_text(encoding="utf-8"))
    out = [(q["id"], fam, q["text"], {}) for fam, ps in b["families"].items() for q in ps]
    return b.get("bank_version", "unknown"), sorted(out, key=lambda t: t[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True, choices=list(ENGINES))
    ap.add_argument("--model", required=True)
    ap.add_argument("--bank", required=True, help="v1 bank .json OR prompts .jsonl")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--limit-prompts", type=int, default=0)
    ap.add_argument("--search", action="store_true", help="enable provider web search (openai/anthropic/gemini)")
    ap.add_argument("--smoke", action="store_true", help="1 prompt x 1 run, prints citations; for surface verification")
    a = ap.parse_args()
    if a.smoke:
        a.limit_prompts, a.runs = 1, 1
    outp = Path(a.out)
    if outp.exists(): sys.exit("REFUSE: %s exists. Versioned new paths only." % a.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    e = env(); fn, temp = ENGINES[a.engine]
    bv, prompts = load_prompts(a.bank)
    if a.limit_prompts: prompts = prompts[:a.limit_prompts]
    web = True if a.engine == "perplexity" else a.search
    plan = len(prompts) * a.runs
    print("ENGINE %s MODEL %s BANK %s PROMPTS %d RUNS %d PLAN %d TEMP %s SEARCH %s" % (
        a.engine, a.model, bv, len(prompts), a.runs, plan, temp, web))
    clean = errs = 0
    with outp.open("w", encoding="utf-8") as f:
        for run_i in range(a.runs):
            for pid, fam, text, extra in prompts:
                row = {"ts": now(), "engine": a.engine, "bank_version": bv, "prompt_id": pid,
                       "family": fam, "run_index": run_i, "rep": run_i + 1, "web_search": web, **extra}
                try:
                    txt, rid, resolved, pay, cites = fn(e, a.model, text, temp, a.max_tokens, web)
                    pay_rec = dict(pay); pay_rec["model"] = resolved
                    pay_rec.setdefault("temperature", "omitted(rejected-or-na)" if temp is None else temp)
                    pay_rec.setdefault("max_tokens", a.max_tokens)
                    row.update({"request_payload": pay_rec, "response_text": txt,
                                "sha256": hashlib.sha256(txt.encode()).hexdigest(),
                                "request_id": rid, "citations": cites})
                    clean += 1
                    print("  ok %3d/%d %s run%d (%d ch, %d cites)" % (
                        clean + errs, plan, pid, run_i, len(txt), len(cites)), flush=True)
                    if a.smoke:
                        print("  --- text ---\n" + txt[:1200] + "\n  --- citations ---")
                        for c in cites: print("   ", c["url"], "|", c["title"][:60])
                except Exception as ex:
                    row.update({"error": str(ex)[:500], "citations": [], "request_payload": {
                        "model": a.model, "temperature": temp, "max_tokens": a.max_tokens,
                        "web_search": web, "messages": [{"role": "user", "content": text}]}})
                    errs += 1
                    print("  ERR %s %s: %s" % (pid, a.engine, str(ex)[:160]), flush=True)
                f.write(json.dumps(row, ensure_ascii=False) + "\n"); f.flush()
                time.sleep(a.sleep)
    print("DONE clean=%d errs=%d -> %s" % (clean, errs, a.out))
    if errs: sys.exit(2)


if __name__ == "__main__":
    main()
