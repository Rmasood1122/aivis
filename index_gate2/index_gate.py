#!/usr/bin/env python3
"""index_gate.py v0.2 -- CLAIM-GATE-IDX (OMEGA-INDEXFORGE v1.0) as runnable code.

Encodes the nine index rules I1-I9 against an index RECORD (JSON, the
INDEXFORGE <output_schema> shape), not against a report. Read-only. Stdlib
only. Git Bash / MINGW64 compatible.

Exit: 0 = clean, 1 = findings / selftest failure, 2 = usage error.

Usage:
  python index_gate.py check REC.json [...] [--as-of YYYY-MM-DD]  # one file per panel row
  python index_gate.py source SCORER.py [SCORER.py ...] # heuristic source known-bads
  python index_gate.py selftest                        # 21 fixtures, EXACT id sets
  python index_gate.py selftest-meta                   # prove the selftest can fail
  python index_gate.py schema                          # print a CLEAN record template

Provenance of the fixtures: every known-bad below is a defect MEASURED on a
real CAAI scorer -- v1.0 defects from claude/caai-formula-critique-2026-08-19-v1.md
(F1-F8) and claude/caai-recovery-2026-08-19-v1.md; v2.0 defects (F3c/F3d/F4b/F8c)
from probe_v2_defects.py run against caai_v2_scorer.py on 2026-08-19. None is
invented.

v0.2 CHANGE LOG. Four ids added after CAAI v2 passed v0.1 on defects v0.1 could
not see. That is the gate failing, caught by probing rather than by trusting it:
  + I3-SOURCE-OPAQUE, I3-DIM-SINGLE-SOURCE  a per-source floor is not a
    dimension-level floor (v2 probe 6)
  + I4-DIM-RENORM       an abstained DIMENSION leaving the composite denominator
    is the F4 defect one level up (v2 probe 5)
  + I8-CONSTANT-EXPIRED v0.1 checked a review_date EXISTED, never that it had
    PASSED (v2 probe 4)
The CAAI v1 expected-id set was updated in the same edit, per STAGE 0's CHECK.

NOT COVERED (stated so silence is not read as coverage):
  - construct validity (5x-1), order/position effects (5x-2), replay bundles
    (5x-5). Those are acceptance tests, not gate rules; this file cannot
    check them and does not pretend to.
  - source mode is HEURISTIC pattern-matching on text, not analysis. A clean
    source run is not evidence; a dirty one is. caai_v2_scorer.py scans CLEAN
    in source mode while failing 8 of 9 rules in check mode -- that gap is the
    caveat doing its job, not a contradiction.
  - ESTIMATOR RANGE is not checked. CAAI v2's stability estimator is provably
    confined to [50,100] and is invariant to the magnitude of instability
    (probes 2 and 3). Both are real defects and NEITHER is gateable by any rule
    here; they belong to construct validation (5x-1), not to a gate.
  - the gate never reads a wall clock. I8's expiry check runs only when an
    explicit --as-of DATE is supplied, so a replay of an old run cannot
    silently disagree with the original.
"""
import sys, os, json, re

VERSION = "index_gate v0.2 / CLAIM-GATE-IDX from OMEGA-INDEXFORGE v1.0"

# ---------------------------------------------------------------- vocabulary

DENOM_SYNONYMS = {
    "total": "runs", "runs": "runs", "all_runs": "runs", "n_runs": "runs",
    "total_runs": "runs", "n": "runs",
    "mentions": "mentions", "mentioned": "mentions", "mentioned_runs": "mentions",
    "appearances": "mentions", "ranks": "mentions",
}
# What a dimension's NAME promises about its denominator (I2). Auditable table,
# not a model: add a row, do not widen a regex.
NAME_IMPLIES_DENOM = [
    ("dominance", "mentions"), ("top3", "mentions"), ("top-3", "mentions"),
    ("conditional", "mentions"), ("share of voice", "mentions"),
    ("presence", "runs"), ("mention rate", "runs"),
    ("visibility", "runs"), ("invisibility", "runs"),
]
MID_SCALE = (0.5, 50.0)
FULL_SCALE = (1.0, 100.0)
R_CEILING = 0.85          # I1
# I1 algebraic-identity detector. Tolerance 0.25 because published dimension
# tables are rounded to 1dp: two such values sum with up to +-0.2 of slop, and
# CAAI v1's own table reads 79.2+20.8=100.0 / 71.7+28.3=100.0 / 61.2+38.7=99.9
# [MEASURED: caai-formula-critique sec 1]. A tighter tolerance misses the real
# defect on the real artifact; a looser one starts inventing identities.
SUM_CONST_TOL = 0.25
MIN_RECORDS_FOR_SUM = 3

ALL_IDS = [
    "I1-COLLINEAR", "I1-ALGEBRAIC", "I1-NO-MATRIX",
    "I2-DENOM-MISSING", "I2-DENOM-MISMATCH",
    "I3-NO-FLOOR", "I3-BELOW-FLOOR", "I3-IMPUTED",
    "I3-SOURCE-OPAQUE", "I3-DIM-SINGLE-SOURCE",
    "I4-MISSING-SILENT", "I4-NO-TIER-CAP", "I4-DIM-RENORM",
    "I5-NO-INTERVAL",
    "I6-OVERLAP-ORDERED", "I6-UNREPORTED-TIE",
    "I7-NO-MODEL-PIN",
    "I8-CONSTANT-UNCITED", "I8-EST-NO-REVIEW", "I8-CONSTANT-EXPIRED",
    "I9-NO-PRESCRIPTION",
]

