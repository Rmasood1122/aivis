"""
Engine selection - which engines a study calls, and why.

ADDITIVE MODULE. Nothing in engines.py, runner.py or run_bank_multi_v2.py is
modified. This module decides; the existing runner still executes.

RULE (config/engine_policy_v1.json): an engine runs only when it is CORE for
the study audience, or CONDITIONAL with a condition met - the buyer asked for
it, the vertical is on the engine's relevant list, or the operator declared
relevance with a written reason. Perplexity is conditional for B2C, so a
consumer study does not call it unless one of those three holds.

DISCIPLINE:
  - Selection is a lookup. No model call, no clock, no randomness: the same
    profile and the same policy bytes give the same plan.
  - Fail closed. An unknown audience, an unknown engine, a surface with no
    adapter, or a declared relevance with no reason is an error, never a
    silent default.
  - Every surface in the policy gets a row: RUN, SKIP or NOT_MEASURED, each
    with a reason code. A skipped engine is printed, not hidden.
  - The plan carries the SHA-256 of the policy bytes that produced it.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

PLAN_SCHEMA = "engine_plan_v1"
BASE_AUDIENCES = ("b2c", "b2b")
TIERS = ("core", "conditional")

RUN = "RUN"
SKIP = "SKIP"
NOT_MEASURED = "NOT_MEASURED"

AUDIENCE_CORE = "AUDIENCE_CORE"
CLIENT_REQUESTED = "CLIENT_REQUESTED"
OPERATOR_DECLARED = "OPERATOR_DECLARED"
VERTICAL_RELEVANT = "VERTICAL_RELEVANT"
CONDITION_NOT_MET = "CONDITION_NOT_MET"

# where a study's audience came from
AUDIENCE_FROM_OPERATOR = "OPERATOR"
AUDIENCE_FROM_MAP = "VERTICAL_MAP"
AUDIENCE_UNCLASSIFIED = "VERTICAL_UNCLASSIFIED"


class SelectionError(ValueError):
    """Raised when a profile or a policy cannot produce an honest plan."""


@dataclass(frozen=True)
class StudyProfile:
    audience: str
    vertical: str
    local: bool = False
    web_search: bool | None = None  # None = policy default for the audience
    requested: tuple[str, ...] = ()  # engines the buyer asked for by name
    declared: tuple[tuple[str, str], ...] = ()  # (engine, operator's written reason)
    model_overrides: tuple[tuple[str, str], ...] = ()  # (engine, model id)


@dataclass(frozen=True)
class Decision:
    surface: str
    label: str
    decision: str
    reason_code: str
    reason: str
    tier: str | None = None
    web_search: bool | None = None
    model: str | None = None
    model_evidence: str | None = None
    model_caveat: str | None = None


def normalise_vertical(vertical: str) -> str:
    """'Personal Finance' and 'personal-finance' are the same vertical."""
    return "_".join(vertical.strip().lower().replace("-", " ").split())


@dataclass(frozen=True)
class Classification:
    """What the vertical map says about a vertical name."""

    given: str  # the name as typed
    vertical: str  # the map key the policy will see (or the normalised name if unlisted)
    audience: str
    local: bool
    source: str  # AUDIENCE_FROM_MAP, AUDIENCE_UNCLASSIFIED, or the classifier's own source
    note: str
    record: dict | None = None  # the classifier's ledger reference, when one was used


def load_vertical_map(path: str | Path) -> tuple[dict, str]:
    """Return (vertical map, sha256 of the file bytes)."""
    raw = Path(path).read_bytes()
    vmap = json.loads(raw.decode("utf-8"))
    validate_vertical_map(vmap)
    return vmap, hashlib.sha256(raw).hexdigest()


def _vertical_index(vmap: dict) -> dict[str, str]:
    """name-or-alias -> key. A name that points at two keys is a refused map."""
    index: dict[str, str] = {}
    for key, row in vmap["verticals"].items():
        for name in (key, *row["aliases"]):
            norm = normalise_vertical(name)
            if index.get(norm, key) != key:
                raise SelectionError(
                    f"vertical map: {norm!r} points at both {index[norm]!r} and {key!r}"
                )
            index[norm] = key
    return index


def validate_vertical_map(vmap: dict) -> None:
    for key in ("map_version", "verticals", "unclassified"):
        if key not in vmap:
            raise SelectionError(f"vertical map is missing {key!r}")
    rows = {"unclassified": vmap["unclassified"], **vmap["verticals"]}
    for name, row in rows.items():
        if row.get("audience") not in (*BASE_AUDIENCES, "mixed"):
            raise SelectionError(f"vertical map: {name!r} has audience {row.get('audience')!r}")
        if not isinstance(row.get("local"), bool):
            raise SelectionError(f"vertical map: {name!r} has no boolean 'local'")
    for name, row in vmap["verticals"].items():
        if name != normalise_vertical(name):
            raise SelectionError(f"vertical map: key {name!r} is not in normalised form")
        if not isinstance(row.get("aliases"), list):
            raise SelectionError(f"vertical map: {name!r} has no 'aliases' list")
    _vertical_index(vmap)


def classify_vertical(name: str, vmap: dict) -> Classification:
    """
    Map a typed vertical to (key, audience, local). Exact key or alias only,
    with one singular/plural retry - never a substring or fuzzy match.

    An unlisted vertical is NOT guessed into b2c or b2b. It takes the map's
    declared `unclassified` row and says so in `source`.
    """
    norm = normalise_vertical(name)
    if not norm:
        raise SelectionError("vertical is empty. Name the vertical being studied.")
    index = _vertical_index(vmap)
    candidates = [norm, norm + "s"]
    if norm.endswith("es"):
        candidates.append(norm[:-2])
    if norm.endswith("s"):
        candidates.append(norm[:-1])
    for candidate in candidates:
        if candidate in index:
            key = index[candidate]
            row = vmap["verticals"][key]
            return Classification(
                given=name, vertical=key, audience=row["audience"], local=row["local"],
                source=AUDIENCE_FROM_MAP,
                note=f"{norm!r} is listed under {key!r} in {vmap['map_version']}",
            )
    row = vmap["unclassified"]
    return Classification(
        given=name, vertical=norm, audience=row["audience"], local=row["local"],
        source=AUDIENCE_UNCLASSIFIED,
        note=(f"{norm!r} is not in {vmap['map_version']}; treated as {row['audience']} so no "
              "engine is dropped on a guess. Add a row or pass --audience."),
    )


def load_policy(path: str | Path) -> tuple[dict, str]:
    """Return (policy, sha256 of the file bytes). The digest goes on the plan."""
    raw = Path(path).read_bytes()
    policy = json.loads(raw.decode("utf-8"))
    validate_policy(policy)
    return policy, hashlib.sha256(raw).hexdigest()


def validate_policy(policy: dict) -> None:
    """A policy that cannot answer for every engine and audience is refused."""
    for key in ("policy_version", "engines", "unmeasured_surfaces", "web_search_default",
                "models", "declared_reason_min_chars"):
        if key not in policy:
            raise SelectionError(f"policy is missing {key!r}")
    if not policy["engines"]:
        raise SelectionError("policy lists no engines")

    for name, spec in policy["engines"].items():
        for audience in BASE_AUDIENCES:
            tier = spec.get("tier", {}).get(audience)
            if tier not in TIERS:
                raise SelectionError(
                    f"engine {name!r}: tier for {audience!r} is {tier!r}, want one of {TIERS}"
                )
        if not isinstance(spec.get("relevant_verticals"), list):
            raise SelectionError(f"engine {name!r}: relevant_verticals must be a list")
        if name not in policy["models"]:
            raise SelectionError(f"engine {name!r}: no entry under models")

    overlap = set(policy["engines"]) & set(policy["unmeasured_surfaces"])
    if overlap:
        raise SelectionError(f"listed as both engine and unmeasured: {sorted(overlap)}")

    for name, spec in policy["unmeasured_surfaces"].items():
        for key in ("label", "reason_code", "reason"):
            if not spec.get(key):
                raise SelectionError(f"unmeasured surface {name!r} is missing {key!r}")

    for audience in (*BASE_AUDIENCES, "mixed"):
        if not isinstance(policy["web_search_default"].get(audience), bool):
            raise SelectionError(f"web_search_default has no boolean for {audience!r}")


def _tier(spec: dict, audience: str) -> str:
    if audience == "mixed":
        tiers = {spec["tier"][a] for a in BASE_AUDIENCES}
        return "core" if "core" in tiers else "conditional"
    return spec["tier"][audience]


def _check_profile(profile: StudyProfile, policy: dict) -> None:
    if profile.audience not in (*BASE_AUDIENCES, "mixed"):
        raise SelectionError(
            f"unknown audience {profile.audience!r}. Want one of: b2c, b2b, mixed. "
            "No default is applied."
        )
    if not normalise_vertical(profile.vertical):
        raise SelectionError("vertical is empty. Name the vertical being studied.")

    engines = policy["engines"]
    unmeasured = policy["unmeasured_surfaces"]
    named = (
        [(e, "requested") for e in profile.requested]
        + [(e, "declared") for e, _ in profile.declared]
        + [(e, "given a model override") for e, _ in profile.model_overrides]
    )
    for engine, how in named:
        if engine in unmeasured:
            raise SelectionError(
                f"{engine!r} was {how} but cannot be measured: {unmeasured[engine]['reason']}"
            )
        if engine not in engines:
            raise SelectionError(
                f"{engine!r} was {how} but is not in the policy. "
                f"Known: {', '.join(sorted(engines))}"
            )

    minimum = policy["declared_reason_min_chars"]
    for engine, reason in profile.declared:
        if len(reason.strip()) < minimum:
            raise SelectionError(
                f"declared relevance for {engine!r} needs a written reason of at least "
                f"{minimum} characters; got {reason.strip()!r}"
            )


def resolve_web_search(profile: StudyProfile, policy: dict) -> tuple[bool, str]:
    """(search on?, why). An explicit operator setting wins; then local intent."""
    if profile.web_search is not None:
        return profile.web_search, "set by operator"
    if profile.local:
        return True, "local-intent study: consumer apps retrieve live for local questions"
    default = policy["web_search_default"][profile.audience]
    return default, f"policy default for {profile.audience}"


def _model_for(engine: str, search: bool, profile: StudyProfile, policy: dict) -> dict:
    overrides = dict(profile.model_overrides)
    if engine in overrides:
        return {
            "model": overrides[engine],
            "model_evidence": None,
            "model_caveat": "operator override; no committed evidence for this id. "
                            "Confirm with --smoke.",
        }
    mode = "search_on" if search else "search_off"
    entry = policy["models"][engine].get(mode)
    if entry is None:
        raise SelectionError(
            f"policy has no {mode} model for {engine!r}. Pass --model {engine}=<id> "
            "or change the search setting."
        )
    return {
        "model": entry["model"],
        "model_evidence": entry.get("evidence"),
        "model_caveat": entry.get("caveat"),
    }


def _condition(name: str, spec: dict, profile: StudyProfile, vertical: str) -> tuple[str, str]:
    """Which condition, if any, admits a conditional engine. First match wins."""
    if name in profile.requested:
        return CLIENT_REQUESTED, "the buyer asked for this engine by name"
    declared = dict(profile.declared)
    if name in declared:
        return OPERATOR_DECLARED, f"operator declared relevance: {declared[name].strip()}"
    if vertical in spec["relevant_verticals"]:
        return VERTICAL_RELEVANT, f"vertical {vertical!r} is on this engine's relevant list"
    return CONDITION_NOT_MET, (
        f"conditional for {profile.audience}; not requested, not declared, and vertical "
        f"{vertical!r} is not on its relevant list"
    )


def select_engines(profile: StudyProfile, policy: dict) -> list[Decision]:
    """One Decision per surface in the policy. Pure: no I/O, no clock."""
    validate_policy(policy)
    _check_profile(profile, policy)

    vertical = normalise_vertical(profile.vertical)
    search, _ = resolve_web_search(profile, policy)
    decisions: list[Decision] = []

    for name, spec in policy["engines"].items():
        tier = _tier(spec, profile.audience)
        if tier == "core":
            code, reason = AUDIENCE_CORE, f"core engine for a {profile.audience} audience"
        else:
            code, reason = _condition(name, spec, profile, vertical)

        if code == CONDITION_NOT_MET:
            decisions.append(Decision(name, spec["label"], SKIP, code, reason, tier=tier))
            continue

        # Perplexity retrieves live whatever is asked; the runner forces it on too.
        engine_search = True if name == "perplexity" else search
        decisions.append(
            Decision(name, spec["label"], RUN, code, reason, tier=tier,
                     web_search=engine_search,
                     **_model_for(name, engine_search, profile, policy))
        )

    for name, spec in policy["unmeasured_surfaces"].items():
        decisions.append(
            Decision(name, spec["label"], NOT_MEASURED, spec["reason_code"], spec["reason"])
        )
    return decisions


def build_plan(
    profile: StudyProfile,
    policy: dict,
    policy_sha256: str,
    *,
    audience_source: dict | None = None,
) -> dict:
    """
    The JSON-serialisable plan a study files next to its evidence.

    `audience_source` records where the audience came from (operator flag,
    vertical map row, or the unclassified fallback) and, for the map, its
    version and digest. Absent means the caller set the audience directly.
    """
    decisions = select_engines(profile, policy)
    search, search_reason = resolve_web_search(profile, policy)
    return {
        "plan_schema": PLAN_SCHEMA,
        "policy_version": policy["policy_version"],
        "policy_sha256": policy_sha256,
        "audience_source": audience_source or {"source": AUDIENCE_FROM_OPERATOR},
        "profile": {
            "audience": profile.audience,
            "vertical": normalise_vertical(profile.vertical),
            "local": profile.local,
            "requested": list(profile.requested),
            "declared": [{"engine": e, "reason": r.strip()} for e, r in profile.declared],
            "model_overrides": [{"engine": e, "model": m} for e, m in profile.model_overrides],
        },
        "web_search": search,
        "web_search_reason": search_reason,
        "decisions": [asdict(d) for d in decisions],
        "run": [d.surface for d in decisions if d.decision == RUN],
        "skipped": [d.surface for d in decisions if d.decision == SKIP],
        "not_measured": [d.surface for d in decisions if d.decision == NOT_MEASURED],
    }


def runner_commands(
    plan: dict,
    *,
    bank: str,
    runs: int,
    outdir: str,
    tag: str,
    date: str,
    python: str = "python",
    smoke: bool = False,
) -> list[list[str]]:
    """
    One run_bank_multi_v2.py command per RUN engine and none for anything else.

    This is the enforcement point: a skipped engine has no command, so a study
    launched from its plan cannot call it.
    """
    if runs < 1:
        raise SelectionError(f"runs must be at least 1; got {runs}")
    commands: list[list[str]] = []
    for d in plan["decisions"]:
        if d["decision"] != RUN:
            continue
        prefix = "SMOKE_" if smoke else ""
        out = f"{outdir.rstrip('/')}/{prefix}multi_{d['surface']}_{tag}_{date}.jsonl"
        cmd = [python, "run_bank_multi_v2.py", "--engine", d["surface"], "--model", d["model"],
               "--bank", bank, "--runs", str(runs), "--out", out]
        if d["web_search"] and d["surface"] != "perplexity":
            cmd.append("--search")  # the runner turns Perplexity search on by itself
        if smoke:
            cmd.append("--smoke")
        commands.append(cmd)
    return commands


def render_plan(plan: dict) -> str:
    """Plain-text plan for the terminal. Every surface appears, run or not."""
    p = plan["profile"]
    lines = [
        f"ENGINE PLAN  policy={plan['policy_version']}  sha256={plan['policy_sha256'][:12]}",
        (f"audience={p['audience']}  vertical={p['vertical']}  local={p['local']}  "
         f"web_search={plan['web_search']} ({plan['web_search_reason']})"),
    ]
    src = plan["audience_source"]
    lines.append(f"audience from {src['source']}" + (f": {src['note']}" if src.get("note") else ""))
    if src["source"] == AUDIENCE_UNCLASSIFIED:
        lines.append(
            "WARNING: unclassified vertical - every engine is planned. Check before --execute."
        )
    lines.append("")
    for d in plan["decisions"]:
        lines.append(f"{d['decision']:<13}{d['surface']:<20}{d['reason_code']}")
        lines.append(f"{'':13}{d['reason']}")
        if d["decision"] == RUN:
            source = d["model_evidence"] or "no committed evidence"
            lines.append(f"{'':13}model={d['model']}  search={d['web_search']}  [{source}]")
            if d["model_caveat"]:
                lines.append(f"{'':13}CAVEAT: {d['model_caveat']}")
    lines += [
        "",
        f"RUN {len(plan['run'])}: {', '.join(plan['run']) or '-'}",
        f"SKIP {len(plan['skipped'])}: {', '.join(plan['skipped']) or '-'}",
        f"NOT_MEASURED {len(plan['not_measured'])}: {', '.join(plan['not_measured']) or '-'}",
    ]
    return "\n".join(lines)
