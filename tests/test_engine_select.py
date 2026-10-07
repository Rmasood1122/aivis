"""Engine selection - policy contract, fail-closed refusals, and the no-drift pins.

No network. The CLI tests run run_study_v1.py as a dry run only.
"""
import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from aivis import engine_select as es

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "engine_policy_v1.json"
SCRIPT = ROOT / "run_study_v1.py"


@pytest.fixture(scope="module")
def loaded():
    return es.load_policy(POLICY_PATH)


@pytest.fixture()
def policy(loaded):
    return copy.deepcopy(loaded[0])


def _by_surface(profile, policy):
    return {d.surface: d for d in es.select_engines(profile, policy)}


def _runner_module():
    spec = importlib.util.spec_from_file_location("run_bank_multi_v2", ROOT / "run_bank_multi_v2.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# THE RULE - Perplexity does not run on a consumer study unless a condition holds
# ---------------------------------------------------------------------------

def test_b2c_restaurants_skips_perplexity_and_runs_chatgpt_and_gemini(policy):
    d = _by_surface(es.StudyProfile("b2c", "restaurants", local=True), policy)
    assert d["perplexity"].decision == es.SKIP
    assert d["perplexity"].reason_code == es.CONDITION_NOT_MET
    assert d["perplexity"].model is None  # a skipped engine carries nothing to call
    assert d["openai"].decision == es.RUN and d["openai"].reason_code == es.AUDIENCE_CORE
    assert d["gemini"].decision == es.RUN and d["gemini"].reason_code == es.AUDIENCE_CORE
    assert d["anthropic"].decision == es.SKIP


def test_b2b_runs_all_four_engines(policy):
    d = _by_surface(es.StudyProfile("b2b", "pr_agencies"), policy)
    for engine in ("openai", "gemini", "anthropic", "perplexity"):
        assert d[engine].decision == es.RUN
        assert d[engine].reason_code == es.AUDIENCE_CORE


def test_mixed_audience_takes_core_from_either_side(policy):
    d = _by_surface(es.StudyProfile("mixed", "real_estate"), policy)
    assert d["perplexity"].decision == es.RUN
    assert d["perplexity"].tier == "core"


def test_b2c_relevant_vertical_admits_perplexity(policy):
    d = _by_surface(es.StudyProfile("b2c", "Personal Finance"), policy)
    assert d["perplexity"].decision == es.RUN
    assert d["perplexity"].reason_code == es.VERTICAL_RELEVANT
    assert d["anthropic"].decision == es.SKIP  # the list is per engine


def test_b2c_client_request_admits_perplexity(policy):
    d = _by_surface(es.StudyProfile("b2c", "restaurants", requested=("perplexity",)), policy)
    assert d["perplexity"].decision == es.RUN
    assert d["perplexity"].reason_code == es.CLIENT_REQUESTED


def test_b2c_operator_declaration_admits_perplexity_and_records_the_reason(policy):
    why = "buyer's diners are finance-district analysts"
    d = _by_surface(
        es.StudyProfile("b2c", "restaurants", declared=(("perplexity", why),)), policy
    )
    assert d["perplexity"].decision == es.RUN
    assert d["perplexity"].reason_code == es.OPERATOR_DECLARED
    assert why in d["perplexity"].reason


def test_request_outranks_declaration_outranks_vertical(policy):
    p = es.StudyProfile("b2c", "investing", requested=("perplexity",),
                        declared=(("perplexity", "a long enough reason"),))
    assert _by_surface(p, policy)["perplexity"].reason_code == es.CLIENT_REQUESTED
    p = es.StudyProfile("b2c", "investing", declared=(("perplexity", "a long enough reason"),))
    assert _by_surface(p, policy)["perplexity"].reason_code == es.OPERATOR_DECLARED


# ---------------------------------------------------------------------------
# FAIL CLOSED - no silent defaults
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("audience", ["", "consumer", "B2C", "all"])
def test_unknown_audience_refuses(policy, audience):
    with pytest.raises(es.SelectionError, match="unknown audience"):
        es.select_engines(es.StudyProfile(audience, "restaurants"), policy)


def test_empty_vertical_refuses(policy):
    with pytest.raises(es.SelectionError, match="vertical is empty"):
        es.select_engines(es.StudyProfile("b2c", "  "), policy)


def test_declared_relevance_without_a_real_reason_refuses(policy):
    with pytest.raises(es.SelectionError, match="written reason"):
        es.select_engines(
            es.StudyProfile("b2c", "restaurants", declared=(("perplexity", "yes"),)), policy
        )


def test_requesting_an_engine_outside_the_policy_refuses(policy):
    with pytest.raises(es.SelectionError, match="not in the policy"):
        es.select_engines(es.StudyProfile("b2c", "restaurants", requested=("bing",)), policy)


@pytest.mark.parametrize("surface", ["grok", "meta_ai", "google_ai_mode", "copilot"])
def test_requesting_a_surface_with_no_adapter_refuses_with_its_reason(policy, surface):
    with pytest.raises(es.SelectionError, match="cannot be measured"):
        es.select_engines(es.StudyProfile("b2c", "restaurants", requested=(surface,)), policy)


def test_policy_missing_a_tier_refuses(policy):
    del policy["engines"]["gemini"]["tier"]["b2b"]
    with pytest.raises(es.SelectionError, match="tier for 'b2b'"):
        es.validate_policy(policy)


def test_policy_with_a_surface_in_both_lists_refuses(policy):
    policy["unmeasured_surfaces"]["openai"] = {"label": "x", "reason_code": "x", "reason": "x"}
    with pytest.raises(es.SelectionError, match="both engine and unmeasured"):
        es.validate_policy(policy)


def test_search_off_for_perplexity_is_never_planned(policy):
    # Perplexity retrieves live whatever is asked; the plan must say so.
    d = _by_surface(es.StudyProfile("b2b", "pr_agencies", web_search=False), policy)
    assert d["perplexity"].web_search is True
    assert d["openai"].web_search is False


# ---------------------------------------------------------------------------
# EVERY SURFACE IS ACCOUNTED FOR
# ---------------------------------------------------------------------------

def test_every_policy_surface_gets_exactly_one_row(policy):
    decisions = es.select_engines(es.StudyProfile("b2c", "restaurants"), policy)
    surfaces = [d.surface for d in decisions]
    assert len(surfaces) == len(set(surfaces))
    assert set(surfaces) == set(policy["engines"]) | set(policy["unmeasured_surfaces"])
    assert all(d.reason_code and d.reason for d in decisions)


def test_unmeasured_surfaces_are_never_run(policy):
    for audience in ("b2c", "b2b", "mixed"):
        d = _by_surface(es.StudyProfile(audience, "restaurants"), policy)
        for surface in policy["unmeasured_surfaces"]:
            assert d[surface].decision == es.NOT_MEASURED


# ---------------------------------------------------------------------------
# WEB SEARCH
# ---------------------------------------------------------------------------

def test_web_search_resolution_order(policy):
    assert es.resolve_web_search(es.StudyProfile("b2b", "x"), policy)[0] is False
    assert es.resolve_web_search(es.StudyProfile("b2c", "x"), policy)[0] is True
    assert es.resolve_web_search(es.StudyProfile("b2b", "x", local=True), policy)[0] is True
    on, why = es.resolve_web_search(es.StudyProfile("b2c", "x", local=True, web_search=False),
                                    policy)
    assert on is False and why == "set by operator"


# ---------------------------------------------------------------------------
# DETERMINISM + PLAN SHAPE
# ---------------------------------------------------------------------------

def test_same_profile_same_policy_same_plan(loaded):
    policy, digest = loaded
    p = es.StudyProfile("b2c", "restaurants", local=True)
    assert es.build_plan(p, policy, digest) == es.build_plan(p, policy, digest)


def test_plan_binds_the_policy_bytes(loaded):
    import hashlib

    policy, digest = loaded
    assert digest == hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest()
    plan = es.build_plan(es.StudyProfile("b2c", "restaurants", local=True), policy, digest)
    assert plan["policy_sha256"] == digest
    assert plan["run"] == ["openai", "gemini"]
    assert plan["skipped"] == ["anthropic", "perplexity"]
    assert json.loads(json.dumps(plan)) == plan  # JSON-serialisable as is


# ---------------------------------------------------------------------------
# ENFORCEMENT - a skipped engine has no command
# ---------------------------------------------------------------------------

def _commands(policy, digest, profile, **kw):
    plan = es.build_plan(profile, policy, digest)
    args = {"bank": "bank.jsonl", "runs": 5, "outdir": "out/", "tag": "t", "date": "20261007"}
    args.update(kw)
    return es.runner_commands(plan, **args)


def test_no_command_is_built_for_a_skipped_engine(loaded):
    policy, digest = loaded
    cmds = _commands(policy, digest, es.StudyProfile("b2c", "restaurants", local=True))
    engines = [c[c.index("--engine") + 1] for c in cmds]
    assert engines == ["openai", "gemini"]
    assert not any("perplexity" in part for c in cmds for part in c)


def test_command_shape_matches_the_runner_cli(loaded):
    policy, digest = loaded
    cmds = _commands(policy, digest, es.StudyProfile("b2b", "pr_agencies", web_search=True))
    runner = _runner_module()
    by_engine = {c[c.index("--engine") + 1]: c for c in cmds}
    assert set(by_engine) == set(runner.ENGINES)
    assert "--search" in by_engine["openai"]
    assert "--search" not in by_engine["perplexity"]  # runner forces it on for Perplexity
    assert by_engine["gemini"][by_engine["gemini"].index("--out") + 1] == (
        "out/multi_gemini_t_20261007.jsonl"
    )


def test_smoke_commands_are_marked_and_kept_apart_from_measured_files(loaded):
    policy, digest = loaded
    cmds = _commands(policy, digest, es.StudyProfile("b2c", "restaurants"), smoke=True)
    for c in cmds:
        assert c[-1] == "--smoke"
        assert "/SMOKE_multi_" in c[c.index("--out") + 1]


def test_zero_runs_refuses(loaded):
    policy, digest = loaded
    with pytest.raises(es.SelectionError, match="at least 1"):
        _commands(policy, digest, es.StudyProfile("b2c", "restaurants"), runs=0)


# ---------------------------------------------------------------------------
# NO-DRIFT PINS (B7 class) - the policy may not disagree with the repo
# ---------------------------------------------------------------------------

def test_policy_engines_are_exactly_the_runner_engines(policy):
    assert set(policy["engines"]) == set(_runner_module().ENGINES)


def test_every_recorded_model_id_is_present_in_its_committed_evidence(policy):
    """Model ids are read from evidence rows, never typed from memory."""
    checked = 0
    for engine in policy["engines"]:
        for mode in ("search_on", "search_off"):
            entry = policy["models"][engine].get(mode)
            if entry is None:
                continue
            path = ROOT / entry["evidence"]
            assert path.exists(), f"{engine}/{mode}: evidence file missing: {entry['evidence']}"
            models = set()
            for line in path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                if row.get("engine") == engine and "error" not in row:
                    models.add(row["request_payload"]["model"])
            assert models == {entry["model"]}, f"{engine}/{mode}: evidence has {models}"
            checked += 1
    assert checked == 7  # 3 engines x 2 modes + Perplexity search_on


def test_override_model_is_flagged_as_unevidenced(policy):
    p = es.StudyProfile("b2c", "restaurants", model_overrides=(("openai", "some-new-id"),))
    d = _by_surface(p, policy)["openai"]
    assert d.model == "some-new-id"
    assert d.model_evidence is None
    assert "Confirm with --smoke" in d.model_caveat


def test_every_usage_figure_in_the_policy_carries_a_source_and_a_date(policy):
    for e in policy["evidence"]:
        assert e["tag"] == "REPORTED"
        assert e["url"].startswith("https://")
        assert e["retrieved"] and e["route"] and e["claim"]


# ---------------------------------------------------------------------------
# CLI - dry run only
# ---------------------------------------------------------------------------

def _cli(*args, cwd=ROOT):
    # AIVIS_NO_CLASSIFY: a subprocess reads the real .env, so the classifier is switched off
    # here. No test may reach a live model (2026-09-05 key incident class).
    env = {**os.environ, "AIVIS_NO_CLASSIFY": "1"}
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                          cwd=cwd, check=False, env=env)


