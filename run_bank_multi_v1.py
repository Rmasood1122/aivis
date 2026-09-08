#!/usr/bin/env python3
"""run_bank_multi_v1.py - one runner, four engines. Contract: verify_evidence.py must PASS on output."""
import argparse, hashlib, json, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

def env():
    return dict(l.strip().split("=", 1) for l in open(".env") if "=" in l and not l.startswith("#"))

def now(): return datetime.now(timezone.utc).isoformat()

def http(url, headers, body, timeout=90):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={**headers, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def call_openai(e, model, prompt, temp, maxtok):
    pay = {"model": model, "max_completion_tokens": maxtok, "messages": [{"role": "user", "content": prompt}]}
    if temp is not None: pay["temperature"] = temp
    try:
        d = http("https://api.openai.com/v1/chat/completions", {"Authorization": "Bearer " + e["OPENAI_API_KEY"]}, pay)
    except urllib.error.HTTPError as ex:
        msg = ex.read().decode()[:400]
        if temp is not None and "temperature" in msg:
            return call_openai(e, model, prompt, None, maxtok)
        raise RuntimeError("HTTP %s %s" % (ex.code, msg))
    return d["choices"][0]["message"]["content"], d.get("id", ""), d.get("model", model), pay

def call_anthropic(e, model, prompt, temp, maxtok):
    pay = {"model": model, "max_tokens": maxtok, "messages": [{"role": "user", "content": prompt}]}
    if temp is not None: pay["temperature"] = temp
    try:
        d = http("https://api.anthropic.com/v1/messages",
                 {"x-api-key": e["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"}, pay)
    except urllib.error.HTTPError as ex:
        msg = ex.read().decode()[:400]
        if temp is not None and "temperature" in msg:
            return call_anthropic(e, model, prompt, None, maxtok)
        raise RuntimeError("HTTP %s %s" % (ex.code, msg))
    txt = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
    return txt, d.get("id", ""), d.get("model", model), pay

def call_gemini(e, model, prompt, temp, maxtok):
    gen = {"maxOutputTokens": maxtok}
    if temp is not None: gen["temperature"] = temp
    pay = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": gen}
    m = model if model.startswith("models/") else "models/" + model
    try:
        d = http("https://generativelanguage.googleapis.com/v1beta/%s:generateContent" % m,
                 {"x-goog-api-key": e["GEMINI_API_KEY"]}, pay)
    except urllib.error.HTTPError as ex:
        raise RuntimeError("HTTP %s %s" % (ex.code, ex.read().decode()[:400]))
    cands = d.get("candidates", [])
    if not cands: raise RuntimeError("no candidates: " + json.dumps(d)[:300])
    txt = "".join(p.get("text", "") for p in cands[0].get("content", {}).get("parts", []))
    if not txt: raise RuntimeError("empty text, finishReason=%s" % cands[0].get("finishReason"))
    return txt, d.get("responseId", ""), d.get("modelVersion", model), pay

def call_perplexity(e, model, prompt, temp, maxtok):
    key = e.get("PERPLEXITY_API_KEY") or e.get("PPLX_API_KEY")
    if not key: raise RuntimeError("no PERPLEXITY_API_KEY/PPLX_API_KEY in .env")
    pay = {"model": model, "max_tokens": maxtok, "messages": [{"role": "user", "content": prompt}]}
    if temp is not None: pay["temperature"] = temp
    try:
        d = http("https://api.perplexity.ai/chat/completions", {"Authorization": "Bearer " + key}, pay)
    except urllib.error.HTTPError as ex:
        raise RuntimeError("HTTP %s %s" % (ex.code, ex.read().decode()[:400]))
    return d["choices"][0]["message"]["content"], d.get("id", ""), d.get("model", model), pay

ENGINES = {
    "openai":     (call_openai,     0.0),
    "anthropic":  (call_anthropic,  None),   # claude-sonnet-5 rejects temperature [MEASURED 2026-09-02]
    "gemini":     (call_gemini,     0.0),
    "perplexity": (call_perplexity, 0.0),
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True, choices=list(ENGINES))
    ap.add_argument("--model", required=True)
    ap.add_argument("--bank", required=True)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--limit-prompts", type=int, default=0)
    a = ap.parse_args()
    outp = Path(a.out)
    if outp.exists(): sys.exit("REFUSE: %s exists. Versioned new paths only." % a.out)
    e = env(); fn, temp = ENGINES[a.engine]
    b = json.loads(Path(a.bank).read_text(encoding="utf-8"))
    prompts = [(p["id"], fam, p["text"]) for fam, ps in b["families"].items() for p in ps]
    prompts.sort(key=lambda t: t[0])
    if a.limit_prompts: prompts = prompts[:a.limit_prompts]
    bv = b.get("bank_version", "unknown")
    plan = len(prompts) * a.runs
    print("ENGINE %s MODEL %s BANK %s PROMPTS %d RUNS %d PLAN %d TEMP %s" % (
        a.engine, a.model, bv, len(prompts), a.runs, plan, temp))
    clean = errs = 0
    with outp.open("w", encoding="utf-8") as f:
        for run_i in range(a.runs):
            for pid, fam, text in prompts:
                row = {"ts": now(), "engine": a.engine, "bank_version": bv,
                       "prompt_id": pid, "family": fam, "run_index": run_i}
                try:
                    txt, rid, resolved, pay = fn(e, a.model, text, temp, a.max_tokens)
                    pay_rec = dict(pay); pay_rec["model"] = resolved
                    pay_rec.setdefault("temperature", "omitted(rejected-or-na)" if temp is None else temp)
                    pay_rec.setdefault("max_tokens", a.max_tokens)
                    row.update({"request_payload": pay_rec, "response_text": txt,
                                "sha256": hashlib.sha256(txt.encode()).hexdigest(), "request_id": rid})
                    clean += 1
                    done = clean + errs
                    print("  ok %3d/%d %s run%d (%d ch)" % (done, plan, pid, run_i, len(txt)), flush=True)
                except Exception as ex:
                    row.update({"error": str(ex)[:500], "request_payload": {
                        "model": a.model, "temperature": temp, "max_tokens": a.max_tokens,
                        "messages": [{"role": "user", "content": text}]}})
                    errs += 1
                    print("  ERR %s %s: %s" % (pid, a.engine, str(ex)[:120]))
                f.write(json.dumps(row, ensure_ascii=False) + "\n"); f.flush()
                time.sleep(a.sleep)
    print("ATTEMPTED %d  CLEAN %d  ERRORED %d" % (plan, clean, errs))
    if clean == 0:
        print("VERDICT: FAILED RUN - zero clean rows. Nothing usable was produced."); return 1
    if clean + errs != plan:
        print("VERDICT: COUNT MISMATCH - rows do not reconcile."); return 1
    print("DONE (clean>=1, counts reconcile). Verify with verify_evidence.py before use.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
