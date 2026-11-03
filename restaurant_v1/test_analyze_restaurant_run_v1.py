"""Tests for analyze_restaurant_run_v1.py.  Run from the repo root:
    python -m pytest restaurant_v1/test_analyze_restaurant_run_v1.py -q

The four SMOKE_* fixtures are verbatim model output from the NYC01 smoke run of 2026-10-07
("What are the best restaurants in Astoria, Queens?"). Perplexity is the complete answer; the
other three are the first 1,200 characters as printed by the runner's --smoke preview, so each
ends mid-sentence. The remaining fixtures are hand-written to pin one rule each.
"""
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_restaurant_run_v1 as ar  # noqa: E402

PLACE = frozenset(ar.GEO | {"astoria"})

SMOKE_OPENAI = """Here are some of the **best restaurants in Astoria, Queens** as of October 2026, based on recent reviews, local awards, and trusted guides:

---

##  Top-Rated Favorites (Tripadvisor & Michelin)

- **Taverna Kyclades**
  A standout Greek seafood institution, known for its grilled octopus and generous portions of fresh fish. Consistently ranks at the top of local listings. ([tripadvisor.com](https://www.tripadvisor.com/Restaurants-g29837-Astoria_Queens_New_York.html?utm_source=openai))

- **Butcher Bar**
  A popular American-style BBQ spot, praised for its smoked ribs and solid wine selection. ([tripadvisor.com](https://www.tripadvisor.com/Restaurants-g29837-Astoria_Queens_New_York.html?utm_source=openai))

- **Sanford’s**
  A long-standing Astoria favorite offering American comfort food in a modern, casual setting. ([tripadvisor.com](https://www.tripadvisor.com/Restaurants-g29837-Astoria_Queens_New_York.html?utm_source=openai))

- **Loukoumi Taverna**
  A beloved Greek/Mediterranean gem, celebrated for its flavorful branzino and warm atmosphere. ([tripadvisor.com](https://www.tripadvisor.com/Restaurants-g29837-Astoria_Queens_New_York.html?utm_source=openai))

- **Ibn Hamido"""

SMOKE_ANTHROPIC = """Astoria, Queens is famous for its incredible diversity of cuisines, especially Greek, and has long been one of NYC's best neighborhoods for eating out. Here's a roundup based on current reviews and guides:

## Greek Food (Astoria's Specialty)
- **Taverna Kyclades** – a true neighborhood institution considered one of the best Greek restaurants in NYC, known for seafood and lamb chops.
- **Anassa Taverna** – described by Forbes as "Destination Greek Dining", with reviewers calling it "an absolute gem" with a welcoming, positive team.
- **Bahari Estiatorio** (formerly Stamatis) – delivers hearty Greek fare in a cozy space with an open kitchen.
- **Gregory's 26 Corner Taverna** – a charming and rustic taverna, described by the Michelin Guide as an "old-time Greek retreat."
- **Amylos Taverna** – praised for incredible ambiance and excellent Greek food.

## American / Comfort Food
- **Sanford's** – a long-time local favorite serving elevated American comfort food, known for an award-winning whisky list.
- **Butcher Bar** – a well-reviewed BBQ/American spot, praised for its "great meat, great service, nice selection, good price".
- **The Bonnie** – a gastropub known for cocktails, DJs, a"""

SMOKE_GEMINI = """Astoria is one of New York City’s premier culinary destinations. While world-renowned for its authentic Greek tavernas, the neighborhood also boasts incredible Egyptian seafood, regional Mexican, Italian classics, and standout casual eats.

Here are the best restaurants in Astoria, broken down by category:

---

### **1. Iconic Greek & Mediterranean**
Astoria is the heart of Greek culture in NYC, and you shouldn’t visit without dining at one of these spots:

*   **Agnanti Meze** *(Astoria Park)*
    *Vibe:* Cozy, charming taverna with views of Astoria Park.
    *Highlights:* Known for exceptional mezze (small plates). Don’t miss the *ntakos* (Cretan barley rusk salad), grilled octopus, and clay-pot dishes.
*   **Taverna Kyclades** *(Ditmars Blvd)*
    *Vibe:* Bustling, energetic, and always has a crowd.
    *Highlights:* The neighborhood standard for simply prepared seafood. Order the charred octopus, whole grilled branzino, fried calamari, and lemon potatoes.
*   **Bahari Estiatorio** *(Broadway)*
    *Vibe:* A warm, homestyle taverna favored by locals who want to avoid peak Kyclades lines.
    *Highlights:* Incredible grilled lamb chops, *skordalia* (garlic dip), and"""