def test_cli_plan_only_prints_every_surface():
    r = _cli("--audience", "b2c", "--vertical", "restaurants", "--local")
    assert r.returncode == 0, r.stderr
    assert "SKIP         perplexity" in r.stdout
    assert "RUN          openai" in r.stdout
    assert "NOT_MEASURED google_ai_mode" in r.stdout
    assert "COMMANDS" not in r.stdout


def test_cli_dry_run_calls_nothing_and_writes_nothing(tmp_path):
    out = tmp_path / "runs"
    r = _cli("--audience", "b2c", "--vertical", "restaurants", "--local",
             "--bank", "bank.jsonl", "--outdir", str(out))
    assert r.returncode == 0, r.stderr
    assert "dry run - nothing called" in r.stdout
    assert "--engine openai" in r.stdout and "--engine perplexity" not in r.stdout
    assert not out.exists()


def test_cli_refuses_unknown_audience():
    r = _cli("--audience", "everyone", "--vertical", "restaurants")
    assert r.returncode != 0
    assert "REFUSE: unknown audience" in r.stderr


def test_cli_refuses_to_overwrite_a_plan(tmp_path):
    target = tmp_path / "plan.json"
    args = ("--audience", "b2b", "--vertical", "pr_agencies", "--plan-out", str(target))
    assert _cli(*args).returncode == 0
    first = target.read_bytes()
    r = _cli(*args)
    assert r.returncode != 0 and "REFUSE" in r.stderr
    assert target.read_bytes() == first