# v0.2 additions, all four harvested from probing caai_v2_scorer.py on
# 2026-08-19 (INDEXFORGE STAGE 0: an objection that does not become a fixture
# does not count). Each cites the probe that produced it:
#   I3-SOURCE-OPAQUE     probe 6 -- a dimension that does not say how many
#                        sources it survived on cannot be floor-checked at all.
#   I3-DIM-SINGLE-SOURCE probe 6 -- v2 enforces min_n PER ENGINE and never
#                        re-checks at the dimension level, so DS/SS can be a
#                        single-engine estimate reported as MEASURED with an
#                        EMPTY abstention list.
#   I4-DIM-RENORM        probe 5 -- v2 fixed F4 for engines and reintroduced it
#                        for DIMENSIONS: SS abstained, composite renormalised
#                        over 0.80, tier thresholds unchanged, result DOMINANT.
#   I8-CONSTANT-EXPIRED  probe 4 -- ENGINE_WEIGHTS carries valid_until
#                        2026-08-01 and NOTHING in the code reads it. v0.1
#                        checked that a review_date EXISTS, never that it had
#                        not passed. An expiry nobody evaluates is a comment.

# ---------------------------------------------------------------- helpers

def canon_denom(s):
    if not s:
        return None
    return DENOM_SYNONYMS.get(str(s).strip().lower().replace(" ", "_"))

def dims(rec):
    return rec.get("dimensions") or []

def label_of(d):
    return ("%s %s" % (d.get("name", ""), d.get("label", ""))).lower()

def scored(d):
    """A dimension that emitted a number (as opposed to abstaining)."""
    return isinstance(d.get("value"), (int, float))

def norm_estimator(s):
    """Strip inversion so `weighted_mean(1 - x)` and `weighted_mean(x)` collide."""
    t = re.sub(r"\s+", "", str(s or "").lower())
    t = re.sub(r"(?:1|1\.0|100|100\.0)-", "", t)
    return t

def overlaps(a_lo, a_hi, b_lo, b_hi):
    if None in (a_lo, a_hi, b_lo, b_hi):
        return None
    return not (a_hi < b_lo or b_hi < a_lo)

def pair_key(a, b):
    return "|".join(sorted([a, b]))

def V(vid, where, detail):
    return {"id": vid, "where": where, "detail": detail}

# ---------------------------------------------------------------- rules
# Each rule: fn(records) -> list of violations. `records` is a list because
# orthogonality and separation are properties of a PANEL, not of one row.