SMOKE_PERPLEXITY = """Astoria has a lot of great options, especially for Greek food. A strong shortlist:

- **Taverna Kyclades** — A neighborhood classic for Greek seafood; go for grilled fish, octopus, and other simply prepared seafood.
- **AbuQir** — Egyptian seafood, with fresh fish chosen from the display and grilled, fried, or baked to order.
- **Loukoumi Taverna** — Greek dishes beyond the usual, including octopus, dips, and Cypriot specialties.
- **Ruta Oaxaca** — A good pick for Oaxacan cooking, especially moles, tacos, and mezcal.
- **Via Vai** — Italian, known for handmade pasta and a more intimate dinner setting.
- **Astoria Seafood** — Casual, lively seafood where you pick your fish and choose how it’s cooked.
- **Bel Aire Diner** — A classic, all-hours-style diner for breakfast, sandwiches, and comfort food.

For a first visit, I’d choose **Taverna Kyclades** for Greek seafood, **Ruta Oaxaca** for something different, or **AbuQir** for a memorable fish dinner. Check current hours and reservations before heading out."""


def names(text):
    return [n for n, _, _ in ar.discover(text, PLACE)]


def keys(text):
    return [k for _, k, _ in ar.discover(text, PLACE)]


# ------------------------------------------------------------------ real smoke rows

def test_smoke_openai_names_and_no_intro_phrase():
    assert names(SMOKE_OPENAI) == ["Taverna Kyclades", "Butcher Bar", "Sanford’s", "Loukoumi Taverna"]


def test_smoke_anthropic_names_categories_dropped():
    assert names(SMOKE_ANTHROPIC) == [
        "Taverna Kyclades", "Anassa Taverna", "Bahari Estiatorio", "Gregory's 26 Corner Taverna",
        "Amylos Taverna", "Sanford's", "Butcher Bar", "The Bonnie"]


def test_smoke_gemini_bold_heading_is_category_and_italic_labels_ignored():
    assert names(SMOKE_GEMINI) == ["Agnanti Meze", "Taverna Kyclades", "Bahari Estiatorio"]


def test_smoke_perplexity_complete_answer():
    assert names(SMOKE_PERPLEXITY) == [
        "Taverna Kyclades", "AbuQir", "Loukoumi Taverna", "Ruta Oaxaca", "Via Vai", "Astoria Seafood",
        "Bel Aire Diner"]


def test_apostrophe_variants_share_one_key():
    assert ar.norm_key("Sanford’s") == ar.norm_key("Sanford's") == "sanfords"
    assert "sanfords" in keys(SMOKE_OPENAI) and "sanfords" in keys(SMOKE_ANTHROPIC)


# ------------------------------------------------------------------ one rule each

def test_norm_key_rules():
    assert ar.norm_key("The Bonnie") == "bonnie"
    assert ar.norm_key("Lucali Pizzeria") == "lucali"
    assert ar.norm_key("Café Boulud Restaurant") == "cafe boulud"
    assert ar.norm_key("Mac & Cheese & Co") == "mac and cheese"
    assert ar.norm_key("TAVERNA   KYCLADES!") == "taverna kyclades"


def test_colon_names_kept_repeated_colon_labels_dropped():
    text = """### Greek
- **Taverna Kyclades:** seafood institution.
- **Bahari Estiatorio:** homestyle.

### 1. Sweet Afton
- **Cuisine:** gastropub
- **Signature dish:** the burger
- **Must-Try Dishes:** pickles

### 2. Mom's Kitchen & Bar
- **Cuisine:** American
- **Signature dish:** pancakes
- **Must-Try Dishes:** mac and cheese
"""
    assert names(text) == ["Taverna Kyclades", "Bahari Estiatorio", "Sweet Afton", "Mom's Kitchen & Bar"]


def test_category_bullet_with_nested_names():
    text = """- **Greek:**
  - **Taverna Kyclades** – seafood
  - **Agnanti Meze** – meze
- **Italian:**
  - **Via Vai** – pasta
"""
    assert names(text) == ["Taverna Kyclades", "Agnanti Meze", "Via Vai"]


