# 15 · PILOT CODING SHEET — ten PR firms
## 2026-08-29 · PILOT · n=10 · NOT A MATCHED STUDY · NEVER REPORTABLE AS A FINDING
## RUNG: R0. Nothing coded. Sheet empty.

---

## WHAT THIS IS, AND WHAT IT IS NOT

Four firms were named by Claude across 191 responses. Six were named zero times.
This sheet asks one question: **do the eight sealed features vary between those groups
at all?**

**It is not the matched study.** 09 requires matching on category, size band, age band
and geography before any feature is looked at. None of that is done here. Firms are
matched on *category only*, which 09 calls "a confound with paperwork" when the other
three are relaxed. That criticism applies to this sheet and is not waived.

**What it is for:** deciding whether the 150-hour coding arm is worth funding, and
whether any technique from the GEO literature predicts the split. One hour, no credits.

---

## THE ARITHMETIC THAT GOVERNS EVERY CONCLUSION

At 4 vs 6, one-tailed Fisher exact [MEASURED: computed 2026-08-29]:

| Split (visible / not-visible) | p |
|---|---|
| 4/4 vs 0/6 | 0.0048 |
| 4/4 vs 1/6 | 0.0238 |
| 3/4 vs 0/6 | 0.0333 |
| 4/4 vs 2/6 | 0.0714 |
| 3/4 vs 1/6 | 0.1190 |
| 2/4 vs 0/6 | 0.1333 |

**Eight features are being tested. Bonferroni-corrected bar is 0.05/8 = 0.00625.**

**Only a perfect 4/0 split clears it.** Every other pattern in the table is noise at
this sample size, including 3/4 vs 0/6 which will look convincing and is not.

Write this down before coding, because after coding a 3/1 split will feel like a
finding. It is not one. This table is sealed as of this document's date.

---

## STEP 0 — VERIFY THE FOUR BEFORE CODING ANYTHING

The four "visible" firms came from an unseeded regex over raw response text. **Not one
has been verified as a real PR agency, and none has been checked for the context of
its mention.** A firm named inside a warning ("avoid firms like X") is not visible in
the sense this sheet assumes — it is the opposite, and coding it as a case would
invert the whole result.

Run this before anything else:

```
:
cd ~/caai-test/ai-visibility-audit/study2
python3 - <<'PY'
import json,re
clean=[r for r in (json.loads(l) for l in open("data/pr_agency_run4.jsonl") if l.strip()) if r.get("response_text")]
for name in ["Clarity PR","Reputation Ink","Reputation Rhino","Brandstyle Communications"]:
    hits=[r for r in clean if re.search(re.escape(name),r["response_text"],re.I)]
    print("\n=== %s — %d of %d responses ==="%(name,len(hits),len(clean)))
    for r in hits[:3]:
        t=r["response_text"]; i=re.search(re.escape(name),t,re.I).start()
        print("  [%s] ...%s..."%(r["prompt_id"], t[max(0,i-180):i+180].replace("\n"," ")))
PY
```

**Read the excerpts yourself.** For each of the four, record one of:

    RECOMMENDED   named as a firm to consider or hire
    NEUTRAL       named in passing, as an example, or in a list without endorsement
    WARNED        named as a cautionary case
    NOT A FIRM    the string is not an agency (a person, a product, a false positive)

Any firm coded NOT A FIRM or WARNED is **removed from the visible set** and the sheet
is re-derived at the smaller n. If fewer than 3 survive, the arithmetic above collapses
and this pilot is abandoned rather than run at n=3 vs 6.

---

## STEP 1 — THE TEN FIRMS

**Visible group (mention rate, n=191, Claude only, 2026-08-29):**

| Firm | Rate | Verified at Step 0? |
|---|---|---|
| Clarity PR | 11.5% | ☐ |
| Reputation Ink | 7.3% | ☐ |
| Reputation Rhino | 5.8% | ☐ |
| Brandstyle Communications | 5.2% | ☐ |

**Not-visible group (0 of 191 across all five families):**

| Firm | Rate |
|---|---|
| Credible PR | 0.0% |
| Society22PR | 0.0% |
| Medical Marketing Firm | 0.0% |
| True North Social | 0.0% |
| Brenton Way | 0.0% |
| Reputation Pros | 0.0% |

The five non-Credible names come from 07 §5, dated 2026-08-27, itself
[REPORTED: web search, not verified page-by-page]. If any is not a live PR firm with a
working site, drop it and record the drop.

---

## STEP 2 — THE BLINDING PROBLEM, STATED HONESTLY

**You cannot blind yourself. You saw the results twenty minutes before this sheet
existed.** 09 calls blinding "the single cheapest quality control in the entire study."
It is not available here, and no shuffle fixes that.

Three partial mitigations, all cheap:

1. **Code in the shuffled order printed below**, not grouped by outcome.
2. **Code N1 and N2 first**, before F1–F8. They are the negative controls; if they
   track the outcome, you are coding with the answer in mind and the run is void.
3. **Best option: hand the shuffled list to someone else.** Anyone who can follow
   the definitions. One hour of their time converts this from unblinded to blinded
   and is the difference between hypothesis-generating and void.

**Whatever happens, the output carries the line: `BLINDING: NOT ACHIEVED` unless a
second person coded it.** That line travels with every number from this sheet.