def test_cli_execute_refuses_outside_the_repo_root(tmp_path):
    r = _cli("--audience", "b2c", "--vertical", "restaurants", "--bank", "bank.jsonl",
             "--outdir", str(tmp_path / "runs"), "--execute", cwd=tmp_path)
    assert r.returncode != 0
    assert "repo root" in r.stderr


# ---------------------------------------------------------------------------
# CLI --execute against a STUB runner (no network, no keys)
# ---------------------------------------------------------------------------

STUB_RUNNER = """\
import json, sys
from pathlib import Path
args = sys.argv[1:]
engine = args[args.index("--engine") + 1]
with open("calls.log", "a", encoding="utf-8") as f:
    f.write(json.dumps(args) + "\\n")
fail = Path("fail_on.txt")
sys.exit(2 if fail.exists() and fail.read_text().strip() == engine else 0)
"""


def _stub_repo(tmp_path):
    (tmp_path / "run_bank_multi_v2.py").write_text(STUB_RUNNER, encoding="utf-8")
    return tmp_path


def _calls(repo):
    log = repo / "calls.log"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]


def test_execute_calls_only_the_picked_engines_and_files_the_plan(tmp_path):
    repo = _stub_repo(tmp_path)
    r = _cli("--audience", "b2c", "--vertical", "restaurants", "--local", "--bank", "bank.jsonl",
             "--outdir", "runs", "--tag", "nyc", "--execute", cwd=repo)
    assert r.returncode == 0, r.stdout + r.stderr
    called = [c[c.index("--engine") + 1] for c in _calls(repo)]
    assert called == ["openai", "gemini"]  # Perplexity and Claude were never invoked
    plans = list((repo / "runs").glob("engine_plan_nyc_*.json"))
    assert len(plans) == 1
    plan = json.loads(plans[0].read_text(encoding="utf-8"))
    assert plan["skipped"] == ["anthropic", "perplexity"]
    assert plan["planned_at"] and len(plan["commands"]) == 2