def test_name_bullet_with_plain_detail_children_stays_a_name():
    text = """- **Taverna Kyclades** – Greek seafood
  - Great for groups
  - Grilled octopus: must order
- **Butcher Bar** – BBQ
  - Cash only
"""
    assert names(text) == ["Taverna Kyclades", "Butcher Bar"]


def test_table_uses_the_name_column_and_recap_does_not_erase_names():
    text = """1. **Taverna Kyclades** – seafood
2. **Via Vai** – pasta

| Cuisine | Restaurant | Price |
|---|---|---|
| Greek | **Taverna Kyclades** | $$ |
| Italian | Via Vai | $$ |
| BBQ | Butcher Bar | $$ |
"""
    assert names(text) == ["Taverna Kyclades", "Via Vai", "Butcher Bar"]


def test_plain_ordered_list_and_plain_sentences():
    text = """1. Taverna Kyclades – Greek seafood
2. Butcher Bar: smoked ribs
3. Go early to avoid the line.
- Great for groups – really
"""
    assert names(text) == ["Taverna Kyclades", "Butcher Bar"]


def test_generic_and_place_only_heads_rejected():
    text = """## Best Restaurants in Astoria
## Final Thoughts
Enjoy.
**Quick Tips**
- **Reservations:** recommended
- **Top Picks**
"""
    assert names(text) == []


def test_inline_bold_is_weakest_class_and_first_named_prefers_structure():
    text = "You could try **Trattoria L'incontro** tonight.\n\n- **Via Vai** – pasta\n"
    found = ar.discover(text, PLACE)
    assert [(n, c) for n, _, c in found] == [("Trattoria L'incontro", "bold_inline"), ("Via Vai", "list_bold")]


def test_pipe_table_without_leading_pipes():
    text = """### Summary Table

Restaurant | Why
--- | ---
Taverna Kyclades | seafood
Via Vai | pasta
"""
    assert names(text) == ["Taverna Kyclades", "Via Vai"]


def test_advice_bullets_are_not_names():
    text = """- **Make a reservation** – it fills up
- **Go early** on weekends
- **Interview 2-3 agents** before you sign
- **Café con Leche** – Cuban
"""
    assert names(text) == ["Café con Leche"]


def test_abbreviations_and_initials_survive():
    text = "- **St. Anselm** – steaks\n- **J.G. Melon** – burgers\n- **Mr. Chow** – Chinese\n- **Great food. Try it** – no\n"
    assert names(text) == ["St. Anselm", "J.G. Melon", "Mr. Chow"]


def test_name_bolded_in_the_intro_keeps_first_position_and_structural_class():
    text = "For a first visit, **Taverna Kyclades** is the one.\n\n- **Taverna Kyclades** – seafood\n- **Via Vai** – pasta\n"
    assert ar.discover(text, PLACE) == [("Taverna Kyclades", "taverna kyclades", "list_bold"),
                                        ("Via Vai", "via vai", "list_bold")]


def test_bold_name_after_a_plain_category_head():
    assert names("- Greek: **Taverna Kyclades**\n") == ["Taverna Kyclades"]
    assert names("1. Try **Via Vai** for pasta\n") == ["Via Vai"]
    assert names("## Best overall: **Via Vai**\nIt is good.\n") == ["Via Vai"]


def test_restaurant_heading_with_a_bold_label_line_stays_a_name():
    text = "### Taverna Kyclades\n**Highlights:**\n- Grilled octopus\n\n### Via Vai\n**Highlights:**\n- Pasta\n"
    assert names(text) == ["Taverna Kyclades", "Via Vai"]


def test_colon_name_repeated_once_in_a_recap_is_kept():
    text = "- **Via Vai:** handmade pasta\n- **Butcher Bar:** ribs\n\nRecap:\n- **Via Vai:** for a date\n"
    assert names(text) == ["Via Vai", "Butcher Bar"]


def test_one_word_colon_head_twice_is_a_label():
    text = "- **Via Vai** – pasta\n  - **Reputation:** strong\n- **Butcher Bar** – ribs\n  - **Reputation:** solid\n"
    assert names(text) == ["Via Vai", "Butcher Bar"]


def test_described_name_keeps_its_place_over_nested_bold_dishes():
    text = "- **Taverna Kyclades** – seafood\n  - **Grilled Octopus** – order it\n- **Via Vai** – pasta\n"
    assert names(text) == ["Taverna Kyclades", "Via Vai"]


