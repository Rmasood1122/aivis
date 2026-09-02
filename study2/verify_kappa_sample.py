"""B07 preflight: every sealed (corpus, line) must hash to its sealed sha256.
Run BEFORE any labelling session (operator or external labeller).
Stdlib only. Read-only. Exit 0 = 100/100 PASS, exit 1 = anything else.
Line-index convention is calibrated, not assumed: both 0- and 1-based are
tried across the full set; the winning convention is printed. If neither
reaches 100%, the sample does not match the corpora and labelling must not
proceed.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).parent
SAMPLE = HERE / "kappa_sample_v1.json"

def sha(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()

def main() -> int:
    cases = json.loads(SAMPLE.read_text(encoding="utf-8"))["cases"]
    corpora = {}
    for c in cases:
        p = HERE / "data" / c["corpus"]
        if c["corpus"] not in corpora:
            if not p.exists():
                print(f"FAIL: corpus not found: {p}"); return 1
            corpora[c["corpus"]] = p.read_text(encoding="utf-8").splitlines()
    results = {}
    for base in (0, 1):
        ok = 0
        for c in cases:
            lines = corpora[c["corpus"]]
            i = c["line"] - base
            if 0 <= i < len(lines):
                try:
                    row = json.loads(lines[i])
                    if sha(row.get("response_text", "")) == c["sha256"]:
                        ok += 1
                except json.JSONDecodeError:
                    pass
        results[base] = ok
    n = len(cases)
    best = max(results, key=results.get)
    print(f"cases={n}  match(0-based)={results[0]}  match(1-based)={results[1]}")
    if results[best] == n:
        print(f"PASS 100% under {best}-based indexing. Labelling may proceed.")
        return 0
    print(f"FAIL: best convention ({best}-based) matches {results[best]}/{n}. DO NOT LABEL.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