def test_execute_stops_on_first_failure_and_reports_it(tmp_path):
    repo = _stub_repo(tmp_path)
    (repo / "fail_on.txt").write_text("openai", encoding="utf-8")
    r = _cli("--audience", "b2c", "--vertical", "restaurants", "--bank", "bank.jsonl",
             "--outdir", "runs", "--execute", cwd=repo)
    assert r.returncode == 2  # the runner's exit code, not swallowed
    assert "STOP: exit 2 from engine openai" in r.stdout
    assert [c[c.index("--engine") + 1] for c in _calls(repo)] == ["openai"]


def test_execute_with_a_declared_reason_does_call_perplexity(tmp_path):
    repo = _stub_repo(tmp_path)
    r = _cli("--audience", "b2c", "--vertical", "restaurants", "--bank", "bank.jsonl",
             "--outdir", "runs", "--declare", "perplexity=buyer asked for a citation ledger",
             "--execute", cwd=repo)
    assert r.returncode == 0, r.stdout + r.stderr
    assert [c[c.index("--engine") + 1] for c in _calls(repo)] == ["openai", "gemini", "perplexity"]


# ---------------------------------------------------------------------------
# REMAINING REFUSALS + the rendered plan
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", ["policy_version", "engines", "unmeasured_surfaces",
                                 "web_search_default", "models", "declared_reason_min_chars"])