def test_table_name_column_by_header():
    venue = "Cuisine | Venue | Price\n--- | --- | ---\nGreek | Taverna Kyclades | $$\nItalian | Via Vai | $$\n"
    assert names(venue) == ["Taverna Kyclades", "Via Vai"]
    place = "| Type of Place | Restaurant |\n|---|---|\n| Taverna | Taverna Kyclades |\n| Trattoria | Via Vai |\n"
    assert names(place) == ["Taverna Kyclades", "Via Vai"]


def test_one_word_core_is_searched_with_its_article():
    assert ar.cased_needles("The Smith") == [" The Smith ", " the Smith "]
    assert ar.cased_needles("The Butcher Bar") == [" Butcher Bar "]
    assert ar.cased_needles("Lucali Pizzeria") == [" Lucali Pizzeria "]
    assert ar.cased_needles("Olmsted") == [" Olmsted "]
    assert " Smith " not in "".join(ar.cased_needles("The Smith")).replace(" The Smith ", "").replace(" the Smith ", "")


# Modelled on the ChatGPT smoke answer of 2026-10-07. Lines marked (v) are verbatim from that row; the
# rest is filled in to complete the structure, because only the lines behind the junk names were printed.
AWARDS = """- **Best American Restaurant**:
  1. Sanfords
  2. The Bonnie
  3. Queen’s Room, Sanfords, Sweet Afton (tie) ([boast.nyc](https://boast.nyc/boast-best-of-astoria-lic-2025-winners-full-list/?utm_source=openai))

- **Best Deli**:
  1. Sal, Kris & Charlie’s Deli
  2. George’s Deli

- **Best Brunch**:
  1. Tootles & French
  2. Queen’s Room
  3. Sweet Afton & The Bonnie (tie) ([boast.nyc](https://boast.nyc/boast-best-of-astoria-lic-2025-winners-full-list/?utm_source=openai))

##  Diverse & Emerging Favorites (Infatuation & Wanderlog)

- **Wanderlog’s Picks**
  - Trattoria L’incontro
  - Christos Steak House

| Category | Restaurants |
|---|---|
| Greek/Seafood             | Taverna Kyclades, Loukoumi Taverna, Ovelia, Kabab Cafe                              |
| Brunch & Bakeries         | Tootles & French, Queen’s Room, Martha’s Country Bakery                             |
"""


def test_award_category_bullets_hand_over_to_the_numbered_names():
    got = names(AWARDS)
    for label in ("Best American Restaurant", "Best Deli", "Best Brunch", "Wanderlog’s Picks"):
        assert label not in got
    assert got[:2] == ["Sanfords", "The Bonnie"]
    for real in ("Sal, Kris & Charlie’s Deli", "George’s Deli", "Tootles & French", "Queen’s Room",
                 "Trattoria L’incontro", "Christos Steak House"):
        assert real in got, real
    # table cells listing several places are kept whole here and cut apart later, with the market's lexicon
    assert "Taverna Kyclades, Loukoumi Taverna, Ovelia, Kabab Cafe" in got


def test_joined_names_split_only_when_the_market_knows_the_parts(tmp_path):
    p = tmp_path / "run.jsonl"
    p.write_text(json.dumps(_row("openai", "NYC01", 1, "Astoria", AWARDS), ensure_ascii=False) + "\n", encoding="utf-8")
    out = tmp_path / "res"
    ar.main([str(p), "--out", str(out)])
    cand = {r["key"] for r in _read(out / "candidates.csv")}
    assert "sweet afton" in cand and "bonnie" in cand and "queens room" in cand and "sanfords" in cand
    assert not any("queens room sanfords" in k or "sweet afton and" in k for k in cand)
    assert "sal kris and charlies deli" in cand and "tootles and french" in cand     # real names keep their commas and &
    for k in ("taverna kyclades", "loukoumi taverna", "ovelia", "kabab cafe", "marthas country bakery"):
        assert k in cand, k                                                          # table cells cut at their commas


