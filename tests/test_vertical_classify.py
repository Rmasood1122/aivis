"""Vertical classifier - any business name resolves to an audience, with the model's
answer kept as evidence. The model call is always a fake here: no network, no keys."""
import hashlib
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aivis import engine_select as es
from aivis import vertical_classify as vc

ROOT = Path(__file__).resolve().parents[1]
FIXED_NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def vmap():
    return es.load_vertical_map(ROOT / "config" / "vertical_map_v1.json")[0]


class FakeCall:
    """Stands in for the model. Counts calls so 'no call made' is provable."""

    def __init__(self, answer, model="fake-model-1"):
        self.answer, self.model, self.prompts = answer, model, []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer, self.model


def _resolve(name, vmap, ledger, call):
    return vc.resolve_vertical(name, vmap, ledger_path=ledger, call=call, now=lambda: FIXED_NOW)


# ---------------------------------------------------------------------------
# ORDER: map -> ledger -> one call -> fallback
# ---------------------------------------------------------------------------

def test_listed_vertical_never_reaches_the_model(vmap, tmp_path):
    call = FakeCall('{"audience": "b2b", "local": false}')
    c = _resolve("restaurants", vmap, tmp_path / "l.jsonl", call)
    assert c.source == es.AUDIENCE_FROM_MAP and c.audience == "b2c"
    assert call.prompts == []
    assert not (tmp_path / "l.jsonl").exists()


def test_unlisted_business_is_classified_and_recorded(vmap, tmp_path):
    ledger = tmp_path / "state" / "l.jsonl"
    answer = '{"audience": "b2c", "local": true}'
    call = FakeCall(answer)
    c = _resolve("Wedding Photographers", vmap, ledger, call)
    assert (c.source, c.audience, c.local) == (vc.AUDIENCE_FROM_CLASSIFIER, "b2c", True)
    assert c.vertical == "wedding_photographers"
    assert "not operator-reviewed" in c.note
    assert len(call.prompts) == 1 and '"Wedding Photographers"' in call.prompts[0]

    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["response_text"] == answer
    assert row["sha256"] == hashlib.sha256(answer.encode()).hexdigest()
    assert row["prompt_sha256"] == hashlib.sha256(call.prompts[0].encode()).hexdigest()
    assert (row["name"], row["classifier_model"], row["ts"]) == (
        "wedding_photographers", "fake-model-1", FIXED_NOW.isoformat())
    assert c.record["response_sha256"] == row["sha256"]


def test_second_ask_reads_the_ledger_and_makes_no_call(vmap, tmp_path):
    ledger = tmp_path / "l.jsonl"
    first = _resolve("wedding photographers", vmap, ledger,
                     FakeCall('{"audience":"b2c","local":true}'))
    again = FakeCall('{"audience": "b2b", "local": false}')  # a different answer, never used
    second = _resolve("Wedding-Photographers", vmap, ledger, again)
    assert again.prompts == []
    assert (second.audience, second.local) == (first.audience, first.local) == ("b2c", True)
    assert "from the ledger, no call made" in second.note
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 1


def test_ledger_is_used_even_when_the_classifier_is_off(vmap, tmp_path):
    ledger = tmp_path / "l.jsonl"
    _resolve("escape rooms", vmap, ledger, FakeCall('{"audience":"b2c","local":true}'))
    c = _resolve("escape rooms", vmap, ledger, None)
    assert c.source == vc.AUDIENCE_FROM_CLASSIFIER and c.audience == "b2c"


@pytest.mark.parametrize(("answer", "audience", "local"), [
    ('{"audience": "b2b", "local": false}', "b2b", False),
    ('{"audience": "mixed", "local": true}', "mixed", True),
    ('```json\n{"audience": "b2c", "local": false}\n```', "b2c", False),
    ('Here it is: {"local": true, "audience": "b2c"} hope that helps', "b2c", True),
])
def test_readable_answers(vmap, tmp_path, answer, audience, local):
    c = _resolve("some new business", vmap, tmp_path / "l.jsonl", FakeCall(answer))
    assert (c.source, c.audience, c.local) == (vc.AUDIENCE_FROM_CLASSIFIER, audience, local)


# ---------------------------------------------------------------------------
# FALLBACK - never guessed into b2c or b2b
# ---------------------------------------------------------------------------

