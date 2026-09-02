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


# --- D4 fix: citation qualification -------------------------------------
# Rule published in the methodology page. A dotted token is a citation domain
# only in citation context. Everything else is a candidate, not a citation.
#
# Recognised suffixes. Deliberately a moderate inline set, not the full IANA
# root: the cue/URL-shape test is the control, this is a secondary sieve, and
# a fuller list would admit MORE source-file extensions, not fewer.
# Reviewed 2026-08-19.
_D4_TLD = frozenset(["com", "org", "net", "edu", "gov", "mil", "int", "info", "biz", "name", "pro", "io", "ai", "app", "dev", "co", "xyz", "online", "site", "tech", "store", "blog", "cloud", "digital", "agency", "media", "news", "press", "today", "world", "life", "live", "work", "space", "team", "group", "solutions", "systems", "services", "network", "global", "me", "tv", "uk", "de", "fr", "jp", "ca", "au", "nl", "it", "es", "se", "ch", "in", "br", "mx", "ru", "pl", "no", "fi", "dk", "be", "at", "ie", "nz", "sg", "kr"])

# Suffixes that are real TLDs but overwhelmingly appear as source-file
# extensions in software prose. "see README.md" must not mint a citation.
# KNOWN ASYMMETRY, disclosed rather than discovered: a brand whose real domain
# ends in one of these cannot earn a bare-token citation. It still qualifies
# via URL shape.
_D4_EXT = frozenset(["md", "py", "sh", "ts", "rs", "so", "cc", "as", "im", "cd", "la", "ml"])

_D4_URLISH = re.compile(r"(?i)(?:https?://|www\.)[^\s<>\"')\]]+")
_D4_HOSTOK = re.compile(r"(?i)^(?:[a-z0-9][-a-z0-9]*\.)+([a-z]{2,24})$")
_D4_BARE = re.compile(
    r"(?i)(?<![\w@./-])((?:[a-z0-9][-a-z0-9]*\.)+([a-z]{2,24}))(/[^\s<>\"')\]]*)?"
)
_D4_CUE = re.compile(
    r"(?i)\[\d+\]|\b(?:sources?|cited|citations?|references?|see|according\s+to)\b"
)
# A cue followed by a denial is not a citation. This is the mirror image of the
# defect closed in 7ff6781: "Sources: none found for acme.com".
_D4_NEG = re.compile(
    r"(?i)\b(?:no|none|not|non|never|unable|without|lacks?|lacking|absent|missing)\b"
)


def _d4_clean(host):
    host = host.lower().strip(".,;:!?)]}'\"")
    return host.removeprefix("www.")


_D4_PAREN_OPEN = "(["
_D4_PAREN_CLOSE = ")]"


def _d4_paren_span(block, s, e):
    """Text from an enclosing opener to the match, or None if not enclosed.

    A domain inside (...) or [...] is cited by the format: in ranked-list
    output the parenthetical is the citation slot, which is why a model with
    no source writes "(no citation)" in exactly that position.
    """
    head = block[:s]
    stack = []
    for i, ch in enumerate(head):
        if ch in _D4_PAREN_OPEN:
            stack.append(i)
        elif ch in _D4_PAREN_CLOSE and stack:
            stack.pop()
    if not stack:
        return None
    for ch in block[e:]:
        if ch in _D4_PAREN_CLOSE:
            return head[stack[-1] + 1:]
        if ch in _D4_PAREN_OPEN:
            return None
    return None


def _d4_scan(block):
    """Yield (host, qualified) for one paragraph."""
    for m in _D4_URLISH.finditer(block):
        raw = re.sub(r"(?i)^https?://", "", m.group(0))
        host = _d4_clean(raw.split("/")[0])
        if _D4_HOSTOK.match(host):
            yield host, True

    for m in _D4_BARE.finditer(block):
        host, tld, path = m.group(1), m.group(2).lower(), m.group(3)
        host = _d4_clean(host)
        if tld not in _D4_TLD or tld in _D4_EXT:
            yield host, False
            continue
        if path:
            yield host, True
            continue
        par = _d4_paren_span(block, m.start(), m.end())
        if par is not None:
            yield host, not _D4_NEG.search(par)
            continue
        before = block[: m.start()]
        cues = list(_D4_CUE.finditer(before))
        if not cues:
            yield host, False
            continue
        yield host, not _D4_NEG.search(before[cues[-1].end():])


def _d4_walk(text, want):
    out = []
    for block in re.split(r"\n\s*\n", text or ""):
        for host, ok in _d4_scan(block):
            if ok is want and host not in out:
                out.append(host)
    return out


def extract_domains(text: str) -> list[str]:
    """Return citation domains found in text.

    A host qualifies when it carries a scheme, a www. prefix or a following
    slash-segment, or when it is bare with a recognised suffix and a citation
    cue earlier in the same paragraph, or an enclosing parenthesis,
    with no negation in between. Bare
    uncued tokens are candidates, not citations -- see
    extract_domain_candidates. Brand self-mentions receive no exemption.
    """
    return _d4_walk(text, True)


def extract_domain_candidates(text: str) -> list[str]:
    """Domain-shaped tokens the rule declined to count.

    Published beside the score so a refusal is inspectable rather than
    invisible. Never feeds citation_score.
    """
    return _d4_walk(text, False)


def _fail_meta(parse_errors: list[str], violations: list[str]) -> tuple[list[ToolEntry], dict]:
    """The empty-result failure shape, unified (was duplicated verbatim)."""
    return [], {
        "parse_success": False,
        "parse_errors": parse_errors,
        "violations": violations,
        "parse_mode": "unknown",
        "has_duplicates": False,
    }


def _line_rank_rest(ln: str, prev_rank: int) -> tuple[int, str]:
    """Extract (rank, rest) from a numbered or bulleted item line."""
    rank_match = re.match(r"^(\d+)\s*[\.\)]\s+(.*)$", ln)
    if rank_match:
        return int(rank_match.group(1)), rank_match.group(2).strip()
    return prev_rank + 1, re.sub(r"^[-•*]\s*", "", ln).strip()


def _split_name_why(rest: str) -> tuple[str, str]:
    """Split an item's text into (name_raw, why). Bold first, then delimiters."""
    bold_match = re.match(r"^\*\*(.+?)\*\*\s*[:–—-]\s*(.*)$", rest)
    if bold_match:
        return bold_match.group(1).strip(), bold_match.group(2).strip()
    parts = re.split(r"\s*[:–—]\s*", rest, maxsplit=1)
    if len(parts) == 1:
        # Try splitting on " - "
        parts = re.split(r"\s+-\s+", rest, maxsplit=1)
    name_raw = parts[0].strip()
    why = parts[1].strip() if len(parts) > 1 else ""
    return name_raw, why


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
        return _fail_meta(["PE-06"], ["OCV-01"])

    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]

    # Detect numbered or bulleted list items
    item_lines = [
        ln for ln in lines
        if re.match(r"^\d+\s*[\.\)]\s+", ln) or re.match(r"^[-•*]\s+", ln)
    ]

    if not item_lines:
        return _fail_meta(["PE-06"], ["OCV-01"])

    parse_mode = "list"
    rank = 0
    seen_norm: set[str] = set()
    has_dup = False

    for ln in item_lines:
        rank, rest = _line_rank_rest(ln, rank)
        name_raw, why = _split_name_why(rest)

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