def test_table_list_never_cuts_a_name_the_market_gave_whole(tmp_path):
    """The defect seen on the operator's smoke rows, 2026-10-07: a table cell split at every comma produced
    'Sal' and 'Kris & Charlie's Deli', and the second was then matched inside the real name in other answers."""
    table = "| Type | Restaurants |\n|---|---|\n| Delis | Sal, Kris & Charlie’s Deli, George’s Deli, Il Bambino |\n"
    rows = [_row("openai", "NYC01", 1, "Astoria", "- **Sal, Kris & Charlie’s Deli** – heroes\n\n" + table),
            _row("anthropic", "NYC01", 1, "Astoria", "- **Sal, Kris & Charlie's Deli** – famous for The Bomb\n"),
            _row("gemini", "NYC01", 1, "Astoria", "*   **Sal, Kris & Charlie’s Deli** *(23rd Ave)*\n")]
    p = tmp_path / "run.jsonl"
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    out = tmp_path / "res"
    ar.main([str(p), "--out", str(out)])
    cand = {r["key"]: r for r in _read(out / "candidates.csv")}
    assert cand["sal kris and charlies deli"]["responses"] == "3"
    assert "sal" not in cand and "kris and charlies deli" not in cand
    assert "georges deli" in cand and "il bambino" in cand


def test_parts_cut_from_a_table_cell_are_tidied_like_any_other_name(tmp_path):
    """Defect seen on the operator's smoke rows, 2026-10-07: 'Dar Lbahja (Moroccan)' came out of a table cell
    as its own candidate beside 'Dar Lbahja', because cut parts skipped the bracket-stripping step."""
    table = "| Type | Restaurants |\n|---|---|\n| Global | Dar Lbahja (Moroccan), Sami’s Kabab House (Afghan), Ramro (Filipino) |\n"
    rows = [_row("openai", "NYC01", 1, "Astoria", "- **Dar Lbahja** – tagines\n- **Sami’s Kabab House** – kababs\n\n" + table)]
    p = tmp_path / "run.jsonl"
    p.write_text(json.dumps(rows[0], ensure_ascii=False) + "\n", encoding="utf-8")
    out = tmp_path / "res"
    ar.main([str(p), "--out", str(out)])
    cand = {r["key"]: r["display"] for r in _read(out / "candidates.csv")}
    assert set(cand) == {"dar lbahja", "samis kabab house", "ramro"}
    assert not any("(" in d for d in cand.values())


def test_best_split_rules():
    known = {"sweet afton", "bonnie", "queens room", "sanfords"}
    assert ar.best_split("Sweet Afton & The Bonnie", known, PLACE, False) == ["Sweet Afton", "The Bonnie"]
    assert ar.best_split("Queen’s Room, Sanfords, Martha’s Country Bakery", known, PLACE, False) == [
        "Queen’s Room", "Sanfords", "Martha’s Country Bakery"]
    assert ar.best_split("Sal, Kris & Charlie’s Deli", known, PLACE, False) is None
    assert ar.best_split("Tootles & French", known, PLACE, False) is None
    assert ar.best_split("Chela & Garnacha", known | {"chela"}, PLACE, False) is None      # one side known is not enough
    assert ar.best_split("Ovelia, Kabab Cafe, Aliada", set(), PLACE, True) == ["Ovelia", "Kabab Cafe", "Aliada"]
    assert ar.best_split("Ovelia, Kabab Cafe", set(), PLACE, True) is None                 # one comma: not a list


def test_best_pizza_is_still_a_name_when_it_is_listed_as_one():
    assert names("- **Best Pizza** – wood-fired slices on Havemeyer St\n- **L’industrie Pizzeria** – burrata slice\n") == [
        "Best Pizza", "L’industrie Pizzeria"]


def test_bold_dish_after_a_food_label_is_not_a_place():
    text = "*   **Sal, Kris & Charlie’s Deli** *(23rd Ave)*\n    *What to get:* **The Bomb**—a monster hero piled high.\n"
    assert names(text) == ["Sal, Kris & Charlie’s Deli"]
    assert names("- Greek: **Taverna Kyclades**\n") == ["Taverna Kyclades"]


def test_unordered_plain_bullets_alone_are_not_names():
    assert names("Some thoughts:\n- Sweet Afton\n- Great Food\n") == []


def test_citation_links_do_not_become_names():
    text = "- **Via Vai** ([viavai-ny.com](https://www.viavai-ny.com/press)) – pasta [1][2]\n"
    assert names(text) == ["Via Vai"]


# ------------------------------------------------------------------ end to end

