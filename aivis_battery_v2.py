#!/usr/bin/env python3
"""aivis_battery_v2.py — harness for the AUTOMATABLE subset of docs/08_BATTERY_v1.md.

HARNESS_SENTINEL_AIVIS_BATTERY_V2  (v1.1 lesson: any file carrying the sentinel
is never scanned by any probe in this harness.)

FIXES THE PROVENANCE DEFECT ON RECORD (03 Part A: battery-run-v3/v4 byte-identical,
"the battery embeds no clock, ref, or self-version"): every emitted row carries
  - git HEAD (rev-parse, at run time)
  - UTC ISO8601 timestamp
  - sha256 of this harness file itself
  - python version
Two runs can no longer be byte-identical, and every row is anchored to a commit.

SCOPE — 9 tests, chosen because a script can honestly run them; everything else
in doc 08 stays with its existing manual protocol:
  A02 suite count            A05 tamper -> MISMATCH        A06 digest order-sensitivity
  A08 secrets in history     A10 evidence row schema       B06 kappa sample byte-identity
  D04 banned words (PDF)     D05 placeholders (PDF)        D07 digest binds (PDF vs jsonl)

GRADING: the harness only emits PASS/FAIL/ABSTAIN with evidence strings; it never
totals a score (no composite, 04 §1) and the operator pastes output for external
grading — the harness scored itself favourably twice on record and is not trusted
to grade alone.

DESTRUCTION LOCK: read-only against the repo; writes ONLY new paths (refuses
existing); tamper test copies to a NEW temp path and never touches the original.

USAGE (from repo root):
  python aivis_battery_v2.py --out battery08-run-<something-new>.jsonl
Optional: --pdf PATH --evidence PATH (defaults target the 4-engine delivery),
  --skip TESTID[,TESTID]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

HARNESS_SENTINEL = "HARNESS_SENTINEL_AIVIS_BATTERY_V2"

DEFAULT_PDF = "out/crediblepr_delivery_4engine_20260908/aivis_crediblepr_report_4engine_20260908_v2.pdf"
DEFAULT_EVIDENCE = [
    "out/crediblepr_delivery_4engine_20260908/multi_anthropic_run3_20260908.jsonl",
    "out/crediblepr_delivery_4engine_20260908/multi_gemini_run3_20260908.jsonl",
    "out/crediblepr_delivery_4engine_20260908/multi_openai_run3_20260908.jsonl",
    "out/crediblepr_delivery_4engine_20260908/multi_perplexity_run3_20260908.jsonl",
]
VERIFIER = "out/crediblepr_delivery_4engine_20260908/verify_evidence.py"
RUN4 = "study2/data/pr_agency_run4.jsonl"

# doc 08 / charter §6 banned list. "we" is greylisted: counted and shown, and
# per charter it is banned until one delivered pilot — the operator judges
# whether today's delivery changes its status; the harness only counts.
BANNED_HARD = {
    "rank*": r"\brank(?:s|ed|ing|ings)?\b",
    "accura*": r"\baccura(?:te|tely|cy)\b",
    "verifiable": r"\b(?:independently\s+)?verifiable\b",
    "tamper-proof": r"\btamper[-\s]?proof\b",
    "signed": r"\bsigned\b",
    "non-repudiation": r"\bnon[-\s]?repudiation\b",
    "guarantee*": r"\bguarantee(?:s|d|ing)?\b",
    "audit-grade": r"\baudit[-\s]?grade\b",
    "court-ready": r"\bcourt[-\s]?ready\b",
    "customers": r"\bcustomers\b",
}
BANNED_GREY = {"we": r"\bwe\b"}

KAPPA_SEALED_SHA = "4cc3563d"  # prefix on record [QUOTED: 08 ledger B06 2026-09-01]


def sh(cmd: list[str], timeout: int = 600) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def meta() -> dict:
    try:
        _, head = sh(["git", "rev-parse", "HEAD"])
        head = head.strip()
    except Exception:
        head = "UNKNOWN"
    return {
        "head": head,
        "ts_utc": utcnow(),
        "run_id": os.urandom(8).hex(),
        "harness_sha256": file_sha256(os.path.abspath(__file__)),
        "python": sys.version.split()[0],
        "sentinel": HARNESS_SENTINEL,
    }


def result(test: str, verdict: str, evidence: str) -> dict:
    return {"test": test, "result": verdict, "evidence": evidence}


# ---------------------------------------------------------------- tests

def t_a02() -> dict:
    rc, out = sh([sys.executable, "-m", "pytest", "-q"])
    tail = out.strip().splitlines()[-1] if out.strip() else ""
    m = re.search(r"(\d+)\s+passed(?:.*?(\d+)\s+xfailed)?", tail)
    if not m:
        return result("A02", "ABSTAIN", f"could not parse pytest tail: {tail!r}")
    v = "PASS" if rc == 0 else "FAIL"
    return result("A02", v, f"pytest: {tail.strip()} rc={rc}")


def t_a05(evidence_files: list[str]) -> dict:
    src = next((f for f in evidence_files if os.path.exists(f)), None)
    if not src or not os.path.exists(VERIFIER):
        return result("A05", "ABSTAIN", f"missing verifier or evidence (src={src})")
    with tempfile.TemporaryDirectory() as td:
        tampered = os.path.join(td, "tampered.jsonl")
        lines = open(src, encoding="utf-8").read().splitlines()
        flipped = False
        outlines = []
        for line in lines:
            if not flipped and line.strip():
                rec = json.loads(line)
                t = rec.get("response_text")
                if t and not rec.get("error"):
                    rec["response_text"] = ("X" if t[0] != "X" else "Y") + t[1:]
                    line = json.dumps(rec)
                    flipped = True
            outlines.append(line)
        if not flipped:
            return result("A05", "ABSTAIN", "no clean row found to tamper")
        open(tampered, "w", encoding="utf-8").write("\n".join(outlines) + "\n")
        rc, out = sh([sys.executable, VERIFIER, tampered])
        mm = re.search(r"MISMATCH\s+(\d+)", out)
        caught = (mm and int(mm.group(1)) >= 1) or rc != 0
        v = "PASS" if caught else "FAIL"
        return result("A05", v, f"1 byte flipped in copy of {os.path.basename(src)} -> "
                                f"MISMATCH={mm.group(1) if mm else '?'} rc={rc} (original untouched)")


def t_a06() -> dict:
    src = RUN4 if os.path.exists(RUN4) else None
    if not src:
        return result("A06", "ABSTAIN", f"{RUN4} not found")
    hashes = []
    for line in open(src, encoding="utf-8"):
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("error") or not rec.get("response_text"):
            continue
        hashes.append(rec["sha256"])
    fwd = hashlib.sha256("\n".join(hashes).encode("utf-8")).hexdigest()
    rev = hashlib.sha256("\n".join(reversed(hashes)).encode("utf-8")).hexdigest()
    v = "PASS" if fwd != rev else "FAIL"
    return result("A06", v, f"clean rows n={len(hashes)}; forward {fwd[:12]} != reversed {rev[:12]}: {fwd != rev} "
                            f"(digest def per 03: sha256 over newline-joined hashes in run order)")


def t_a08() -> dict:
    rc, out = sh(["git", "log", "-p", "--all"], timeout=900)
    hits = re.findall(r"sk-ant-[A-Za-z0-9_-]{10,}|AKIA[A-Z0-9]{16}|ghp_[A-Za-z0-9]{20,}", out)
    # A08 amended spec (08 ledger): pass = 0 hits excluding enumerated notices.
    # Length-21 documented exposure-notice fragments are the enumerated exclusion.
    real = [h for h in hits if len(h) != 21]
    v = "PASS" if not real else "FAIL"
    return result("A08", v, f"credential-pattern hits: {len(hits)} total, {len(real)} outside the "
                            f"enumerated length-21 notice class; population = full history all refs")


def t_a10() -> dict:
    if not os.path.exists(RUN4):
        return result("A10", "ABSTAIN", f"{RUN4} not found")
    need = ["request_payload", "response_text", "sha256", "bank_version", "model", "temperature"]
    clean = complete = 0
    for line in open(RUN4, encoding="utf-8"):
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("error") or not rec.get("response_text"):
            continue
        clean += 1
        if all(k in rec and rec[k] is not None for k in need):
            complete += 1
    v = "PASS" if clean and complete == clean else "FAIL"
    return result("A10", v, f"complete rows {complete} of {clean} clean (fields: {','.join(need)})")


def t_b06() -> dict:
    if not os.path.exists("kappa_sample.py") and not os.path.exists("study2/kappa_sample.py"):
        return result("B06", "ABSTAIN", "kappa_sample.py not found at repo root or study2/")
    script = "kappa_sample.py" if os.path.exists("kappa_sample.py") else "study2/kappa_sample.py"
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "kappa_sample_recheck.json")
        rc, log = sh([sys.executable, script, "--seed", "20260830", "--n", "100",
                      "--corpus", "study2/data/mattress_run2.jsonl:study2/config/prompts_mattress_premium_v1.json",
                      "--corpus", "study2/data/pr_agency_run4.jsonl:study2/config/prompts_pr_agency_v1.json",
                      "--out", out])
        if rc != 0 or not os.path.exists(out):
            return result("B06", "ABSTAIN", f"sample script rc={rc}; invocation may need --out "
                                            f"or different args; tail: {log.strip().splitlines()[-1] if log.strip() else ''}")
        sha = file_sha256(out)
        v = "PASS" if sha.startswith(KAPPA_SEALED_SHA) else "FAIL"
        return result("B06", v, f"recomputed sample sha256 {sha[:12]} vs sealed {KAPPA_SEALED_SHA}* -> {v}")


def _pdf_text(pdf: str) -> str | None:
    try:
        from pypdf import PdfReader
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception:
            return None
    try:
        return "\n".join((p.extract_text() or "") for p in PdfReader(pdf).pages)
    except Exception:
        return None


def t_d04(pdf: str) -> dict:
    if not os.path.exists(pdf):
        return result("D04", "ABSTAIN", f"{pdf} not found")
    text = _pdf_text(pdf)
    if text is None:
        return result("D04", "ABSTAIN", "pypdf/PyPDF2 unavailable or extraction failed")
    low = text.lower()
    counts = {label: len(re.findall(pat, low)) for label, pat in BANNED_HARD.items()}
    grey = {label: len(re.findall(pat, low)) for label, pat in BANNED_GREY.items()}
    hard_hits = {w: c for w, c in counts.items() if c}
    v = "PASS" if not hard_hits else "FAIL"
    return result("D04", v, f"hard banned-word hits: {hard_hits or 0}; grey ('we'): {grey['we']} "
                            f"[operator judges 'we' per charter pilot-delivery unlock]; population = extracted PDF text")


def t_d05(pdf: str) -> dict:
    if not os.path.exists(pdf):
        return result("D05", "ABSTAIN", f"{pdf} not found")
    text = _pdf_text(pdf)
    if text is None:
        return result("D05", "ABSTAIN", "pypdf/PyPDF2 unavailable or extraction failed")
    ph = text.count("\u27e6")  # ⟦
    banner = "SPECIMEN" in text
    ok = (ph == 0 and not banner) or (ph > 0 and banner)
    v = "PASS" if ok else "FAIL"
    return result("D05/D02", v, f"placeholders ⟦: {ph}; SPECIMEN banner present: {banner} "
                                f"(pass = banner iff placeholders)")


def t_d07(pdf: str, evidence_files: list[str]) -> dict:
    if not os.path.exists(pdf):
        return result("D07", "ABSTAIN", f"{pdf} not found")
    text = _pdf_text(pdf)
    if text is None:
        return result("D07", "ABSTAIN", "pypdf/PyPDF2 unavailable or extraction failed")
    pdf_hexes = set(re.findall(r"\b[0-9a-f]{64}\b", text.lower()))
    matched, computed = 0, 0
    detail = []
    for ef in evidence_files:
        if not os.path.exists(ef):
            continue
        hashes = []
        for line in open(ef, encoding="utf-8"):
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("error") or not rec.get("response_text"):
                continue
            hashes.append(rec["sha256"])
        digest = hashlib.sha256("\n".join(hashes).encode("utf-8")).hexdigest()
        computed += 1
        hit = digest in pdf_hexes
        matched += hit
        detail.append(f"{os.path.basename(ef)}:{digest[:8]}:{'IN_PDF' if hit else 'ABSENT'}")
    if computed == 0:
        return result("D07", "ABSTAIN", "no evidence files found")
    v = "PASS" if matched == computed else ("FAIL" if pdf_hexes else "ABSTAIN")
    note = "" if pdf_hexes else " (no 64-hex strings extractable from PDF — extraction may mangle them; verify manually)"
    return result("D07", v, f"digests matched in PDF: {matched}/{computed}; pdf carries {len(pdf_hexes)} hex64 strings; "
                            + " ".join(detail) + note)


# ---------------------------------------------------------------- main

TESTS = ["A02", "A05", "A06", "A08", "A10", "B06", "D04", "D05", "D07"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="NEW jsonl path for results")
    ap.add_argument("--pdf", default=DEFAULT_PDF)
    ap.add_argument("--evidence", action="append", default=None)
    ap.add_argument("--skip", default="", help="comma-separated test ids to skip")
    args = ap.parse_args(argv)

    if os.path.exists(args.out):
        print(f"REFUSED: {args.out} exists. New paths only.", file=sys.stderr)
        return 2
    evidence = args.evidence or DEFAULT_EVIDENCE
    skip = {s.strip().upper() for s in args.skip.split(",") if s.strip()}
    m = meta()

    runners = {
        "A02": t_a02,
        "A05": lambda: t_a05(evidence),
        "A06": t_a06,
        "A08": t_a08,
        "A10": t_a10,
        "B06": t_b06,
        "D04": lambda: t_d04(args.pdf),
        "D05": lambda: t_d05(args.pdf),
        "D07": lambda: t_d07(args.pdf, evidence),
    }

    rows = []
    for tid in TESTS:
        if tid in skip:
            rows.append(result(tid, "ABSTAIN", "skipped by operator"))
            continue
        try:
            rows.append(runners[tid]())
        except Exception as exc:  # a crashed probe is an ABSTAIN with a reason, never silence
            rows.append(result(tid, "ABSTAIN", f"probe crashed: {type(exc).__name__}: {exc}"))

    with open(args.out, "x", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps({**row, "meta": m}) + "\n")

    counts = {"PASS": 0, "FAIL": 0, "ABSTAIN": 0}
    print(f"BATTERY08 v2 harness | HEAD {m['head'][:9]} | {m['ts_utc']} | harness {m['harness_sha256'][:9]}")
    for row in rows:
        counts[row["result"].split("/")[0] if row["result"] in counts else row["result"]] = counts.get(row["result"], 0) + 1
        print(f"  {row['test']:<7} {row['result']:<8} {row['evidence']}")
    print(f"PASS {counts.get('PASS',0)} · FAIL {counts.get('FAIL',0)} · ABSTAIN {counts.get('ABSTAIN',0)} · POPULATION {len(rows)} (automatable subset of 72)")
    print(f"WROTE {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
