#!/usr/bin/env python3
"""gen_restaurant_banks_v1.py - emits the four restaurant prompt banks (NYC, MA, DE, CT).

Construction rule (fixed before any run):
  * 20 prompts per market = 10 areas x 2 intents. Area i gets intent i (phrasing A, slots 1-10)
    and intent (i+5) mod 10 (phrasing B, slots 11-20). Every intent is therefore asked twice per
    market, in two different areas, with two different wordings.
  * The slot -> (intent, phrasing) mapping is IDENTICAL across markets; only geography and the
    signature dish change. Cross-market comparisons join on `slot`.
  * Open-ended retrieval only: no prompt names a restaurant, chef, chain, guide or review site,
    so every roster is the engine's own.

Refuses to overwrite: every output path must be new (destruction lock).
Usage:  python restaurant_v1/gen_restaurant_banks_v1.py
"""
import json
import sys
from pathlib import Path

INTENTS = [
    ("best_overall",     "What are the best restaurants in {p}?",
                         "Which restaurants in {p} are most worth going to right now?"),
    ("date_night",       "Where should I go for a date night dinner in {p}?",
                         "Recommend a romantic restaurant in {p} for a date."),
    ("special_occasion", "Recommend a restaurant in {p} for an anniversary dinner.",
                         "Where should I book a birthday dinner in {p} that feels special?"),
    ("family",           "What are good family-friendly restaurants in {p} for dinner with young kids?",
                         "Where can I take my parents and kids for a sit-down dinner in {p}?"),
    ("group",            "Which restaurant in {p} works well for a group dinner of 10 people?",
                         "I need a restaurant in {p} that can seat a party of 12. Where should I book?"),
    ("business",         "What is the best restaurant in {p} for a business dinner with a client?",
                         "Where should I take a client to lunch in {p}?"),
    ("brunch",           "What are the best brunch spots in {p}?",
                         "Where should I go for weekend brunch in {p}?"),
    ("budget",           "Where can I get a great dinner for under $25 a person in {p}?",
                         "What are the best cheap eats in {p}?"),
    ("signature_dish",   "Where is the best {dish} in {p}?",
                         "Who makes the best {dish} in {p}?"),
    ("visitor",          "I'm visiting {p} for one night. Where should I eat dinner?",
                         "I have one dinner in {p} this weekend. Which restaurant should I pick?"),
]

# (area label, phrase used inside the prompt). Index order matters: see construction rule.
MARKETS = {
    "nyc": {"prefix": "NYC", "region": "New York City", "dish": "pizza", "areas": [
        ("Astoria", "Astoria, Queens"),
        ("West Village", "the West Village in Manhattan"),
        ("Upper West Side", "the Upper West Side of Manhattan"),
        ("Williamsburg", "Williamsburg, Brooklyn"),
        ("Flushing", "Flushing, Queens"),
        ("Midtown Manhattan", "Midtown Manhattan"),
        ("Park Slope", "Park Slope, Brooklyn"),
        ("Harlem", "Harlem in Manhattan"),
        ("Arthur Avenue", "the Arthur Avenue area of the Bronx"),
        ("St. George", "St. George, Staten Island"),
    ]},
    "ma": {"prefix": "MA", "region": "Massachusetts", "dish": "seafood", "areas": [
        ("North End", "the North End in Boston"),
        ("Back Bay", "Back Bay in Boston"),
        ("Cambridge", "Cambridge, Massachusetts"),
        ("Seaport", "the Seaport District in Boston"),
        ("Worcester", "Worcester, Massachusetts"),
        ("Springfield", "Springfield, Massachusetts"),
        ("Somerville", "Somerville, Massachusetts"),
        ("Lowell", "Lowell, Massachusetts"),
        ("Provincetown", "Provincetown, Massachusetts"),
        ("Salem", "Salem, Massachusetts"),
    ]},
    "de": {"prefix": "DE", "region": "Delaware", "dish": "crab cakes", "areas": [
        ("Dover", "Dover, Delaware"),
        ("Newark", "Newark, Delaware"),
        ("Middletown", "Middletown, Delaware"),
        ("Lewes", "Lewes, Delaware"),
        ("Bethany Beach", "Bethany Beach, Delaware"),
        ("Wilmington", "Wilmington, Delaware"),
        ("Hockessin", "Hockessin, Delaware"),
        ("Milford", "Milford, Delaware"),
        ("Rehoboth Beach", "Rehoboth Beach, Delaware"),
        ("New Castle", "New Castle, Delaware"),
    ]},
    "ct": {"prefix": "CT", "region": "Connecticut", "dish": "pizza", "areas": [
        ("Hartford", "Hartford, Connecticut"),
        ("West Hartford", "West Hartford, Connecticut"),
        ("Greenwich", "Greenwich, Connecticut"),
        ("Middletown", "Middletown, Connecticut"),
        ("Norwalk", "Norwalk, Connecticut"),
        ("Stamford", "Stamford, Connecticut"),
        ("Westport", "Westport, Connecticut"),
        ("Danbury", "Danbury, Connecticut"),
        ("New Haven", "New Haven, Connecticut"),
        ("Mystic", "Mystic, Connecticut"),
    ]},
}


def build(market):
    m = MARKETS[market]
    assert len(m["areas"]) == 10 and len(INTENTS) == 10
    rows = []
    for slot in range(1, 21):
        i = (slot - 1) % 10
        phrasing = "A" if slot <= 10 else "B"
        intent_i = i if phrasing == "A" else (i + 5) % 10
        intent, text_a, text_b = INTENTS[intent_i]
        area, phrase = m["areas"][i]
        text = (text_a if phrasing == "A" else text_b).format(p=phrase, dish=m["dish"])
        rows.append({"prompt_id": "%s%02d" % (m["prefix"], slot), "region": m["region"], "area": area,
                     "intent": intent, "slot": slot, "phrasing": phrasing, "text": text})
    return rows


def main():
    here = Path(__file__).resolve().parent
    targets = {mk: here / ("%s_restaurant_prompts_v1.jsonl" % mk) for mk in MARKETS}
    existing = [str(p) for p in targets.values() if p.exists()]
    if existing:
        sys.exit("REFUSE: exists, versioned new paths only: %s" % ", ".join(existing))
    for mk, path in targets.items():
        rows = build(mk)
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        print("WROTE %s ROWS %d" % (path.name, len(rows)))


if __name__ == "__main__":
    main()