def _row(engine, pid, rep, area, text, cites=()):
    return {"engine": engine, "bank_version": "nyc_restaurant_prompts_v1", "prompt_id": pid, "rep": rep,
            "area": area, "family": "New York City", "intent": "best_overall", "response_text": text,
            "citations": [{"url": u, "title": ""} for u in cites],
            "request_payload": {"tools": [{"type": "web_search"}]}}


@pytest.fixture()
def run_file(tmp_path):
    rows = []
    for engine, text in (("openai", SMOKE_OPENAI), ("anthropic", SMOKE_ANTHROPIC),
                         ("gemini", SMOKE_GEMINI), ("perplexity", SMOKE_PERPLEXITY)):
        for rep in (1, 2, 3):
            rows.append(_row(engine, "NYC01", rep, "Astoria", text, ["https://www.tripadvisor.com/x"]))
    rows.append(_row("anthropic", "NYC01", 4, "Astoria",
                     "I would send you to Taverna Kyclades, honestly, or to the Bonnie for a drink."))
    rows.append({"engine": "gemini", "bank_version": "nyc_restaurant_prompts_v1", "prompt_id": "NYC01",
                 "rep": 4, "error": "WinError 10054", "citations": []})
    p = tmp_path / "run.jsonl"
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return p


def _read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_end_to_end_counts_prose_pass_and_r3(run_file, tmp_path, capsys):
    out = tmp_path / "res"
    ar.main([str(run_file), "--out", str(out)])
    cand = {r["key"]: r for r in _read(out / "candidates.csv")}
    assert cand["taverna kyclades"]["responses"] == "13" and cand["taverna kyclades"]["of_n"] == "13"
    assert cand["taverna kyclades"]["engines_n"] == "4"
    assert cand["taverna kyclades"]["prose_only_responses"] == "1"       # the prose-only Claude row
    assert cand["bonnie"]["responses"] == "4" and cand["bonnie"]["prose_only_responses"] == "1"
    assert cand["butcher bar"]["engines"] == "anthropic;openai"
    summary = (out / "summary.txt").read_text(encoding="utf-8")
    assert "CLEAN RESPONSES 13 | ERROR ROWS 1" in summary
    assert "ALL CANDIDATES - NOT VERIFIED" in summary and "DECISION RULE: NOT EVALUATED" in summary
    # named by >=3 of 4 engines in Astoria: Kyclades (4), Bahari (2 -> no), Loukoumi (2 -> no)
    assert "same area: 1" in summary
    per = _read(out / "per_response.csv")
    assert len(per) == 13 and all(r["search_tool_in_payload"] == "1" for r in per)
    assert sum(r["citations"] == "0" for r in per) == 1
    dom = _read(out / "domains.csv")
    assert {"engine": "openai", "domain": "tripadvisor.com", "responses_citing": "3", "of_engine_responses": "3"} in dom


def test_one_stray_structural_word_is_not_amplified_through_prose(tmp_path):
    rows = [_row("openai", "NYC01", 1, "Astoria", "- **Reviews** – check them\n- **Via Vai** – pasta\n")]
    for rep in (2, 3, 4, 5):
        rows.append(_row("openai", "NYC01", rep, "Astoria",
                         "Reviews are mixed and the reviews say go. Try Via Vai, or via vai if you must."))
    p = tmp_path / "run.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    out = tmp_path / "res"
    ar.main([str(p), "--out", str(out)])
    cand = {r["key"]: r for r in _read(out / "candidates.csv")}
    assert cand["reviews"]["responses"] == "1"            # one-word name, support 1: never prose-matched
    assert cand["via vai"]["responses"] == "5" and cand["via vai"]["prose_only_responses"] == "4"


def test_prose_match_is_case_sensitive(tmp_path):
    rows = [_row("openai", "NYC01", r, "Astoria", "- **The Bonnie** – gastropub\n") for r in (1, 2, 3)]
    rows.append(_row("openai", "NYC01", 4, "Astoria", "My friend bonnie likes it."))
    rows.append(_row("openai", "NYC01", 5, "Astoria", "Head to the Bonnie after."))
    p = tmp_path / "run.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    out = tmp_path / "res"
    ar.main([str(p), "--out", str(out)])
    cand = {r["key"]: r for r in _read(out / "candidates.csv")}
    assert cand["bonnie"]["responses"] == "4" and cand["bonnie"]["prose_only_responses"] == "1"