def test_policy_missing_a_top_level_key_refuses(policy, key):
    del policy[key]
    with pytest.raises(es.SelectionError, match=f"missing '{key}'"):
        es.validate_policy(policy)


def test_policy_with_no_engines_refuses(policy):
    policy["engines"] = {}
    with pytest.raises(es.SelectionError, match="lists no engines"):
        es.validate_policy(policy)


def test_policy_engine_without_relevant_verticals_list_refuses(policy):
    policy["engines"]["openai"]["relevant_verticals"] = None
    with pytest.raises(es.SelectionError, match="relevant_verticals must be a list"):
        es.validate_policy(policy)


def test_policy_engine_without_a_models_entry_refuses(policy):
    del policy["models"]["gemini"]
    with pytest.raises(es.SelectionError, match="no entry under models"):
        es.validate_policy(policy)


def test_policy_unmeasured_surface_without_a_reason_refuses(policy):
    policy["unmeasured_surfaces"]["grok"]["reason"] = ""
    with pytest.raises(es.SelectionError, match="missing 'reason'"):
        es.validate_policy(policy)


def test_policy_without_a_search_default_refuses(policy):
    del policy["web_search_default"]["mixed"]
    with pytest.raises(es.SelectionError, match="no boolean for 'mixed'"):
        es.validate_policy(policy)


def test_missing_model_for_a_search_mode_refuses_instead_of_guessing(policy):
    del policy["models"]["openai"]["search_off"]
    with pytest.raises(es.SelectionError, match="no search_off model for 'openai'"):
        es.select_engines(es.StudyProfile("b2b", "pr_agencies"), policy)


def test_rendered_plan_shows_every_surface_and_the_openai_search_caveat(loaded):
    policy, digest = loaded
    plan = es.build_plan(es.StudyProfile("b2c", "restaurants", local=True), policy, digest)
    text = es.render_plan(plan)
    for surface in (*policy["engines"], *policy["unmeasured_surfaces"]):
        assert surface in text
    assert digest[:12] in text
    assert "CAVEAT: This is the RESOLVED snapshot" in text
    assert "RUN 2: openai, gemini" in text
    assert "SKIP 2: anthropic, perplexity" in text


# ---------------------------------------------------------------------------
# VERTICAL MAP - the audience comes from the vertical name
# ---------------------------------------------------------------------------

VMAP_PATH = ROOT / "config" / "vertical_map_v1.json"


@pytest.fixture(scope="module")
def vloaded():
    return es.load_vertical_map(VMAP_PATH)


@pytest.fixture()
def vmap(vloaded):
    return copy.deepcopy(vloaded[0])


@pytest.mark.parametrize(("typed", "key", "audience", "local"), [
    ("restaurants", "restaurants", "b2c", True),
    ("law firms", "law_firms", "mixed", True),
    ("retail", "retail", "b2c", False),
    ("fashion", "fashion", "b2c", False),
    ("PR agencies", "pr_agencies", "b2b", False),
    ("Law Firm", "law_firms", "mixed", True),  # case + singular
    ("nail salon", "salons", "b2c", True),  # singular of an alias
    ("real-estate", "real_estate", "b2c", True),  # hyphen
    ("personal injury lawyers", "personal_injury_law", "b2c", True),
    ("stocks", "investing", "b2c", False),  # alias onto a Perplexity-relevant key
])
def test_named_verticals_classify(vmap, typed, key, audience, local):
    c = es.classify_vertical(typed, vmap)
    assert (c.vertical, c.audience, c.local) == (key, audience, local)
    assert c.source == es.AUDIENCE_FROM_MAP
    assert c.given == typed


def test_no_substring_matching_lawn_care_is_not_law(vmap):
    assert es.classify_vertical("lawn care", vmap).vertical == "home_services"
    assert es.classify_vertical("law", vmap).source == es.AUDIENCE_UNCLASSIFIED