def _assert_fallback(c, vmap):
    assert c.source == es.AUDIENCE_UNCLASSIFIED
    assert c.audience == vmap["unclassified"]["audience"] == "mixed"


def test_classifier_off_falls_back(vmap, tmp_path):
    c = _resolve("wedding photographers", vmap, tmp_path / "l.jsonl", None)
    _assert_fallback(c, vmap)
    assert "Classifier is off" in c.note


def test_failed_call_falls_back_says_why_and_writes_nothing(vmap, tmp_path):
    ledger = tmp_path / "l.jsonl"
    c = _resolve("wedding photographers", vmap, ledger,
                 FakeCall(RuntimeError("ANTHROPIC_API_KEY not set. Add it to .env")))
    _assert_fallback(c, vmap)
    assert "Classifier call failed: ANTHROPIC_API_KEY not set" in c.note
    assert not ledger.exists()


@pytest.mark.parametrize("answer", [
    "I think this is a consumer business.",
    '{"audience": "consumer", "local": true}',
    '{"audience": "b2c", "local": "yes"}',
    '{"audience": "b2c"}',
    "{not json}",
    "",
])
def test_unreadable_answer_falls_back_and_writes_nothing(vmap, tmp_path, answer):
    ledger = tmp_path / "l.jsonl"
    c = _resolve("wedding photographers", vmap, ledger, FakeCall(answer))
    _assert_fallback(c, vmap)
    assert "Classifier answer unreadable" in c.note
    assert not ledger.exists()


def test_unknown_answer_falls_back_but_is_recorded_so_it_is_not_asked_twice(vmap, tmp_path):
    ledger = tmp_path / "l.jsonl"
    c = _resolve("asdf qwerty", vmap, ledger, FakeCall('{"audience": "unknown", "local": false}'))
    _assert_fallback(c, vmap)
    assert 'answered "unknown"' in c.note and c.record is not None
    again = FakeCall('{"audience": "b2c", "local": false}')
    c2 = _resolve("asdf qwerty", vmap, ledger, again)
    _assert_fallback(c2, vmap)
    assert again.prompts == []


def test_empty_name_refuses(vmap, tmp_path):
    with pytest.raises(es.SelectionError, match="vertical is empty"):
        _resolve("   ", vmap, tmp_path / "l.jsonl", FakeCall("{}"))


# ---------------------------------------------------------------------------
# LEDGER INTEGRITY - a row must match its own stored response
# ---------------------------------------------------------------------------

def _seed(vmap, ledger):
    _resolve("wedding photographers", vmap, ledger, FakeCall('{"audience":"b2c","local":true}'))
    return json.loads(ledger.read_text(encoding="utf-8"))


def test_edited_audience_is_refused(vmap, tmp_path):
    ledger = tmp_path / "l.jsonl"
    row = _seed(vmap, ledger)
    row["audience"] = "b2b"  # flipped by hand; the stored response still says b2c
    ledger.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(es.SelectionError, match="differ from the stored response"):
        _resolve("wedding photographers", vmap, ledger, None)


def test_edited_response_text_is_refused(vmap, tmp_path):
    ledger = tmp_path / "l.jsonl"
    row = _seed(vmap, ledger)
    row["response_text"] = '{"audience":"b2b","local":true}'
    row["audience"] = "b2b"
    ledger.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(es.SelectionError, match="sha256 does not match"):
        vc.read_ledger(ledger)


def test_first_row_wins_and_blank_lines_are_ignored(vmap, tmp_path):
    ledger = tmp_path / "l.jsonl"
    first = _seed(vmap, ledger)
    later = dict(first, response_text='{"audience":"b2b","local":false}', audience="b2b",
                 local=False)
    later["sha256"] = hashlib.sha256(later["response_text"].encode()).hexdigest()
    with ledger.open("a", encoding="utf-8") as f:
        f.write("\n" + json.dumps(later) + "\n")
    assert vc.read_ledger(ledger)["wedding_photographers"]["audience"] == "b2c"


def test_missing_ledger_is_empty(tmp_path):
    assert vc.read_ledger(tmp_path / "nope.jsonl") == {}


# ---------------------------------------------------------------------------
# PROMPT + LIVE-CALL ADAPTER
# ---------------------------------------------------------------------------