def rule_i1(records, as_of=None):
    """ORTHOGONALITY. No pair |r| > 0.85; no dimension algebraically derivable
    from another. KNOWN-BAD: SRS = weighted_mean(1 - mention_rate) beside
    PS = weighted_mean(mention_rate)  [MEASURED: caai-formula-critique F1]."""
    out = []
    rec = records[0]
    names = [d.get("name") for d in dims(rec)]
    r = rec.get("pairwise_r") or {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            k = pair_key(names[i], names[j])
            if k not in r:
                out.append(V("I1-NO-MATRIX", k, "no published pairwise r for this dimension pair"))
            elif abs(float(r[k])) > R_CEILING:
                out.append(V("I1-COLLINEAR", k, "|r|=%.3f exceeds ceiling %.2f" % (abs(float(r[k])), R_CEILING)))
    # (a) estimator-string derivability -- catches the identity even if r is fudged
    est = {d.get("name"): d.get("estimator") for d in dims(rec)}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            if not est.get(a) or not est.get(b):
                continue
            if est[a] != est[b] and norm_estimator(est[a]) == norm_estimator(est[b]):
                out.append(V("I1-ALGEBRAIC", pair_key(a, b),
                             "estimators are inversions of one another: %r vs %r" % (est[a], est[b])))
    # (b) sum-to-a-constant across the panel -- how F1 was actually found
    if len(records) >= MIN_RECORDS_FOR_SUM:
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                sums = []
                for rr in records:
                    m = {d.get("name"): d.get("value") for d in dims(rr)}
                    if isinstance(m.get(a), (int, float)) and isinstance(m.get(b), (int, float)):
                        sums.append(m[a] + m[b])
                if len(sums) == len(records) and len(sums) >= MIN_RECORDS_FOR_SUM:
                    if max(sums) - min(sums) <= SUM_CONST_TOL:
                        k = pair_key(a, b)
                        if not any(v["id"] == "I1-ALGEBRAIC" and v["where"] == k for v in out):
                            out.append(V("I1-ALGEBRAIC", k,
                                         "values sum to a constant %.2f on %d/%d rows -- one dimension is the other inverted"
                                         % (sum(sums) / len(sums), len(sums), len(records))))
    return out

def rule_i2(records, as_of=None):
    """DENOMINATOR TRUTH. Every rate states its denominator, and it is the one
    the dimension's NAME implies. KNOWN-BAD: 'dominance' = top3/all_runs
    [MEASURED: caai-formula-critique F2]."""
    out = []
    for rec in records:
        for d in dims(rec):
            nm = d.get("name", "?")
            if not scored(d) and d.get("status") == "INSUFFICIENT_CONTEXT":
                continue
            declared = d.get("denominator")
            if not declared:
                out.append(V("I2-DENOM-MISSING", nm, "dimension emits a rate with no stated denominator"))
                continue
            cd = canon_denom(declared)
            lab = label_of(d)
            for token, expected in NAME_IMPLIES_DENOM:
                if token in lab:
                    if cd and cd != expected:
                        out.append(V("I2-DENOM-MISMATCH", nm,
                                     "name implies denominator %r (token %r) but %r is declared"
                                     % (expected, token, declared)))
                    break
            m = re.search(r"/\s*([A-Za-z_][A-Za-z_0-9]*)", str(d.get("estimator") or ""))
            if m and cd:
                ce = canon_denom(m.group(1))
                if ce and ce != cd:
                    out.append(V("I2-DENOM-MISMATCH", nm,
                                 "estimator divides by %r (%s) but denominator is declared %r (%s)"
                                 % (m.group(1), ce, declared, cd)))
    return out

def rule_i3(records, as_of=None):
    """SUPPORT FLOOR. Below min_n a dimension abstains. No imputation, no
    mid-scale default, no zero-for-missing. KNOWN-BAD: stability = 1.0 from a
    single observation; fi_rank = 0.5 default  [MEASURED: critique F3, F6]."""
    out = []
    for rec in records:
        for d in dims(rec):
            nm = d.get("name", "?")
            min_n, n, val = d.get("min_n"), d.get("n"), d.get("value")
            if min_n is None:
                out.append(V("I3-NO-FLOOR", nm, "no min_n declared; the floor cannot be enforced"))
            if d.get("status") == "INSUFFICIENT_CONTEXT" and scored(d):
                out.append(V("I3-IMPUTED", nm, "status INSUFFICIENT_CONTEXT but a numeric value %r is published" % (val,)))
                continue
            if not scored(d):
                continue
            if isinstance(n, int) and isinstance(min_n, int) and n < min_n:
                out.append(V("I3-BELOW-FLOOR", nm, "value %r published at n=%d, below min_n=%d" % (val, n, min_n)))
            if n == 1 and val in FULL_SCALE:
                out.append(V("I3-IMPUTED", nm, "perfect score %r from a single observation is a default, not a measurement" % (val,)))
            if n == 0:
                out.append(V("I3-IMPUTED", nm, "value %r published from zero observations" % (val,)))
            if val in MID_SCALE and (n is None or (isinstance(min_n, int) and isinstance(n, int) and n < min_n)):
                out.append(V("I3-IMPUTED", nm, "mid-scale default %r on unsupported n=%r" % (val, n)))
            # v0.2, probe 6: a per-source floor is not a dimension-level floor.
            used, elig = d.get("sources_used"), d.get("sources_eligible")
            if used is None or elig is None:
                out.append(V("I3-SOURCE-OPAQUE", nm,
                             "scored dimension does not declare sources_used/sources_eligible; "
                             "a per-source floor cannot be re-checked at the dimension level"))
            elif isinstance(used, int) and isinstance(elig, int) and elig > 1 and used <= 1:
                out.append(V("I3-DIM-SINGLE-SOURCE", nm,
                             "value %r survives on %d of %d eligible sources and is still reported "
                             "as measured, with no abstention" % (val, used, elig)))
    return out

def rule_i4(records, as_of=None):
    """COVERAGE HONESTY. An unreachable engine is INSUFFICIENT, not absent; it
    may not silently leave the denominator, and it caps the tier. KNOWN-BAD:
    dropping Gemini and renormalising over 0.80  [MEASURED: critique F4]."""
    out = []
    for rec in records:
        comp = rec.get("composite") or {}
        # v0.2, probe 5: the F4 failure class, one level up. An ABSTAINED
        # DIMENSION that silently leaves the composite denominator is the same
        # defect as an absent engine leaving the engine denominator.
        abst = comp.get("dimensions_abstained") or []
        dren = comp.get("dimension_renormalised_over")
        if abst or (isinstance(dren, (int, float)) and dren < 1.0):
            capped_by = str((rec.get("tier") or {}).get("capped_by") or "")
            if "dimension" not in capped_by.lower() and "abstain" not in capped_by.lower():
                out.append(V("I4-DIM-RENORM", ",".join(map(str, abst)) or "composite",
                             "composite renormalised over %s of the dimension weight with "
                             "unchanged tier thresholds; tier.capped_by=%r does not name the abstention"
                             % (("%.2f" % dren) if isinstance(dren, (int, float)) else "part",
                                capped_by or None)))
        cov = rec.get("coverage") or {}
        missing = cov.get("missing") or []
        if not missing:
            continue
        if not cov.get("tier_cap_applied"):
            out.append(V("I4-NO-TIER-CAP", ",".join(map(str, missing)),
                         "engine(s) missing but coverage.tier_cap_applied is false"))
        ren = comp.get("renormalised_over")
        if isinstance(ren, (int, float)) and ren < 1.0 and comp.get("full_denominator_value") is None:
            out.append(V("I4-MISSING-SILENT", ",".join(map(str, missing)),
                         "weights renormalised over %.2f with no full-denominator companion published" % ren))
    return out

def rule_i5(records, as_of=None):
    """INTERVAL COVERAGE. point_estimates_without_interval = 0. KNOWN-BAD:
    stability 0.675 to three decimals from n=3  [MEASURED: critique F5]."""
    out = []
    for rec in records:
        for d in dims(rec):
            if scored(d) and (d.get("ci_low") is None or d.get("ci_high") is None):
                out.append(V("I5-NO-INTERVAL", d.get("name", "?"), "value %r published without an interval" % (d.get("value"),)))
        c = rec.get("composite") or {}
        if isinstance(c.get("value"), (int, float)) and (c.get("ci_low") is None or c.get("ci_high") is None):
            out.append(V("I5-NO-INTERVAL", "composite", "composite %r published without an interval" % (c.get("value"),)))
    return out

def rule_i6(records, as_of=None):
    """SEPARATION. No ordinal claim where intervals overlap. KNOWN-BAD:
    'Purple leads at 76.8' when Purple [68.2-74.5] overlaps Casper [65.5-73.1]
    [MEASURED: critique F5 / INDEXFORGE I6]."""
    out = []
    for rec in records:
        for s in (rec.get("separation") or []):
            if s.get("overlap") and str(s.get("verdict", "")).upper() == "ORDERED":
                out.append(V("I6-OVERLAP-ORDERED", s.get("pair", "?"),
                             "intervals overlap but the pair is published as ORDERED"))
    if len(records) >= 2:
        declared = set()
        for rec in records:
            for s in (rec.get("separation") or []):
                declared.add(pair_key(*str(s.get("pair", "?")).split("|", 1)) if "|" in str(s.get("pair", "")) else str(s.get("pair")))
        subj = [(r.get("subject") or r.get("brand") or "row%d" % i, (r.get("composite") or {}))
                for i, r in enumerate(records)]
        for i in range(len(subj)):
            for j in range(i + 1, len(subj)):
                (na, ca), (nb, cb) = subj[i], subj[j]
                ov = overlaps(ca.get("ci_low"), ca.get("ci_high"), cb.get("ci_low"), cb.get("ci_high"))
                if ov and pair_key(na, nb) not in declared:
                    out.append(V("I6-UNREPORTED-TIE", pair_key(na, nb),
                                 "composite intervals overlap and no separation verdict is published"))
    return out

def rule_i7(records, as_of=None):
    """TEMPORAL ANCHOR. Every record pins model id + snapshot date + api
    version. KNOWN-BAD: provider = 'anthropic' with no model version
    [MEASURED: critique F8]."""
    out = []
    need = ("model_id", "snapshot_date", "api_version")
    for rec in records:
        t = rec.get("temporal") or {}
        rows = t.get("records") or []
        if not rows:
            out.append(V("I7-NO-MODEL-PIN", rec.get("subject", "record"), "no temporal block: nothing is pinned"))
            continue
        for k, row in enumerate(rows):
            miss = [f for f in need if not row.get(f)]
            if miss:
                out.append(V("I7-NO-MODEL-PIN", "%s/%s" % (rec.get("subject", "record"), row.get("engine", "row%d" % k)),
                             "missing %s" % ", ".join(miss)))
    return out

def rule_i8(records, as_of=None):
    """CONSTANT PROVENANCE. Every weight, threshold, normaliser and floor has a
    derivation, an [EST: basis] with a review date, or a deletion. KNOWN-BAD:
    `variance / 25.0  # max reasonable variance is ~25`  [MEASURED: critique F6]."""
    out = []
    for rec in records:
        buckets = [(d.get("name", "?"), d.get("constants") or []) for d in dims(rec)]
        buckets.append(("composite", (rec.get("composite") or {}).get("constants") or []))
        for owner, consts in buckets:
            for c in consts:
                where = "%s.%s" % (owner, c.get("name", "?"))
                der, est = c.get("derivation"), c.get("est_basis")
                if not der and not est:
                    out.append(V("I8-CONSTANT-UNCITED", where, "constant %r has neither a derivation nor an [EST: basis]" % (c.get("value"),)))
                elif est and not c.get("review_date"):
                    out.append(V("I8-EST-NO-REVIEW", where, "[EST: %s] carries no review_date; an estimate with no expiry never decays" % est))
                # v0.2, probe 4: v0.1 checked that a review_date EXISTS. It never
                # checked whether it had PASSED. An expiry nobody evaluates is a
                # comment, and M9 says a comment is not a control.
                rd = c.get("review_date")
                if as_of and rd and str(rd) < str(as_of):
                    out.append(V("I8-CONSTANT-EXPIRED", where,
                                 "constant %r expired on %s (as-of %s) and is still in use "
                                 "with no [UNVERIFIED] downgrade" % (c.get("value"), rd, as_of)))
    return out

def rule_i9(records, as_of=None):
    """PRESCRIPTION. Every dimension maps to at least one action a buyer can
    take. KNOWN-BAD: a fragmentation index with no recommended response
    [MEASURED: INDEXFORGE E5 / 5x-3]."""
    out = []
    rec = records[0]
    for d in dims(rec):
        p = d.get("prescription")
        if not (isinstance(p, str) and p.strip()) and not d.get("prescriptions"):
            out.append(V("I9-NO-PRESCRIPTION", d.get("name", "?"), "dimension changes no decision: no prescriptive path published"))
    return out

RULES = [("I1", rule_i1), ("I2", rule_i2), ("I3", rule_i3), ("I4", rule_i4),
         ("I5", rule_i5), ("I6", rule_i6), ("I7", rule_i7), ("I8", rule_i8),
         ("I9", rule_i9)]

def run_gate(records, disabled=frozenset(), as_of=None):
    out = []
    for rid, fn in RULES:
        if rid in disabled:
            continue
        out.extend(fn(records, as_of))
    return out

# ---------------------------------------------------------------- source mode

SRC_PATTERNS = [
    ("I3-IMPUTED", re.compile(r"len\([^)]*\)\s*==\s*1\s*:"), "branch on a single observation"),
    ("I3-IMPUTED", re.compile(r"=\s*0\.5\b"), "mid-scale default assignment"),
    ("I2-DENOM-MISMATCH", re.compile(r"top3\w*\s*/\s*(total|runs|n_runs|all_runs)\b"), "top-3 rate over all runs, not over mentions"),
    ("I8-CONSTANT-UNCITED", re.compile(r"/\s*\d+\.\d+\s*[\)\],]*\s*(?:#.*)?$"), "bare numeric normaliser"),
]
SRC_EXEMPT = re.compile(r"\[(MEASURED|EST|QUOTED|REPORTED):", re.I)

def cmd_source(paths):
    out = []
    for p in paths:
        lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
        for i, ln in enumerate(lines, 1):
            if SRC_EXEMPT.search(ln):
                continue
            for vid, rx, why in SRC_PATTERNS:
                if rx.search(ln):
                    if vid == "I3-IMPUTED" and "==" in ln and i < len(lines):
                        nxt = lines[i] if i < len(lines) else ""
                        if not re.search(r"=\s*(0\.0|1\.0|0\.5|100\.0)\b", nxt):
                            continue
                    out.append(V(vid, "%s:%d" % (os.path.basename(p), i), "%s -- %s" % (why, ln.strip()[:70])))
    return out

# ---------------------------------------------------------------- fixtures

def clean_record(subject="Purple"):
    """A record that MUST produce zero violations. If this ever fails, the gate
    is over-firing and the fixtures below prove nothing."""
    def dim(name, label, est, denom, val, lo, hi, n, presc, consts):
        return {"name": name, "label": label, "construct": "see methodology",
                "estimator": est, "denominator": denom, "min_n": 5, "status": "OK",
                "value": val, "ci_low": lo, "ci_high": hi, "n": n,
                "sources_used": 4, "sources_eligible": 4,
                "prescription": presc, "constants": consts}
    W = lambda nm, v, why: {"name": nm, "value": v, "derivation": why, "review_date": "2026-12-31"}
    return {
        "index_version": "2.0", "supersedes": "1.0", "subject": subject,
        "dimensions": [
            dim("PS", "Presence Score", "weighted_mean_e(mentions_e / runs_e)", "runs",
                79.2, 74.1, 83.6, 120, "buy category coverage on the engine with the lowest mention rate", []),
            dim("DS", "Dominance Strength", "weighted_mean_e(top3_e / mentions_e)", "mentions",
                59.4, 52.0, 66.1, 95, "improve ranked placement where you are already mentioned", []),
            dim("SS", "Stability Score", "weighted_mean_e(1 - dispersion(ranks_e))", "mentions",
                94.2, 90.1, 97.0, 95, "stabilise the engine with the widest rank spread", []),
            dim("SRS", "Suppression Risk (worst-engine invisibility)", "max_e(1 - mention_rate_e)", "runs",
                53.3, 47.0, 59.2, 120, "treat the worst engine as a named blind spot with a budget", []),
            dim("FI", "Fragmentation Index", "entropy_e(rank_distribution_e)", "mentions",
                24.8, 19.4, 30.6, 95, "consolidate messaging where engine answers diverge most", []),
        ],
        "pairwise_r": {"DS|PS": 0.41, "PS|SS": 0.22, "PS|SRS": 0.62, "FI|PS": -0.18,
                       "DS|SS": 0.30, "DS|SRS": 0.11, "DS|FI": -0.27,
                       "SRS|SS": 0.09, "FI|SS": -0.44, "FI|SRS": 0.35},
        "composite": {"value": 76.8, "ci_low": 71.2, "ci_high": 81.9,
                      "weights_used": {"PS": 0.25, "DS": 0.25, "SS": 0.20, "SRS": 0.20, "FI": 0.10},
                      "renormalised_over": 1.0, "full_denominator_value": 76.8,
                      "dimension_renormalised_over": 1.0, "dimensions_abstained": [],
                      "constants": [W("w_PS", 0.25, "panel-assigned, published in methodology appendix A"),
                                    W("w_DS", 0.25, "panel-assigned, published in methodology appendix A"),
                                    W("w_SS", 0.20, "panel-assigned, published in methodology appendix A"),
                                    W("w_SRS", 0.20, "panel-assigned, published in methodology appendix A"),
                                    W("w_FI", 0.10, "panel-assigned, published in methodology appendix A")]},
        "coverage": {"present": ["openai", "google", "anthropic", "grok"], "missing": [],
                     "ratio": 1.0, "tier_cap_applied": False},
        "tier": {"value": "STRONG", "computed_from": "composite ci_low", "capped_by": None},
        "separation": [],
        "temporal": {"records": [
            {"engine": "openai", "model_id": "gpt-x-2026-02", "snapshot_date": "2026-02-23", "api_version": "v1"},
            {"engine": "anthropic", "model_id": "claude-x-2026-02", "snapshot_date": "2026-02-23", "api_version": "v1"},
        ]},
    }

def _mut(fn, subject="Purple"):
    r = clean_record(subject)
    fn(r)
    return [r]

def _d(rec, name):
    return next(d for d in rec["dimensions"] if d["name"] == name)

def _f1a(r): r["pairwise_r"]["PS|SRS"] = -1.00
def _f1b(r):
    _d(r, "PS")["estimator"] = "weighted_mean_e(mention_rate_e)"
    _d(r, "SRS")["estimator"] = "weighted_mean_e(1 - mention_rate_e)"
def _f1c(r): del r["pairwise_r"]["FI|SS"]
def _f2a(r): _d(r, "DS").update(estimator="weighted_mean_e(top3_e / total)", denominator="all_runs")
def _f2b(r): _d(r, "SS")["denominator"] = None
def _f3a(r): _d(r, "SS").update(value=100.0, ci_low=100.0, ci_high=100.0, n=1)
def _f3b(r): _d(r, "FI")["min_n"] = None
def _f4(r):
    r["coverage"].update(present=["openai", "anthropic", "grok"], missing=["google"], ratio=0.80, tier_cap_applied=False)
    r["composite"]["renormalised_over"] = 0.80
    r["composite"]["full_denominator_value"] = None
def _f5(r): _d(r, "SS").update(ci_low=None, ci_high=None)
def _f6a(r): r["separation"] = [{"pair": "Purple|Casper", "overlap": True, "verdict": "ORDERED"}]
def _f7(r): r["temporal"]["records"] = [{"engine": "anthropic", "provider": "anthropic"}]
def _f3c(r): _d(r, "DS").update(sources_used=1, sources_eligible=3)
def _f3d(r): [_d(r, "SS").pop(k) for k in ("sources_used", "sources_eligible")]
def _f4b(r):
    _d(r, "SS").update(value=None, ci_low=None, ci_high=None, status="INSUFFICIENT_CONTEXT")
    r["composite"].update(dimension_renormalised_over=0.80, dimensions_abstained=["SS"])
    r["tier"]["capped_by"] = None
def _f8c(r): _d(r, "SS")["constants"] = [{"name": "engine_w_openai", "value": 0.35,
                                          "est_basis": "consumer reach, operator estimate 2026-02",
                                          "review_date": "2026-08-01"}]
def _f8a(r): _d(r, "SS")["constants"] = [{"name": "variance_normaliser", "value": 25.0}]
def _f8b(r): _d(r, "FI")["constants"] = [{"name": "fi_rank_split", "value": 0.7, "est_basis": "author judgement"}]
def _f9(r): _d(r, "FI").pop("prescription")

def _f1d():
    """The identity with the estimator strings scrubbed clean -- caught only by
    summing two published columns across the panel, which is how F1 was actually
    found [MEASURED: caai-formula-critique sec 1]. Estimators here do NOT
    invert, so the string detector is blind and only the panel arithmetic sees it."""
    rows = [("Purple", 79.2, 59.4, 94.2, 20.8, 24.8, 83.0, 85.0),
            ("Casper", 71.7, 35.4, 90.8, 28.3, 14.5, 71.0, 75.0),
            ("Tempur-Pedic", 61.2, 47.5, 83.0, 38.7, 22.6, 61.0, 65.0)]
    out = []
    for subj, ps, ds, ss, srs, fi, clo, chi in rows:
        r = clean_record(subj)
        for nm, val in (("PS", ps), ("DS", ds), ("SS", ss), ("SRS", srs), ("FI", fi)):
            _d(r, nm).update(value=val, ci_low=val - 5.0, ci_high=val + 5.0)
        r["composite"].update(value=(clo + chi) / 2.0, ci_low=clo, ci_high=chi,
                              full_denominator_value=(clo + chi) / 2.0)
        out.append(r)
    return out

def _f6b():
    a, b = clean_record("Purple"), clean_record("Casper")
    a["composite"].update(value=76.8, ci_low=68.2, ci_high=74.5)
    b["composite"].update(value=67.8, ci_low=65.5, ci_high=73.1)
    return [a, b]

def caai_v1_panel():
    """CAAI v1.0 as actually shipped, reconstructed from the published dimension
    table [MEASURED: caai-formula-critique-2026-08-19-v1.md sec 0] and the
    recovered constant block [MEASURED: caai-recovery-2026-08-19-v1.md sec 3].
    This is the FORGE's own falsifier: if this returns 0 blocks, the gate is a
    rubber stamp and must be rebuilt."""
    rows = [("Purple", 79.2, 59.4, 94.2, 20.8, 24.8, 76.8),
            ("Casper", 71.7, 35.4, 90.8, 28.3, 14.5, 67.8),
            ("Tempur-Pedic", 61.2, 47.5, 83.0, 38.7, 22.6, 63.8)]
    out = []
    for subj, ps, ds, ss, srs, fi, comp in rows:
        def d(name, label, est, denom, val):
            return {"name": name, "label": label, "estimator": est, "denominator": denom,
                    "min_n": None, "status": "OK", "value": val,
                    "ci_low": None, "ci_high": None, "n": 3, "constants": []}
        out.append({
            "index_version": "1.0", "subject": subj,
            "dimensions": [
                d("PS", "Presence Score", "weighted_mean_e(mention_rate_e)", "total", ps),
                d("DS", "Dominance Strength", "weighted_mean_e(top3_e / total)", "total", ds),
                d("SS", "Stability Score", "weighted_mean_e(1 - variance / 25.0)", "ranks", ss),
                d("SRS", "Suppression Risk Score", "weighted_mean_e(1 - mention_rate_e)", "total", srs),
                d("FI", "Fragmentation Index", "fi_rank * 0.7 + mention_spread * 0.3", "total", fi),
            ],
            "pairwise_r": {},
            "composite": {"value": comp, "ci_low": None, "ci_high": None,
                          "weights_used": {"PS": 0.25, "DS": 0.25, "SS": 0.20, "SRS": 0.20, "FI": 0.10},
                          "renormalised_over": 0.80, "full_denominator_value": None,
                          "constants": [{"name": "variance_normaliser", "value": 25.0},
                                        {"name": "fi_rank_split", "value": 0.7}]},
            "coverage": {"present": ["openai", "anthropic", "grok"], "missing": ["google"],
                         "ratio": 0.80, "tier_cap_applied": False},
            "tier": {"value": "STRONG", "computed_from": "composite point estimate", "capped_by": None},
            "separation": [],
            "temporal": {"records": [{"engine": "openai", "provider": "openai"}]},
        })
    return out

BAD_SOURCE = """# excerpt reproduced from caai_v1_scorer.py [QUOTED: caai-recovery sec 2]
def stability(ranks):
    if len(ranks) >= 2:
        return max(0.0, 1.0 - variance / 25.0)
    elif len(ranks) == 1:
        stability = 1.0
        return stability
    return 0.0

def dominance(top3, total):
    top3_rate = top3 / total
    return top3_rate

fi_rank = 0.5
"""

FIXTURES = [
    ("CLEAN                       (base must be silent)", lambda: [clean_record()], set()),
    ("F1a  r=-1.00 PS vs SRS      [critique F1]", lambda: _mut(_f1a), {"I1-COLLINEAR"}),
    ("F1b  inverted estimators    [critique F1]", lambda: _mut(_f1b), {"I1-ALGEBRAIC"}),
    ("F1c  incomplete r matrix    [INDEXFORGE STAGE 1]", lambda: _mut(_f1c), {"I1-NO-MATRIX"}),
    ("F1d  columns sum to 100     [critique F1]", _f1d, {"I1-ALGEBRAIC"}),
    ("F2a  top3/all_runs          [critique F2]", lambda: _mut(_f2a), {"I2-DENOM-MISMATCH"}),
    ("F2b  denominator absent     [INDEXFORGE I2]", lambda: _mut(_f2b), {"I2-DENOM-MISSING"}),
    ("F3a  SS=100 from n=1        [critique F3]", lambda: _mut(_f3a), {"I3-BELOW-FLOOR", "I3-IMPUTED"}),
    ("F3b  no support floor       [critique F3]", lambda: _mut(_f3b), {"I3-NO-FLOOR"}),
    ("F3c  dim on 1 of 3 sources  [v2 probe 6]", lambda: _mut(_f3c), {"I3-DIM-SINGLE-SOURCE"}),
    ("F3d  source count undeclared[v2 probe 6]", lambda: _mut(_f3d), {"I3-SOURCE-OPAQUE"}),
    ("F4   Gemini renormalised    [critique F4]", lambda: _mut(_f4), {"I4-NO-TIER-CAP", "I4-MISSING-SILENT"}),
    ("F4b  abstained dim, no cap  [v2 probe 5]", lambda: _mut(_f4b), {"I4-DIM-RENORM"}),
    ("F5   value without interval [critique F5]", lambda: _mut(_f5), {"I5-NO-INTERVAL"}),
    ("F6a  overlap sold as ORDERED[INDEXFORGE I6]", lambda: _mut(_f6a), {"I6-OVERLAP-ORDERED"}),
    ("F6b  unreported tie         [INDEXFORGE I6]", _f6b, {"I6-UNREPORTED-TIE"}),
    ("F7   provider, no model id  [critique F8]", lambda: _mut(_f7), {"I7-NO-MODEL-PIN"}),
    ("F8a  variance / 25.0        [critique F6]", lambda: _mut(_f8a), {"I8-CONSTANT-UNCITED"}),
    ("F8b  [EST] with no expiry   [critique F6]", lambda: _mut(_f8b), {"I8-EST-NO-REVIEW"}),
    ("F8c  expiry already passed  [v2 probe 4]", lambda: _mut(_f8c), {"I8-CONSTANT-EXPIRED"}),
    ("F9   dimension, no action   [INDEXFORGE 5x-3]", lambda: _mut(_f9), {"I9-NO-PRESCRIPTION"}),
]

CAAI_V1_EXPECTED = {
    "I1-ALGEBRAIC", "I1-NO-MATRIX", "I2-DENOM-MISMATCH", "I3-NO-FLOOR",
    "I3-SOURCE-OPAQUE",                      # v0.2: v1 declares no source counts
    "I4-NO-TIER-CAP", "I4-MISSING-SILENT", "I5-NO-INTERVAL", "I7-NO-MODEL-PIN",
    "I8-CONSTANT-UNCITED", "I9-NO-PRESCRIPTION",
}
# Fixed date for the selftest so I8-CONSTANT-EXPIRED is deterministic. The gate
# must never read a wall clock: a rule whose verdict changes overnight cannot be
# regression-tested, and a replay of an old run would silently disagree.
SELFTEST_AS_OF = "2026-08-19"
BAD_SOURCE_EXPECTED = {"I3-IMPUTED", "I2-DENOM-MISMATCH", "I8-CONSTANT-UNCITED"}

# ---------------------------------------------------------------- selftest

def selftest(disabled=frozenset(), verbose=True, as_of=SELFTEST_AS_OF):
    """Assert the EXACT violation-id set per fixture. Not a count, not a
    substring: an extra id fails as hard as a missing one."""
    failures, exercised = [], set()
    cases = list(FIXTURES)
    cases.append(("CAAI v1.0 as shipped        [FORGE falsifier]", caai_v1_panel, CAAI_V1_EXPECTED))
    for name, build, expected in cases:
        got = {v["id"] for v in run_gate(build(), disabled, as_of)}
        exercised |= got
        if got != expected:
            failures.append("%-44s expected %s got %s" % (name, sorted(expected) or "{}", sorted(got) or "{}"))
        elif verbose:
            print("  ok   %-44s %s" % (name, sorted(got) or "(silent)"))
    got_src = {v["id"] for v in cmd_source_text(BAD_SOURCE)}
    exercised |= got_src
    if got_src != BAD_SOURCE_EXPECTED:
        failures.append("%-44s expected %s got %s" % ("SRC  caai_v1_scorer.py excerpt", sorted(BAD_SOURCE_EXPECTED), sorted(got_src)))
    elif verbose:
        print("  ok   %-44s %s" % ("SRC  caai_v1_scorer.py excerpt", sorted(got_src)))
    unexercised = [i for i in ALL_IDS if i not in exercised and not any(i.startswith(r + "-") for r in disabled)]
    if unexercised:
        failures.append("COVERAGE: declared violation ids never exercised by any fixture: %s" % unexercised)
    return failures

def cmd_source_text(text):
    import tempfile
    fd, p = tempfile.mkstemp(suffix=".py", text=True)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    try:
        return cmd_source([p])
    finally:
        os.unlink(p)   # agent-created temp only; nothing pre-existing is touched

def selftest_meta():
    """Prove the selftest CAN fail. A selftest that passes with a rule switched
    off is a rubber stamp (APEX L6) and the whole file is theatre."""
    failures = []
    if selftest(verbose=False):
        return ["selftest-meta precondition: selftest must PASS before it can be shown to fail"]
    for rid, _ in RULES:
        if not selftest(disabled={rid}, verbose=False):
            failures.append("rule %s disabled and the selftest still PASSED -- %s is unfixtured, the gate is a rubber stamp" % (rid, rid))
        else:
            print("  ok   disabling %s makes the selftest fail, as it must" % rid)
    return failures

# ---------------------------------------------------------------- cli

def report(findings):
    if not findings:
        print("CLEAN=0 violations   (%s)" % VERSION)
        return 0
    print("BLOCK violations=%d   (%s)" % (len(findings), VERSION))
    for v in findings:
        print("  %-20s %-28s %s" % (v["id"], v["where"], v["detail"]))
    ids = sorted({v["id"] for v in findings})
    print("  ids: %s" % " ".join(ids))
    return 1

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    mode, args = sys.argv[1], sys.argv[2:]
    as_of = None
    if "--as-of" in args:
        i = args.index("--as-of")
        as_of = args[i + 1]
        args = args[:i] + args[i + 2:]
    if mode == "check":
        if not args:
            print(__doc__)
            return 2
        recs = [json.load(open(p, encoding="utf-8")) for p in args]
        print("checking %d record(s): %s" % (len(recs), ", ".join(os.path.basename(a) for a in args)))
        if len(recs) < MIN_RECORDS_FOR_SUM:
            print("  NOTE: %d record(s) supplied; the I1 sum-to-a-constant detector needs >= %d and did not run."
                  % (len(recs), MIN_RECORDS_FOR_SUM))
        if not as_of:
            print("  NOTE: no --as-of DATE given; the I8 constant-expiry detector did not run.")
        return report(run_gate(recs, as_of=as_of))
    if mode == "source":
        if not args:
            print(__doc__)
            return 2
        print("HEURISTIC source scan (not analysis): %s" % ", ".join(os.path.basename(a) for a in args))
        return report(cmd_source(args))
    if mode == "selftest":
        print("selftest: %d fixtures + CAAI v1 panel + source excerpt" % len(FIXTURES))
        f = selftest()
        if f:
            print("FAIL %d" % len(f))
            [print("  -", x) for x in f]
            return 1
        print("PASS: every fixture produced its exact expected violation-id set.")
        return 0
    if mode == "selftest-meta":
        print("selftest-meta: disabling each rule in turn")
        f = selftest_meta()
        if f:
            print("FAIL %d" % len(f))
            [print("  -", x) for x in f]
            return 1
        print("PASS: the selftest fails when any of the %d rules is switched off." % len(RULES))
        return 0
    if mode == "schema":
        print(json.dumps(clean_record(), indent=2))
        return 0
    print(__doc__)
    return 2

if __name__ == "__main__":
    sys.exit(main())