def test_merges_fold_variants_and_chains_are_refused(run_file, tmp_path):
    m = tmp_path / "merges.csv"
    m.write_text("from_key,to_key\nbahari estiatorio,taverna kyclades\n", encoding="utf-8")
    out = tmp_path / "res"
    ar.main([str(run_file), "--out", str(out), "--merges", str(m)])
    cand = {r["key"] for r in _read(out / "candidates.csv")}
    assert "bahari estiatorio" not in cand and "taverna kyclades" in cand
    assert "MERGE RULES 1 | rules that matched a name: 1" in (out / "summary.txt").read_text(encoding="utf-8")
    m2 = tmp_path / "typo.csv"
    m2.write_text("from_key,to_key\nbahari estiatorioo,taverna kyclades\n", encoding="utf-8")
    out3 = tmp_path / "res3"
    ar.main([str(run_file), "--out", str(out3), "--merges", str(m2)])
    assert "NEVER MATCHED: ['bahari estiatorioo']" in (out3 / "summary.txt").read_text(encoding="utf-8")
    m.write_text("from_key,to_key\na,b\nb,c\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="merge chains"):
        ar.main([str(run_file), "--out", str(tmp_path / "res2"), "--merges", str(m)])


def test_bracket_before_a_colon_is_stripped():
    assert ar.tidy_name("Via Vai (Astoria):") == "Via Vai"
    assert ar.tidy_name("**Bahari Estiatorio** (formerly Stamatis)") == "Bahari Estiatorio"


def test_dash_inside_bold_and_numeric_ranges():
    text = "- **Via Vai – Italian** handmade pasta\n- **Sweet Afton (Astoria** gastropub\n1. Open 2–3 nights: check\n"
    assert names(text) == ["Via Vai", "Sweet Afton"]


def test_refuses_existing_out_and_mixed_banks(run_file, tmp_path):
    out = tmp_path / "res"
    ar.main([str(run_file), "--out", str(out)])
    with pytest.raises(SystemExit, match="REFUSE: .* exists"):
        ar.main([str(run_file), "--out", str(out)])
    other = tmp_path / "other.jsonl"
    r = _row("openai", "MA01", 1, "North End", SMOKE_OPENAI)
    r["bank_version"] = "ma_restaurant_prompts_v1"
    other.write_text(json.dumps(r) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="span bank versions"):
        ar.main([str(run_file), str(other), "--out", str(tmp_path / "res2")])


def test_verified_mode_counts_only_open_names_and_evaluates_rule(run_file, tmp_path):
    out = tmp_path / "res"
    ar.main([str(run_file), "--out", str(out)])
    sheet = _read(out / "verify_sheet.csv")
    assert [r["tier"] for r in sheet].count("A") == 1 and sheet[0]["key"] == "taverna kyclades"
    filled = tmp_path / "filled.csv"
    with open(filled, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sheet[0]))
        w.writeheader()
        for r in sheet:
            r["verdict"] = "open" if r["key"] in ("taverna kyclades", "butcher bar") else "closed"
            w.writerow(r)
    out2 = tmp_path / "res_verified"
    ar.main([str(run_file), "--out", str(out2), "--verified", str(filled)])
    cand = {r["key"] for r in _read(out2 / "candidates.csv")}
    assert cand == {"taverna kyclades", "butcher bar"}
    summary = (out2 / "summary.txt").read_text(encoding="utf-8")
    assert "VERIFIED NAMES ONLY" in summary and "DECISION RULE: NO TOP SET (R3=1, below 5)" in summary
    assert "R5 tier A: closed+not_found+wrong_area = 0.0% (0 of 1)" in summary


def test_same_cell_twice_is_refused(run_file, tmp_path):
    with pytest.raises(SystemExit, match="appear more than once"):
        ar.main([str(run_file), str(run_file), "--out", str(tmp_path / "r")])