def test_unlisted_vertical_takes_the_declared_fallback_and_says_so(vmap):
    c = es.classify_vertical("underwater basket weaving", vmap)
    assert c.source == es.AUDIENCE_UNCLASSIFIED
    assert c.audience == vmap["unclassified"]["audience"] == "mixed"
    assert c.vertical == "underwater_basket_weaving"
    assert "not in vertical_map_v1" in c.note


def test_empty_vertical_name_refuses_in_the_classifier(vmap):
    with pytest.raises(es.SelectionError, match="vertical is empty"):
        es.classify_vertical("  ", vmap)


def test_the_rule_holds_for_every_row_of_the_map(vmap, policy):
    """Across the whole map: a b2c vertical never plans Perplexity unless it is on
    Perplexity's relevant list, and every b2b or mixed vertical plans all engines."""
    relevant = set(policy["engines"]["perplexity"]["relevant_verticals"])
    seen = {"b2c": 0, "b2b": 0, "mixed": 0}
    for key in vmap["verticals"]:
        c = es.classify_vertical(key, vmap)
        d = _by_surface(es.StudyProfile(c.audience, c.vertical, local=c.local), policy)
        seen[c.audience] += 1
        if c.audience == "b2c":
            want = es.RUN if key in relevant else es.SKIP
            assert d["perplexity"].decision == want, key
            assert d["openai"].decision == d["gemini"].decision == es.RUN
        else:
            assert all(d[e].decision == es.RUN for e in policy["engines"]), key
    assert all(seen.values())  # each audience is exercised by at least one row


def test_every_relevant_vertical_in_the_policy_is_a_key_of_the_map(vmap, policy):
    # otherwise a relevant_verticals entry could never be reached by name (B7 class)
    for engine, spec in policy["engines"].items():
        for vertical in spec["relevant_verticals"]:
            assert vertical in vmap["verticals"], f"{engine}: {vertical}"


def test_map_alias_pointing_at_two_verticals_refuses(vmap):
    vmap["verticals"]["retail"]["aliases"].append("cafes")
    with pytest.raises(es.SelectionError, match="points at both"):
        es.validate_vertical_map(vmap)


@pytest.mark.parametrize("key", ["map_version", "verticals", "unclassified"])
def test_map_missing_a_top_level_key_refuses(vmap, key):
    del vmap[key]
    with pytest.raises(es.SelectionError, match=f"missing '{key}'"):
        es.validate_vertical_map(vmap)


def test_map_row_with_a_bad_audience_refuses(vmap):
    vmap["verticals"]["retail"]["audience"] = "consumer"
    with pytest.raises(es.SelectionError, match="has audience 'consumer'"):
        es.validate_vertical_map(vmap)


def test_map_row_without_boolean_local_refuses(vmap):
    vmap["unclassified"]["local"] = "no"
    with pytest.raises(es.SelectionError, match="no boolean 'local'"):
        es.validate_vertical_map(vmap)


def test_map_key_not_in_normalised_form_refuses(vmap):
    vmap["verticals"]["Law Firms"] = vmap["verticals"].pop("law_firms")
    with pytest.raises(es.SelectionError, match="not in normalised form"):
        es.validate_vertical_map(vmap)


def test_map_row_without_aliases_list_refuses(vmap):
    del vmap["verticals"]["retail"]["aliases"]
    with pytest.raises(es.SelectionError, match="no 'aliases' list"):
        es.validate_vertical_map(vmap)


def test_plan_defaults_to_operator_as_the_audience_source(loaded):
    policy, digest = loaded
    plan = es.build_plan(es.StudyProfile("b2c", "restaurants"), policy, digest)
    assert plan["audience_source"] == {"source": es.AUDIENCE_FROM_OPERATOR}
    assert "audience from OPERATOR" in es.render_plan(plan)


# ---------------------------------------------------------------------------
# CLI - one word is enough
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("typed", "run_line"), [
    ("restaurants", "RUN 2: openai, gemini"),
    ("fashion", "RUN 2: openai, gemini"),
    ("retail", "RUN 2: openai, gemini"),
    ("law firms", "RUN 4: openai, gemini, anthropic, perplexity"),
    ("pr agencies", "RUN 4: openai, gemini, anthropic, perplexity"),
])
def test_cli_vertical_alone_picks_the_engines(typed, run_line):
    r = _cli(typed)
    assert r.returncode == 0, r.stderr
    assert run_line in r.stdout
    assert "audience from VERTICAL_MAP" in r.stdout
    assert "WARNING" not in r.stdout


