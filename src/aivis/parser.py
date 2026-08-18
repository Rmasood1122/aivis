from __future__ import annotations

import re

from .models import ToolEntry

DOMAIN_RE = re.compile(r"(?i)\b([a-z0-9][-a-z0-9]*\.[a-z]{2,}(?:\.[a-z]{2,})?)\b")

# Alias table: maps common variations to canonical name_norm
ALIAS_TABLE: dict[str, str] = {
    "jira software": "jira",
    "ms project": "microsoft project",
    "microsoft project online": "microsoft project",
    "monday": "monday.com",
    "click up": "clickup",
    "base camp": "basecamp",
    "wrike project management": "wrike",
    "smartsheet project management": "smartsheet",
    "github projects": "github",
    "gitlab project management": "gitlab",
}

STRIP_SUFFIXES = {"software", "app", "tool", "platform", "solution", "solutions"}


def norm_name(name: str) -> str:
    """Deterministic name normalization. Same input → same output. Always."""
    n = name.strip().lower()
    n = re.sub(r"[®™]", "", n)
    n = re.sub(r"\s+", " ", n)
    # strip trailing punctuation
    n = n.rstrip(".,;:!)")
    # strip known suffixes
    for suffix in STRIP_SUFFIXES:
        if n.endswith(f" {suffix}"):
            n = n[: -(len(suffix) + 1)].rstrip()
    # strip domain extensions when they're not the brand itself
    if not n.endswith(".com") and not n.endswith(".io") and not n.endswith(".co"):
        pass  # keep as-is
    else:
        # brands like monday.com keep their extension
        if n in ("monday.com", "clickup.com"):
            pass
        else:
            for ext in (".com", ".io", ".co"):
                if n.endswith(ext):
                    n = n[: -len(ext)].rstrip()
    # apply alias table
    if n in ALIAS_TABLE:
        n = ALIAS_TABLE[n]
    return n


def extract_domains(text: str) -> list[str]:
    """Extract citation domains from text. Strips www, protocol, paths."""
    domains: list[str] = []
    for m in DOMAIN_RE.finditer(text or ""):
        d = m.group(1).lower()
        d = d.removeprefix("www.")
        d = d.split("/")[0]
        if d not in domains and "." in d:
            domains.append(d)
    return domains


def parse_tool_list(raw: str) -> tuple[list[ToolEntry], dict]:
    """
    Parse a ranked tool list from raw model response.
    Returns (tool_list, meta_dict).
    meta keys: parse_success, parse_errors, violations, parse_mode, has_duplicates
    """
    parse_errors: list[str] = []
    violations: list[str] = []
    tool_list: list[ToolEntry] = []

    if not raw or not raw.strip():
        return [], {
            "parse_success": False,
            "parse_errors": ["PE-06"],
            "violations": ["OCV-01"],
            "parse_mode": "unknown",
            "has_duplicates": False,
        }

    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]

    # Detect numbered or bulleted list items
    item_lines: list[str] = []
    for ln in lines:
        if re.match(r"^\d+\s*[\.\)]\s+", ln) or re.match(r"^[-•*]\s+", ln):
            item_lines.append(ln)

    if not item_lines:
        violations.append("OCV-01")
        return [], {
            "parse_success": False,
            "parse_errors": ["PE-06"],
            "violations": violations,
            "parse_mode": "unknown",
            "has_duplicates": False,
        }

    parse_mode = "list"
    rank = 0
    seen_norm: set[str] = set()
    has_dup = False

    for ln in item_lines:
        # Try to extract explicit rank number
        rank_match = re.match(r"^(\d+)\s*[\.\)]\s+(.*)$", ln)
        if rank_match:
            rank = int(rank_match.group(1))
            rest = rank_match.group(2).strip()
        else:
            rank += 1
            rest = re.sub(r"^[-•*]\s*", "", ln).strip()

        # Split name from why using common delimiters
        # Handle **bold names** first
        bold_match = re.match(r"^\*\*(.+?)\*\*\s*[:–—-]\s*(.*)$", rest)
        if bold_match:
            name_raw = bold_match.group(1).strip()
            why = bold_match.group(2).strip()
        else:
            parts = re.split(r"\s*[:–—]\s*", rest, maxsplit=1)
            if len(parts) == 1:
                # Try splitting on " - "
                parts = re.split(r"\s+-\s+", rest, maxsplit=1)
            name_raw = parts[0].strip()
            why = parts[1].strip() if len(parts) > 1 else ""

        # Clean up name_raw
        name_raw = name_raw.strip("*").strip()

        if not name_raw:
            parse_errors.append("PE-02")
            continue
        if not why:
            parse_errors.append("PE-03")

        name_n = norm_name(name_raw)
        if name_n in seen_norm:
            has_dup = True
            parse_errors.append("PE-04")
        seen_norm.add(name_n)

        # Citation extraction
        # Fix (test_no_citation_phrase_should_not_discard_a_real_domain):
        # the phrase "no citation" in prose must not veto real domains found
        # in the same entry. Extraction decides; prose does not.
        domains = extract_domains(rest)

        tool_list.append(
            ToolEntry(
                rank=rank,
                name_raw=name_raw,
                name_norm=name_n,
                why=why,
                citation_domains=domains,
            )
        )

    # Enforce max 10
    if len(tool_list) > 10:
        violations.append("OCV-02")
        tool_list = tool_list[:10]

    # Check for all entries having a rank and name
    parse_success = len(tool_list) >= 1 and all(t.rank and t.name_raw for t in tool_list)

    return tool_list, {
        "parse_success": parse_success,
        "parse_errors": sorted(set(parse_errors)),
        "violations": sorted(set(violations)),
        "parse_mode": parse_mode,
        "has_duplicates": has_dup,
    }