def test_names_in_two_or_fewer_responses_are_in_no_metric(tmp_path):
    rows = [_row("openai", "NYC01", r, "Astoria", "- **Via Vai** – pasta\n") for r in (1, 2, 3)]
    rows.append(_row("openai", "NYC01", 4, "Astoria", "- **Sweet Afton** – gastropub\n"))
    p = tmp_path / "run.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    out = tmp_path / "res"
    ar.main([str(p), "--out", str(out)])
    summary = (out / "summary.txt").read_text(encoding="utf-8")
    assert "[openai] n=4 errors=0 | R1 names>=1: 75.0% (3 of 4)" in summary
    per = _read(out / "per_response.csv")
    assert [r["first_named"] for r in per] == ["via vai", "via vai", "via vai", ""]
    cand = {r["key"]: r for r in _read(out / "candidates.csv")}
    assert cand["sweet afton"]["tier"] == "excluded" and cand["sweet afton"]["first_named_responses"] == "0"


def test_no_decision_while_any_sheet_row_is_unchecked_and_stray_verdicts_refused(run_file, tmp_path):
    out = tmp_path / "res"
    ar.main([str(run_file), "--out", str(out)])
    sheet = _read(out / "verify_sheet.csv")
    filled = tmp_path / "filled.csv"
    with open(filled, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sheet[0]))
        w.writeheader()
        for r in sheet:
            r["verdict"] = "open" if r["tier"] == "A" else ""     # tier A done, tier B untouched
            w.writerow(r)
    out2 = tmp_path / "res2"
    ar.main([str(run_file), "--out", str(out2), "--verified", str(filled)])
    assert "DECISION RULE: NOT EVALUATED - %d of %d sheet rows have no verdict" % (len(sheet) - 1, len(sheet)) in (
        out2 / "summary.txt").read_text(encoding="utf-8")
    stray = tmp_path / "stray.csv"
    stray.write_text("key,verdict\nnot on the sheet,open\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="not on the current verification sheet"):
        ar.main([str(run_file), "--out", str(tmp_path / "res3"), "--verified", str(stray)])
    nocol = tmp_path / "nocol.csv"
    nocol.write_text("name,status\nx,open\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="needs columns 'key' and 'verdict'"):
        ar.main([str(run_file), "--out", str(tmp_path / "res4"), "--verified", str(nocol)])


def test_leftover_partial_directory_and_truncated_file_are_named(run_file, tmp_path):
    (tmp_path / "res.partial").mkdir()
    with pytest.raises(SystemExit, match="earlier run stopped before finishing"):
        ar.main([str(run_file), "--out", str(tmp_path / "res")])
    cut = tmp_path / "cut.jsonl"
    cut.write_text(run_file.read_text(encoding="utf-8")[:-40], encoding="utf-8")
    with pytest.raises(SystemExit, match="not valid JSON"):
        ar.main([str(cut), "--out", str(tmp_path / "res5")])
    assert not (tmp_path / "res5").exists() and not (tmp_path / "res5.partial").exists()


def test_rows_without_rep_fall_back_to_run_index(tmp_path):
    rows = []
    for i in (0, 1, 2):
        r = _row("openai", "NYC01", None, "Astoria", "- **Via Vai** – pasta\n")
        del r["rep"]
        r["run_index"] = i
        rows.append(r)
    p = tmp_path / "run.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    ar.main([str(p), "--out", str(tmp_path / "res")])
    assert [r["rep"] for r in _read(tmp_path / "res" / "per_response.csv")] == ["0", "1", "2"]


def test_unknown_verdict_refused(run_file, tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("key,verdict\ntaverna kyclades,probably\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="unknown verdicts"):
        ar.main([str(run_file), "--out", str(tmp_path / "r"), "--verified", str(bad)])


def test_output_identical_across_hash_seeds(run_file, tmp_path):
    digests = []
    for seed in ("0", "1", "2"):
        out = tmp_path / ("seed" + seed)
        env = dict(os.environ, PYTHONHASHSEED=seed)
        subprocess.run([sys.executable, str(HERE / "analyze_restaurant_run_v1.py"), str(run_file), "--out", str(out)],
                       check=True, capture_output=True, env=env)
        digests.append(tuple((out / f).read_bytes() for f in
                             ("candidates.csv", "per_response.csv", "domains.csv", "verify_sheet.csv", "summary.txt")))
    assert digests[0] == digests[1] == digests[2]


def test_verification_sample_is_reproducible():
    res = {"resp_count": {("name %03d" % i): (12 if i < 5 else 4) for i in range(105)}}
    first = ar.verification_sheet(res)
    assert first == ar.verification_sheet(res)
    sheet, n_a, n_b = first
    assert (n_a, n_b, len(sheet)) == (5, 100, 45)