def test_cli_unlisted_vertical_warns_and_plans_every_engine():
    r = _cli("underwater basket weaving")
    assert r.returncode == 0, r.stderr
    assert "audience from VERTICAL_UNCLASSIFIED" in r.stdout
    assert "WARNING: unclassified vertical" in r.stdout
    assert "RUN 4: openai, gemini, anthropic, perplexity" in r.stdout


def test_cli_audience_flag_overrides_the_map_and_is_recorded(tmp_path):
    target = tmp_path / "plan.json"
    r = _cli("law firms", "--audience", "b2c", "--plan-out", str(target))
    assert r.returncode == 0, r.stderr
    assert "RUN 2: openai, gemini" in r.stdout
    src = json.loads(target.read_text(encoding="utf-8"))["audience_source"]
    assert src["source"] == es.AUDIENCE_FROM_OPERATOR
    assert src["map_audience"] == "mixed"  # what the map said is kept on the record


def test_cli_plan_binds_the_vertical_map_bytes(tmp_path):
    import hashlib

    target = tmp_path / "plan.json"
    assert _cli("restaurants", "--plan-out", str(target)).returncode == 0
    plan = json.loads(target.read_text(encoding="utf-8"))
    src = plan["audience_source"]
    assert src["map_sha256"] == hashlib.sha256(VMAP_PATH.read_bytes()).hexdigest()
    assert src["source"] == es.AUDIENCE_FROM_MAP and src["matched_vertical"] == "restaurants"
    assert plan["profile"]["local"] is True  # taken from the map, no --local flag given


def test_cli_without_a_vertical_refuses():
    r = _cli()
    assert r.returncode != 0 and "REFUSE: name the vertical" in r.stderr


def test_cli_two_different_verticals_refuses():
    r = _cli("restaurants", "--vertical", "retail")
    assert r.returncode != 0 and "two different verticals" in r.stderr


def test_execute_from_a_vertical_name_alone_never_calls_perplexity(tmp_path):
    repo = _stub_repo(tmp_path)
    r = _cli("restaurants", "--bank", "bank.jsonl", "--outdir", "runs", "--execute", cwd=repo)
    assert r.returncode == 0, r.stdout + r.stderr
    assert [c[c.index("--engine") + 1] for c in _calls(repo)] == ["openai", "gemini"]


def test_rendered_plan_warns_on_an_unclassified_vertical(loaded, vmap):
    policy, digest = loaded
    c = es.classify_vertical("underwater basket weaving", vmap)
    plan = es.build_plan(es.StudyProfile(c.audience, c.vertical, local=c.local), policy, digest,
                         audience_source={"source": c.source, "note": c.note})
    text = es.render_plan(plan)
    assert "audience from VERTICAL_UNCLASSIFIED" in text
    assert "WARNING: unclassified vertical - every engine is planned" in text


# ---------------------------------------------------------------------------
# ANSWER CAP - passed through so a study is not truncated at the runner default
# ---------------------------------------------------------------------------

def test_max_tokens_is_passed_to_every_command(loaded):
    policy, digest = loaded
    cmds = _commands(policy, digest, es.StudyProfile("b2b", "pr_agencies"), max_tokens=8192)
    assert len(cmds) == 4
    for c in cmds:
        assert c[c.index("--max-tokens") + 1] == "8192"


def test_max_tokens_none_leaves_the_runner_default(loaded):
    policy, digest = loaded
    cmds = _commands(policy, digest, es.StudyProfile("b2c", "restaurants"))
    assert not any("--max-tokens" in c for c in cmds)


def test_max_tokens_below_one_refuses(loaded):
    policy, digest = loaded
    with pytest.raises(es.SelectionError, match="max_tokens must be at least 1"):
        _commands(policy, digest, es.StudyProfile("b2c", "restaurants"), max_tokens=0)


def test_cli_default_cap_is_8192_and_reaches_the_runner(tmp_path):
    repo = _stub_repo(tmp_path)
    r = _cli("restaurants", "--bank", "bank.jsonl", "--outdir", "runs", "--execute", cwd=repo)
    assert r.returncode == 0, r.stdout + r.stderr
    for call in _calls(repo):
        assert call[call.index("--max-tokens") + 1] == "8192"