def test_prompt_names_the_business_and_the_allowed_answers():
    p = vc.build_prompt('  Bob\'s "Best" Tacos ')
    assert "Business: \"Bob's 'Best' Tacos\"" in p  # quotes cannot break out of the field
    for word in vc.ANSWERS:
        assert f'"{word}"' in p


def test_default_call_goes_through_the_existing_engine_adapter(monkeypatch):
    from aivis import engines

    seen = {}

    def fake_run_once_on(engine, prompt, *, max_tokens):
        seen.update(engine=engine, prompt=prompt, max_tokens=max_tokens)
        return engines.RunResult(raw_text="{}", raw_json=None, request_payload={},
                                 model_version_hint="claude-x")

    monkeypatch.setattr(engines, "run_once_on", fake_run_once_on)
    assert vc.default_call("anthropic")("the prompt") == ("{}", "claude-x")
    assert seen == {"engine": "anthropic", "prompt": "the prompt", "max_tokens": 100}


def test_default_call_falls_back_to_the_registry_model_when_no_hint(monkeypatch):
    from aivis import engines

    monkeypatch.setattr(
        engines, "run_once_on",
        lambda engine, prompt, *, max_tokens: engines.RunResult("{}", None, {}),
    )
    assert vc.default_call("anthropic")("p")[1] == engines.ENGINES["anthropic"].default_model


def test_default_call_without_a_key_raises_so_resolve_can_fall_back(vmap, tmp_path):
    # conftest nulls every key: the real adapter must refuse, and resolve must report it
    c = _resolve("wedding photographers", vmap, tmp_path / "l.jsonl", vc.default_call())
    _assert_fallback(c, vmap)
    assert "ANTHROPIC_API_KEY not set" in c.note


# ---------------------------------------------------------------------------
# CLI in-process, with an injected classifier
# ---------------------------------------------------------------------------

def _main():
    spec = importlib.util.spec_from_file_location("run_study_v1", ROOT / "run_study_v1.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main


def test_cli_any_business_picks_engines_from_the_model_answer(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("AIVIS_NO_CLASSIFY", raising=False)
    ledger, plan_path = tmp_path / "l.jsonl", tmp_path / "plan.json"
    call = FakeCall('{"audience": "b2c", "local": true}')
    code = _main()(["wedding photographers", "--ledger", str(ledger),
                    "--plan-out", str(plan_path)], classifier_call=call)
    out = capsys.readouterr().out
    assert code == 0
    assert "audience from MODEL_CLASSIFIED" in out
    assert "RUN 3: openai, gemini, anthropic" in out and "SKIP 1: perplexity" in out
    assert "WARNING" not in out
    src = json.loads(plan_path.read_text(encoding="utf-8"))["audience_source"]
    assert src["source"] == vc.AUDIENCE_FROM_CLASSIFIER
    assert src["classifier"]["response_sha256"] == hashlib.sha256(call.answer.encode()).hexdigest()


def test_cli_b2b_answer_plans_all_four(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("AIVIS_NO_CLASSIFY", raising=False)
    call = FakeCall('{"audience": "b2b", "local": false}')
    assert _main()(["restaurant equipment suppliers", "--ledger", str(tmp_path / "l.jsonl")],
                   classifier_call=call) == 0
    assert "RUN 4: openai, gemini, anthropic, perplexity" in capsys.readouterr().out


@pytest.mark.parametrize("extra", [["--no-classify"], ["--audience", "b2c"]])
def test_cli_flags_that_must_prevent_the_call(tmp_path, capsys, monkeypatch, extra):
    monkeypatch.delenv("AIVIS_NO_CLASSIFY", raising=False)
    call = FakeCall('{"audience": "b2b", "local": false}')
    assert _main()(["wedding photographers", "--ledger", str(tmp_path / "l.jsonl"), *extra],
                   classifier_call=call) == 0
    assert call.prompts == []
    capsys.readouterr()


def test_cli_env_switch_prevents_the_call(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("AIVIS_NO_CLASSIFY", "1")
    call = FakeCall('{"audience": "b2b", "local": false}')
    assert _main()(["wedding photographers", "--ledger", str(tmp_path / "l.jsonl")],
                   classifier_call=call) == 0
    assert call.prompts == []
    assert "WARNING: unclassified vertical" in capsys.readouterr().out
