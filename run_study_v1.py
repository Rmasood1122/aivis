#!/usr/bin/env python3
"""run_study_v1.py - pick the engines for a study from config/engine_policy_v1.json, then
(optionally) launch run_bank_multi_v2.py for the engines that were picked and for no others.

Default is a DRY RUN: the plan and the exact runner commands are printed, nothing is called.
--execute runs the commands in order and stops on the first non-zero exit.

Name the vertical; the audience (b2c / b2b / mixed) and local intent are read from
config/vertical_map_v1.json, and the engines follow from the audience:
  python run_study_v1.py restaurants
  python run_study_v1.py "law firms"
  python run_study_v1.py fashion

A vertical that is not on the map is planned as mixed (every engine) with a printed warning.
--audience overrides the map.

Plan + commands (dry run):
  python run_study_v1.py restaurants \
      --bank restaurants_v1/nyc_prompts_v1.jsonl --runs 5 --outdir restaurants_v1/runs

Surface check first (1 prompt x 1 run per picked engine), then the measured run:
  ... --smoke --execute
  ... --execute

Admitting a conditional engine (Perplexity or Claude on a B2C study):
  --request perplexity                      the buyer asked for it by name
  --declare "perplexity=buyer's audience is equity analysts"   operator's written reason

--execute writes the plan JSON into --outdir before the first call, so the evidence files sit
next to the record of why each engine was or was not called. Existing files are never overwritten.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from aivis.engine_select import (
    AUDIENCE_FROM_OPERATOR,
    SelectionError,
    StudyProfile,
    build_plan,
    classify_vertical,
    load_policy,
    load_vertical_map,
    render_plan,
    runner_commands,
)

DEFAULT_POLICY = Path(__file__).resolve().parent / "config" / "engine_policy_v1.json"
DEFAULT_VERTICAL_MAP = Path(__file__).resolve().parent / "config" / "vertical_map_v1.json"


def _pairs(values, flag):
    out = []
    for v in values:
        if "=" not in v:
            sys.exit("REFUSE: %s wants ENGINE=VALUE, got %r" % (flag, v))
        k, val = v.split("=", 1)
        out.append((k.strip(), val.strip()))
    return tuple(out)


def _write_new(path, plan):
    p = Path(path)
    if p.exists():
        sys.exit("REFUSE: %s exists. Versioned new paths only." % path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("PLAN WRITTEN %s" % path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("vertical_pos", nargs="?", metavar="VERTICAL",
                    help='e.g. restaurants, "law firms", retail, fashion')
    ap.add_argument("--vertical", help="same as the positional VERTICAL")
    ap.add_argument("--audience", help="b2c | b2b | mixed; overrides the vertical map")
    ap.add_argument("--local", action="store_true",
                    help="force local intent on (the vertical map can also turn it on)")
    ap.add_argument("--vertical-map", default=str(DEFAULT_VERTICAL_MAP))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--search", dest="search", action="store_true", default=None)
    g.add_argument("--no-search", dest="search", action="store_false")
    ap.add_argument("--request", action="append", default=[], metavar="ENGINE",
                    help="engine the buyer asked for by name (repeatable)")
    ap.add_argument("--declare", action="append", default=[], metavar="ENGINE=REASON",
                    help="operator-declared relevance with a written reason (repeatable)")
    ap.add_argument("--model", action="append", default=[], metavar="ENGINE=ID",
                    help="override the policy's recorded model id (repeatable)")
    ap.add_argument("--policy", default=str(DEFAULT_POLICY))
    ap.add_argument("--plan-out", help="write the plan JSON here (refuses an existing path)")
    ap.add_argument("--bank", help="prompt bank .json or .jsonl; enables the runner commands")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--outdir", help="directory for evidence files (required with --bank)")
    ap.add_argument("--tag", help="label in evidence file names (default: bank file stem)")
    ap.add_argument("--smoke", action="store_true", help="1 prompt x 1 run per picked engine")
    ap.add_argument("--execute", action="store_true", help="run the commands (default: dry run)")
    a = ap.parse_args(argv)

    if a.bank and not a.outdir:
        sys.exit("REFUSE: --bank needs --outdir")
    if a.execute and not a.bank:
        sys.exit("REFUSE: --execute needs --bank and --outdir")
    if a.execute and not Path("run_bank_multi_v2.py").exists():
        sys.exit("REFUSE: --execute must be started from the repo root (run_bank_multi_v2.py "
                 "and .env are read from the current directory)")

    if a.vertical and a.vertical_pos and a.vertical != a.vertical_pos:
        sys.exit("REFUSE: two different verticals given (%r and %r)" % (a.vertical_pos, a.vertical))
    vertical = a.vertical or a.vertical_pos
    if not vertical:
        sys.exit("REFUSE: name the vertical, e.g. python run_study_v1.py restaurants")

    try:
        policy, digest = load_policy(a.policy)
        vmap, vmap_digest = load_vertical_map(a.vertical_map)
        cls = classify_vertical(vertical, vmap)
        source = {
            "source": AUDIENCE_FROM_OPERATOR if a.audience else cls.source,
            "given": cls.given,
            "matched_vertical": cls.vertical,
            "map_audience": cls.audience,
            "map_local": cls.local,
            "note": ("--audience %s given; the map says %s" % (a.audience, cls.audience)
                     if a.audience else cls.note),
            "map_version": vmap["map_version"],
            "map_sha256": vmap_digest,
        }
        profile = StudyProfile(
            audience=a.audience or cls.audience, vertical=cls.vertical,
            local=a.local or cls.local, web_search=a.search,
            requested=tuple(a.request), declared=_pairs(a.declare, "--declare"),
            model_overrides=_pairs(a.model, "--model"),
        )
        plan = build_plan(profile, policy, digest, audience_source=source)
    except SelectionError as ex:
        sys.exit("REFUSE: %s" % ex)

    print(render_plan(plan))

    stamp = datetime.now(timezone.utc)
    plan["planned_at"] = stamp.isoformat()
    date = stamp.strftime("%Y%m%d")

    commands = []
    if a.bank:
        tag = a.tag or Path(a.bank).stem
        try:
            commands = runner_commands(plan, bank=a.bank, runs=a.runs, outdir=a.outdir, tag=tag,
                                       date=date, python=sys.executable, smoke=a.smoke)
        except SelectionError as ex:
            sys.exit("REFUSE: %s" % ex)
        plan["commands"] = commands
        print("\nCOMMANDS (%s)" % ("EXECUTE" if a.execute else "dry run - nothing called"))
        for c in commands:
            print("  " + subprocess.list2cmdline(c))

    plan_path = a.plan_out
    if a.execute and not plan_path:
        prefix = "SMOKE_" if a.smoke else ""
        plan_path = "%s/%sengine_plan_%s_%s.json" % (a.outdir.rstrip("/"), prefix, tag, date)
    if plan_path:
        _write_new(plan_path, plan)

    if not a.execute:
        return 0

    for c in commands:
        print("\nRUN %s" % subprocess.list2cmdline(c), flush=True)
        code = subprocess.run(c, check=False).returncode
        if code != 0:
            print("STOP: exit %d from engine %s. Later engines were NOT run." % (
                code, c[c.index("--engine") + 1]))
            return code
    print("\nDONE %d engine run(s). Skipped by policy: %s" % (
        len(commands), ", ".join(plan["skipped"]) or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
