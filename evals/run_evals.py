#!/usr/bin/env python3
"""aivis release-gate adapter (eval-conductor consumer-2).

Measures the gated metrics from committed artifacts and the installed aivis
package — no engine API keys, fully offline, deterministic — and writes a
candidate/v2 score file for the vendored gate (evals/tools/promote.py):

  {"manifest": {"schema": "candidate/v2",
                "registry_hash": sha256(evals/registry.yaml),   # VERIFIED by the gate
                "dataset_hash":  sha256(sorted gated inputs)},  # attestation
   "scores": {<metric>: <measured number>, ...}}

Metrics (see evals/registry.yaml for thresholds):
  evidence_verify_pass_rate   pass-corpus files passing study2/verify_evidence.py
                              (exit 0, run WITH --expect <that file's stored digest>)
  negative_exhibit_integrity  must_fail exhibits (the D0 receipt) STILL failing
  tamper_detection_rate       5 live tamper classes on a pristine evidence file,
                              each must FAIL verification (--expect anchored)
  sealed_sample_integrity     study2/verify_kappa_sample.py exit 0
  abstention_integrity_rate   unparseable -> exact INSUFFICIENT_EVIDENCE token on
                              every score; parseable+absent -> 0.0, never abstained
  verify_latency_p95_s        p95 wall time of one verifier invocation (soft)

Honest run (CI):  python3 evals/run_evals.py
BLOCK fixtures:   python3 evals/run_evals.py --sabotage <mode> --out <path>

Sabotage modes exist ONLY to prove the gate fires (seen-it-fire doctrine).
Each simulates one real failure class and overwrites exactly one metric of an
otherwise-honest run:
  evidence   one pass-corpus file is a byte-flipped copy -> pass rate < 1.0
  exhibit    the D0 receipt slot holds a clean file -> integrity 0.0
             ("the failure receipt was replaced")
  tamper     verifier invoked WITHOUT the --expect anchor -> the consistent-edit
             /delete/reorder classes slip through -> detection < 1.0
             (this is the real bug --expect exists to prevent)
  sealed     sealed kappa sample with one sha corrupted -> integrity 0.0
  abstention the D6 defect re-created: parse failure scored as 0.0 instead of
             the abstention token -> rate < 1.0

All subprocess exit codes are read directly from run() results — no gating
signal ever crosses a pipe.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
VERIFIER = REPO / "study2/verify_evidence.py"
KAPPA_VERIFIER = REPO / "study2/verify_kappa_sample.py"
KAPPA_SAMPLE = REPO / "study2/kappa_sample_v1.json"
CORPUS = REPO / "evals/evidence_corpus.yaml"
ABSTENTION_FIXTURE = REPO / "evals/abstention_fixture.json"
PRISTINE_FOR_TAMPER = REPO / "study2/data/pr_agency_run4.jsonl"

TAMPER_CLASSES = ("flip_text_byte", "strip_row_hash", "consistent_edit",
                  "delete_row", "reorder_rows")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def run_verifier(evidence: Path, expect: str | None) -> int:
    cmd = [sys.executable, str(VERIFIER), str(evidence)]
    if expect:
        cmd += ["--expect", expect]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode


def stored_digest(evidence: Path) -> str:
    """Recompute the bundle digest exactly as the verifier defines it:
    sha256 over newline-joined STORED per-row hashes of clean rows, file order."""
    hashes = []
    for line in evidence.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("response_text") and row.get("sha256"):
            hashes.append(row["sha256"])
    return hashlib.sha256("\n".join(hashes).encode("utf-8")).hexdigest()


# --- metric: evidence corpus ------------------------------------------------

def evidence_rates(tampered_substitute: Path | None = None,
                   exhibit_substitute: Path | None = None) -> tuple[float, float]:
    corpus = yaml.safe_load(CORPUS.read_text())
    pass_map = {REPO / p: digest for p, digest in corpus["pass"].items()}
    fail_files = [REPO / p for p in corpus["must_fail"]]
    if not pass_map or not fail_files:
        raise SystemExit("FAIL: evidence corpus must list both pass and must_fail files")

    ok = 0
    for f, sealed in pass_map.items():
        target = tampered_substitute if (tampered_substitute and f == PRISTINE_FOR_TAMPER) else f
        # --expect pins the SEALED digest from the corpus manifest, so even a
        # self-consistent edit of the file trips the gate.
        if run_verifier(target, expect=sealed) == 0:
            ok += 1
    pass_rate = ok / len(pass_map)

    still_failing = 0
    for f in fail_files:
        target = exhibit_substitute or f
        if run_verifier(target, expect=None) == 1:
            still_failing += 1
    exhibit_rate = still_failing / len(fail_files)
    return pass_rate, exhibit_rate


# --- metric: tamper detection ------------------------------------------------

def make_tampered(src: Path, mode: str, dst: Path) -> None:
    lines = [json.loads(ln) for ln in src.read_text(encoding="utf-8").splitlines() if ln.strip()]
    clean_idx = [i for i, r in enumerate(lines) if r.get("response_text") and r.get("sha256")]
    i = clean_idx[len(clean_idx) // 2]
    if mode == "flip_text_byte":
        t = lines[i]["response_text"]
        lines[i]["response_text"] = t[:-1] + ("X" if t[-1] != "X" else "Y")
    elif mode == "strip_row_hash":
        del lines[i]["sha256"]
    elif mode == "consistent_edit":
        t = lines[i]["response_text"] + " [edited after collection]"
        lines[i]["response_text"] = t
        lines[i]["sha256"] = sha256_text(t)  # attacker keeps row self-consistent
    elif mode == "delete_row":
        del lines[i]
    elif mode == "reorder_rows":
        j = clean_idx[0]
        lines[i], lines[j] = lines[j], lines[i]
    else:
        raise ValueError(f"unknown tamper mode {mode}")
    dst.write_text("\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8")


def tamper_detection(anchored: bool) -> float:
    """Fraction of tamper classes the verifier catches. anchored=True passes
    the PRISTINE file's digest as --expect (the shipped-report anchor);
    anchored=False models the invocation bug where the anchor is dropped."""
    pristine_digest = stored_digest(PRISTINE_FOR_TAMPER)
    caught = 0
    with tempfile.TemporaryDirectory() as td:
        for mode in TAMPER_CLASSES:
            dst = Path(td) / f"tampered_{mode}.jsonl"
            make_tampered(PRISTINE_FOR_TAMPER, mode, dst)
            code = run_verifier(dst, expect=pristine_digest if anchored else None)
            if code == 1:
                caught += 1
    return caught / len(TAMPER_CLASSES)


# --- metric: sealed kappa sample ---------------------------------------------

def sealed_sample_integrity(corrupted: bool) -> float:
    if not corrupted:
        r = subprocess.run([sys.executable, str(KAPPA_VERIFIER)], capture_output=True, text=True)
        return 1.0 if r.returncode == 0 else 0.0
    # sabotage: same verifier, one sealed sha corrupted, in an isolated copy
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        shutil.copy2(KAPPA_VERIFIER, base / "verify_kappa_sample.py")
        sample = json.loads(KAPPA_SAMPLE.read_text(encoding="utf-8"))
        sample["cases"][0]["sha256"] = "0" * 64
        (base / "kappa_sample_v1.json").write_text(json.dumps(sample), encoding="utf-8")
        data = base / "data"
        data.mkdir()
        for c in sample["cases"]:
            srcf = REPO / "study2/data" / c["corpus"]
            dstf = data / c["corpus"]
            if not dstf.exists():
                shutil.copy2(srcf, dstf)
        r = subprocess.run([sys.executable, str(base / "verify_kappa_sample.py")],
                           capture_output=True, text=True)
        return 1.0 if r.returncode == 0 else 0.0


# --- metric: abstention contract ---------------------------------------------

def abstention_rate(d6_regression: bool) -> float:
    """d6_regression=True re-creates defect D6: parse failure scored as 0.0."""
    from aivis.parser import parse_tool_list
    from aivis.scorer import INSUFFICIENT_EVIDENCE, compute_scores, is_abstained

    fx = json.loads(ABSTENTION_FIXTURE.read_text(encoding="utf-8"))
    rank_map = {"1": 1.0, "2": 0.8, "3": 0.6, "default": 0.2}
    total, ok = 0, 0

    def score(parse_success: bool, mentioned: bool, rank):
        if d6_regression and not parse_success:
            class Broken:  # the D6 defect: PARSE_ERROR leaves numbers behind
                mention, rank, citation = 0.0, 0.0, 0.0
            return Broken()
        return compute_scores(mentioned, rank, False, rank_map, parse_success=parse_success)

    for raw in fx["unparseable"]:
        total += 1
        _tools, meta = parse_tool_list(raw)
        if meta["parse_success"]:
            continue  # fixture case misclassified — counts as a failure
        s = score(False, False, None)
        if all(isinstance(v, str) and v == INSUFFICIENT_EVIDENCE and is_abstained(v)
               for v in (s.mention, s.rank, s.citation)):
            ok += 1

    for raw in fx["parseable_brand_absent"]:
        total += 1
        _tools, meta = parse_tool_list(raw)
        if not meta["parse_success"]:
            continue
        s = score(True, False, None)
        if s.mention == 0.0 and not is_abstained(s.mention):
            ok += 1

    for raw in fx["parseable_brand_present_rank1"]:
        total += 1
        _tools, meta = parse_tool_list(raw)
        if not meta["parse_success"]:
            continue
        s = score(True, True, 1)
        if isinstance(s.mention, float) and s.mention > 0 and not is_abstained(s.mention):
            ok += 1

    if total == 0:
        raise SystemExit("FAIL: abstention fixture is empty — refusing a vacuous rate")
    return ok / total


# --- latency ------------------------------------------------------------------

def verify_latency_p95_s(samples: int = 5) -> float:
    durs = []
    for _ in range(samples):
        t0 = time.perf_counter()
        run_verifier(PRISTINE_FOR_TAMPER, expect=None)
        durs.append(time.perf_counter() - t0)
    durs.sort()
    rank = max(1, -(-95 * len(durs) // 100))  # ceil, nearest-rank
    return durs[rank - 1]


# --- manifest -----------------------------------------------------------------

def dataset_hash() -> str:
    """sha256 over the sorted gated inputs: corpus manifest, every corpus file,
    the kappa sample + verifier, the abstention fixture. path NUL bytes NUL."""
    corpus = yaml.safe_load(CORPUS.read_text())
    rels = sorted(set(corpus["pass"].keys()) | set(corpus["must_fail"]) | {
        "evals/evidence_corpus.yaml",
        "evals/abstention_fixture.json",
        "study2/kappa_sample_v1.json",
        "study2/verify_kappa_sample.py",
        "study2/verify_evidence.py",
    })
    h = hashlib.sha256()
    for rel in rels:
        p = REPO / rel
        h.update(rel.encode()); h.update(b"\0")
        h.update(p.read_bytes()); h.update(b"\0")
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(REPO / "evals/candidate.json"))
    ap.add_argument("--registry", default=str(REPO / "evals/registry.yaml"))
    ap.add_argument("--sabotage", default="",
                    choices=["", "evidence", "exhibit", "tamper", "sealed", "abstention"])
    a = ap.parse_args()

    # honest measurements
    pass_rate, exhibit_rate = evidence_rates()
    scores = {
        "evidence_verify_pass_rate": pass_rate,
        "negative_exhibit_integrity": exhibit_rate,
        "tamper_detection_rate": tamper_detection(anchored=True),
        "sealed_sample_integrity": sealed_sample_integrity(corrupted=False),
        "abstention_integrity_rate": abstention_rate(d6_regression=False),
        "verify_latency_p95_s": verify_latency_p95_s(),
    }

    if a.sabotage == "evidence":
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "tampered.jsonl"
            make_tampered(PRISTINE_FOR_TAMPER, "flip_text_byte", bad)
            pr, _ = evidence_rates(tampered_substitute=bad)
        scores["evidence_verify_pass_rate"] = pr
    elif a.sabotage == "exhibit":
        _, ex = evidence_rates(exhibit_substitute=PRISTINE_FOR_TAMPER)
        scores["negative_exhibit_integrity"] = ex
    elif a.sabotage == "tamper":
        scores["tamper_detection_rate"] = tamper_detection(anchored=False)
    elif a.sabotage == "sealed":
        scores["sealed_sample_integrity"] = sealed_sample_integrity(corrupted=True)
    elif a.sabotage == "abstention":
        scores["abstention_integrity_rate"] = abstention_rate(d6_regression=True)

    cand = {
        "manifest": {
            "schema": "candidate/v2",
            "registry_hash": sha256_file(Path(a.registry)),
            "dataset_hash": dataset_hash(),
        },
        "scores": scores,
    }
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cand, indent=2) + "\n", encoding="utf-8")

    mode = "honest" if not a.sabotage else f"SABOTAGE:{a.sabotage}"
    print(f"run_evals ({mode}): wrote {out}")
    for k in sorted(scores):
        print(f"  {k:28s} {scores[k]:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
