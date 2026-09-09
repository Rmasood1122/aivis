#!/usr/bin/env python3
"""verify_evidence.py — recipient-side verification of an aivis evidence file.

Stdlib only. Requires nothing from the vendor installed. Python 3.8+.

WHAT IT CHECKS
  1. Every clean row's stored sha256 equals SHA-256 of its own response_text.
  2. The bundle digest, recomputed as SHA-256 over the newline-joined per-run
     response hashes IN RUN ORDER.
     [QUOTED: src/aivis/evidence.py, commit 3e322a9 -- the definition this
      implements. If the emitter's definition ever changes, this file is wrong
      and the mismatch is the finding.]
  3. ROWS / CLEAN / ERRORED / DISTINCT, each printed with its denominator.

WHAT IT CANNOT CHECK
  Whether the responses are what the engine actually returned. A hash proves the
  file was not altered after collection. It does NOT prove collection was honest.
  That is a limit of the artifact, not of this checker, and it is printed on
  every run so a recipient cannot miss it.

USAGE
  python3 verify_evidence.py <evidence.jsonl> [--expect <digest>]
  exit 0 = all checks passed   exit 1 = a check failed   exit 2 = bad input
"""
import sys, json, hashlib, argparse, pathlib

TOOL_VERSION = "verify_evidence v0.1.0"


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def bundle_digest(row_hashes):
    """SHA-256 over the newline-joined per-run response hashes, in run order."""
    return hashlib.sha256("\n".join(row_hashes).encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("evidence")
    ap.add_argument("--expect", default=None,
                    help="bundle digest as printed in the report; compared if given")
    a = ap.parse_args()

    p = pathlib.Path(a.evidence)
    if not p.exists():
        print("FAIL: no such file: %s" % p); return 2

    rows, bad_json = [], 0
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            bad_json += 1

    clean = [r for r in rows if r.get("response_text")]
    errored = len(rows) - len(clean)

    print(TOOL_VERSION)
    print("FILE            %s" % p.name)
    print("ROWS            %d   (malformed lines skipped: %d)" % (len(rows), bad_json))
    print("CLEAN           %d of %d" % (len(clean), len(rows)))
    print("ERRORED         %d of %d" % (errored, len(rows)))

    if not clean:
        print("\nFAIL: zero clean rows. Nothing to verify.")
        print("      A run that produced no responses is not an audit, whatever")
        print("      the producing tool reported on its console.")
        return 1

    # --- check 1: per-row hash identity -----------------------------------
    ok, mismatch, missing = 0, [], 0
    for i, r in enumerate(clean):
        stored = r.get("sha256")
        if not stored:
            missing += 1
            continue
        if stored == sha256_text(r["response_text"]):
            ok += 1
        else:
            mismatch.append((i, r.get("prompt_id", "?"), r.get("run", "?")))

    print("\nCHECK 1 · per-row hash recomputed from response_text")
    print("  MATCH         %d of %d clean rows" % (ok, len(clean)))
    print("  MISMATCH      %d" % len(mismatch))
    print("  NO HASH       %d" % missing)
    for i, pid, run in mismatch[:10]:
        print("    row %d  prompt_id=%s run=%s" % (i, pid, run))
    if len(mismatch) > 10:
        print("    ... %d more" % (len(mismatch) - 10))

    distinct = len({r["response_text"] for r in clean})
    print("\n  DISTINCT response_text   %d of %d clean rows" % (distinct, len(clean)))
    if distinct == 1 and len(clean) > 1:
        print("  NOTE: DISTINCT=1. Every response is byte-identical. Verify the")
        print("        producing run was not a stub before reading anything into this.")

    # --- check 2: bundle digest -------------------------------------------
    hashes = [r["sha256"] for r in clean if r.get("sha256")]
    digest = bundle_digest(hashes)
    # Second digest over hashes recomputed from the text itself. The emitter's
    # definition folds the STORED hashes, so a row whose text was edited while
    # its hash was left intact passes that check. This one does not.
    rederived = bundle_digest([sha256_text(r["response_text"])
                               for r in clean if r.get("sha256")])
    print("\nCHECK 2 · bundle digest")
    print("  INPUT         %d row hashes, newline-joined, in file order" % len(hashes))
    print("  FROM STORED   %s" % digest)
    print("  FROM TEXT     %s" % rederived)
    print("  AGREE         %s" % ("YES" if digest == rederived else
                                  "NO -- stored hashes do not describe the stored text"))
    if a.expect:
        same = digest.strip().lower() == a.expect.strip().lower()
        print("  IN REPORT     %s" % a.expect)
        print("  MATCH         %s" % ("YES" if same else "NO"))
    else:
        print("  IN REPORT     (not supplied -- pass --expect <digest> to compare)")

    # --- payload completeness ---------------------------------------------
    with_payload = sum(1 for r in clean if r.get("request_payload"))
    print("\nCHECK 3 · request payload present")
    print("  POPULATED     %d of %d clean rows" % (with_payload, len(clean)))
    if clean and clean[0].get("request_payload"):
        pl = clean[0]["request_payload"]
        print("  DECLARED      model=%s temperature=%s max_tokens=%s" % (
            pl.get("model"), pl.get("temperature"), pl.get("max_tokens")))

    # --- verdict -----------------------------------------------------------
    failed = bool(mismatch) or missing or (digest != rederived) or (a.expect and digest.strip().lower() != a.expect.strip().lower())
    print("\n" + "-" * 62)
    print("VERDICT   %s" % ("FAIL" if failed else "PASS"))
    print("-" * 62)
    print("WHAT PASS MEANS: the stored text and the stored hashes are consistent")
    print("with each other. The file has not been edited since it was written.")
    print("WHAT PASS DOES NOT MEAN: that the responses came from the engine named")
    print("in the payload, or that the run happened as described. A hash cannot")
    print("establish either. Ask for the console receipt and the probe record.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
