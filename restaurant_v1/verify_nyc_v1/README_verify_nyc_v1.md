# verify_nyc_v1 - checking the NYC names (working folder, RUNG R1)

Nothing in this folder is a result. It exists so a person can give each of the 131 names on
`../results_nyc_v2_merged/verify_sheet.csv` a verdict, as the pre-registration requires
("confirmed, by a human opening a primary source ... URL recorded").

| file | what it is |
|---|---|
| `verify_leads_assistant_v1.csv` | one row per sheet name: a link, an address and a note found by an AI assistant on 2026-10-07. UNCHECKED machine output. No verdict column. |
| `check_nyc_v1.html` | the same rows as a page: two links per name, five verdict buttons, a download button. Built by `../make_verify_page_v1.py`. Fills in no verdict. |
| `verified_nyc_v1_<stamp>.csv` | (added by the operator) the downloaded verdicts, given to the analyzer with `--verified`. |

## How the leads were gathered  [REPORTED: assistant session 2026-10-07]
- Five AI lookup agents, each given about 26 names, searched the web and read pages through a
  summarising fetch tool. They did not read raw pages, and Google Maps was not opened.
- Lead flags, POPULATION 131 sheet rows: ok 107, not_a_place 14, possibly_closed 5,
  possibly_wrong_area 4, ambiguous 1, not_found 0.
- 96 of 131 leads point at the place's own site; 25 at a listing (OpenTable, Yelp, other); 10 have no link
  (all 10 are flagged not_a_place).

## Second look by the assistant, same day  [REPORTED: same fetch tool, so not an independent route]
- possibly_closed (5): the source page was fetched again for 4 and the closure wording came back for
  4 of 4 (Absolute Bagels, Convivium Osteria, The Leopard at des Artistes, The Milling Room). For
  Full Moon Pizza a search found neither a closure nor the rename the lead suggests.
- ok (107): 8 drawn with `random.Random(20261007).sample`; a closure search or own-site fetch found
  no closure for 8 of 8. Search-result titles only for 6 of the 8, so this is a weak check.
- Known judgement calls: Absolute Bagels (original closed; an unaffiliated "New Absolute Bagels" is
  reported at the same address); Chela (two different restaurants share the name); Roberta's (flagship
  in Bushwick, a second location reported in Williamsburg); Astoria Seafood and Cevabdzinica Sarajevo
  (postal city "Long Island City", on the Astoria border).

## What a lead flag is not
`ok` means "the agent saw no closure wording", not "open". A flag is a pointer for the human, never a verdict.