**Shuffled coding order:**

    1. Brenton Way
    2. Clarity PR
    3. Medical Marketing Firm
    4. Reputation Rhino
    5. Credible PR
    6. Brandstyle Communications
    7. Reputation Pros
    8. True North Social
    9. Reputation Ink
    10. Society22PR

---

## STEP 3 — THE FEATURES

Adapted from the sealed F1–F8. Where a definition changed from the cosmetic-practice
version, that is marked ADAPTED and the change is stated. Definitions are dated before
any coding begins.

| ID | Feature | How to check it, exactly |
|---|---|---|
| **F1** | Third-party comparative coverage | Search `<firm> vs` and `best PR agencies` on Google. Score 1 if ≥3 comparison or round-up pages on domains the firm does not own appear on page one. Own blog and own press releases score 0. |
| **F2** | Published explicit prices | Open the site. Score 1 if a price, retainer range, or package figure is visible without a form, call booking, or email. |
| **F3** | Dated recency | Score 1 if ≥1 substantive page (blog, guide, case study) carries a visible date within 90 days. |
| **F4** | Explicit intent match | Score 1 if the firm owns ≥1 page whose visible heading answers a buyer question in buyer language — "how to get featured in Forbes", "how much does PR cost". A services page does not count. |
| **F5** | Structured markup | View source, search `schema.org`. Score 1 if `Organization`, `Service`, `Review`, or `FAQPage` type is present. ADAPTED: cosmetic version used `LocalBusiness`/`Physician`; PR firms are service businesses, often national. |
| **F6** | Third-party review volume | Score 1 if ≥25 reviews on a platform the firm does not control (Google, Clutch, Trustpilot, G2). ADAPTED: threshold lowered from 1,000 — B2B service firms operate at a different review scale than consumer brands. |
| **F7** | Named entity authority | Score 1 if the site names ≥1 identifiable person with a bio and credentials on a dedicated page — founder, senior practitioner. A team grid with names only scores 0. |
| **F8** | Independent directory presence | Score 1 if listed on ≥2 of: Clutch, G2, Agency Spotter, O'Dwyer's, PRSA member directory. ADAPTED: cosmetic version used medical boards. |
| **N1** | Keyword density *(negative control)* | Homepage source contains "PR agency" or "public relations" ≥8×. **Expected NOT to vary with visibility.** |
| **N2** | Superlative self-description *(negative control)* | Homepage uses "#1", "best", "leading", "top-rated" without third-party attribution. **Expected NOT to vary.** |

---

## STEP 4 — THE SHEET

Code in the shuffled order. 1 or 0. No notes, no half-marks. **N1 and N2 first.**

| # | Firm | N1 | N2 | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Brenton Way | | | | | | | | | | |
| 2 | Clarity PR | | | | | | | | | | |
| 3 | Medical Marketing Firm | | | | | | | | | | |
| 4 | Reputation Rhino | | | | | | | | | | |
| 5 | Credible PR | | | | | | | | | | |
| 6 | Brandstyle Communications | | | | | | | | | | |
| 7 | Reputation Pros | | | | | | | | | | |
| 8 | True North Social | | | | | | | | | | |
| 9 | Reputation Ink | | | | | | | | | | |
| 10 | Society22PR | | | | | | | | | | |

---

## STEP 5 — HOW TO READ IT

Four outcomes, sealed before coding.

**A · No feature splits 4/0.** The features do not discriminate at this sample.
The coding arm is not worth 150 hours as currently specified. Redesign the feature set,
or accept that the separating variable is not on this list. **This is the most likely
outcome and it is a real result.**

**B · Exactly one feature splits 4/0.** It clears the corrected bar. It becomes the
single primary for a real matched study at n=25 pairs. It is a hypothesis, not a
finding — n=10, unmatched, unblinded.

**C · Several features split 4/0.** Suspect a common cause rather than several
mechanisms. Most likely explanation is firm size or age, which was never matched on.
Check company age and headcount for all ten before believing any of it.

**D · N1 or N2 splits 4/0.** **STOP.** The negative controls are supposed to be flat.
Either the definitions leak outcome information or the coding was done with the answer
in mind. Debug before proceeding. This is the only row that can catch a broken
instrument, and it is the reason they are coded first.

---

## WHAT NO OUTCOME LICENSES

- **No causal verb.** Cross-sectional, n=10. Write "co-occurs with", "differs between".
  Never "drives", "causes", "gets you cited".
- **No claim that a feature would move Credible PR's rate.** That requires the
  before/after intervention study, which is separate work.
- **No sentence beginning "we found that F_n separates."** Not from this sheet, under
  any outcome, in any document.
- **One engine, one day, one category.** Claude only; ChatGPT and Grok are not wired.
- **The extractor is unvalidated.** The visible group was found by regex with no κ, and
  four real agencies were missed by the seeded roster on the same run.
- **`BLINDING: NOT ACHIEVED`** unless a second person coded it.

---

## AFTER

If outcome B: the next step is the matched design at n=25 pairs, and the category should
be PR agencies rather than cosmetic practices — you now hold a measured baseline here
and a live counterparty who is in the not-visible group.

If outcome A: publish it. Zero of eight features separating visible from invisible firms
is the null reproduced on original data, and nobody in this category will publish that.

---

RUN LOG
    CODED ....... 0 of 10
    CODER ....... unassigned
    BLINDED ..... NO
    STATUS ...... R0. Sealed, never executed.
