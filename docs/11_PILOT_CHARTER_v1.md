# 11 · PILOT CHARTER — Placement Impact Measurement (pre-registered)
## RUNG R0 (offer, not engagement) · 2026-09-01 · recipient: Sep 8 meeting
## Prices are proposals; willingness-to-pay is [REPORTED], not measured. B6 measures it.
WHAT IS MEASURED   Per client market: which providers AI assistants name, at what rate,
                   with 95% intervals, before a placement and at +30/60/90 days after,
                   against untreated competitors in the same metro.
SURFACE            Declared on every report: engine(s), model id, temperature. v1 is one
                   engine unless adapters land first; the gap is printed, never pooled.
POWER FLOOR        N >= 7 runs per combination · full 30-prompt bank per market ·
                   minimum detectable change printed on the face · below-power metrics
                   abstain rather than estimate.
EVIDENCE           Every response stored raw with its request payload and SHA-256.
                   Reports ship with the evidence file and a public, stdlib-only checker.
                   Tamper-evident, hash-verified. Nothing stronger is claimed.
NOT CLAIMED        No link to consultations or revenue is claimed at signing — measuring
                   whether one exists is the point. Extraction error is unmeasured until
                   the agreement study publishes; every report says so until then.
PRE-COMMITTED OUTCOMES (sealed before first measurement)
  POSITIVE  placements move AI answers -> jointly written case study, agency named.
  NULL      no detectable movement at the stated MDC -> agency learns first;
            reweighting guidance included in the deliverable.
  EITHER    client-identifiable results stay confidential; aivis retains the right to
            publish anonymized, aggregated findings. This clause is not negotiable —
            it is what funds the instrument's independence.
CONFOUNDING        Six concurrent services make attribution impossible. The study runs
                   on a staggered subset of placements; the stagger is the agency's one
                   operational cost and the charter names it up front.
ATTRIBUTION KIT    Intake adds "AI assistant" as a consult source, with the 30-second
                   front-desk script and a quarterly population check (all new consults;
                   unasked recorded as its own category). Their data, their systems.
PRICE              Founding engagements (first 3): $2,500/quarter per market, in
                   exchange for named case-study rights. List thereafter: $5,000/quarter.
DEFEATED-BY        Signing without the stagger (attribution dies) · skipping the intake
                   script (Join-2 returns nothing) · quoting any rate without its
                   denominator and interval (the charter's own rules apply to its output).

## AMENDED 2026-09-01 — session 6: stagger replaced by natural timing variation
SUPERSEDES the CONFOUNDING clause above. The staggered subset asked the agency to
delay revenue-bearing work — the one clause that made the charter expensive to sign.
Replacement: placements across a book of clients already land on DIFFERENT dates
without anyone delaying anything. That existing spread IS the stagger, free.
DESIGN      Each placement's date is recorded as it naturally occurs. Markets whose
            placement lands in month k are compared against markets untreated as of
            month k — the same before/after joins, using variation the business
            already produces.
COST        The agency delays nothing and delivers nothing early. Their only
            operational ask is now the intake script (attribution kit, above).
HONEST      Natural timing is not random assignment. Placement dates may correlate
            with client readiness or seasonality; the report names this and controls
            against each market's own pre-period, per the original design.
DEFEATED-BY all placements landing in the same week (no spread, no contrast — the
            design degrades to a single before/after and says so on its face) ·
            selecting WHICH clients to measure after seeing early results (the
            measured set is fixed at signing).
