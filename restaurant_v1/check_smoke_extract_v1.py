#!/usr/bin/env python3
"""check_smoke_extract_v1.py - read a candidates.csv made from the NYC01 smoke rows and say PASS or FAIL.

Not part of the measurement and not sealed. It checks the specific defects found on the smoke rows of
2026-10-07 (PREREG amendments v1.2 and v1.3), so the operator does not have to eyeball 60 names:
award-category heads, a list-word head, a dish, a real name cut at its comma, and a name that kept a
trailing bracket. PASS means those named defects are absent. It does NOT mean the list is clean: the first
version of this script printed PASS while two bracketed duplicates were in the list (amendment v1.4).
Read the names.

Usage:  python restaurant_v1/check_smoke_extract_v1.py restaurant_v1/smoke/extract_check_v3/candidates.csv
Exit 0 = PASS, 1 = FAIL.
"""
import csv
import sys

MUST_BE_ABSENT = {"sal", "kris and charlies deli", "bomb", "wanderlogs picks", "queens room sanfords sweet afton",
                  "sweet afton and bonnie"}
MUST_BE_PRESENT = {"taverna kyclades", "sal kris and charlies deli", "bel aire diner", "ruta oaxaca", "tootles and french"}


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: check_smoke_extract_v1.py <candidates.csv>")
    with open(sys.argv[1], encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    keys = {r["key"] for r in rows}
    for r in rows:
        print("%s | %s | %s" % (r["display"], r["responses"], r["engines"]))
    bad = sorted(k for k in keys if k in MUST_BE_ABSENT or k.startswith("best "))
    bad += sorted(r["display"] for r in rows if r["display"].rstrip().endswith((")", "]")))   # "Dar Lbahja (Moroccan)"
    joined = sorted(r["display"] for r in rows if r["display"].count(",") >= 2)
    missing = sorted(MUST_BE_PRESENT - keys)
    print("DISTINCT %d | unwanted present: %s | still-joined lists: %s | expected but missing: %s" % (
        len(keys), bad, joined, missing))
    ok = not bad and not joined and not missing
    print("CHECK %s" % ("PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
