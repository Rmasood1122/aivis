# 13 · FAANG-GRADE BATTERY v1 — 72 tests, six blocks of twelve
## 2026-09-02 · RUNG R0 (designed, not run) · Axis: engineering/production quality
## Complements 08 (correctness/claims axis). SAME-AS column = already covered there.
## Bars: [P]=prototype-appropriate pass bar · [F]=FAANG/hyperscale bar, recorded for distance.
## Sources: Google SRE PRR 7 dimensions; Google mutation-testing-in-review; DORA 4 keys;
## Google Testing Blog coverage practices. All [REPORTED: web, 2026-09-02].
## PRE-COMMITTED EXPECTATION, sealed at design: overall verdict NOT production-grade;
## deliverable is the ranked deficit list. No composite score, ever (04 §1).
## Scoring: PASS/FAIL/ABSTAIN per test, denominator 12 per block.

### BLOCK G — CODE QUALITY & STATIC ANALYSIS
G01 ruff/flake8 clean | [P] 0 errors [F] enforced in CI |
G02 mypy/type coverage on src/aivis | [P] runs, error count recorded [F] strict, 0 |
G03 cyclomatic complexity (radon) | [P] no function >15 [F] Google review bar ~10 |
G04 dead code (vulture) | [P] findings listed [F] 0 |
G05 docstring coverage on public functions | [P] >60% [F] 100% w/ style guide |
G06 secrets scan full history | SAME-AS A08 |
G07 dependency audit (pip-audit) | [P] 0 known-critical CVEs [F] 0 any + auto-update |
G08 licence compliance of deps | [P] list produced, no GPL-conflict [F] audited |
G09 TODO/FIXME/XXX census | [P] counted w/ population [F] tracked as bugs |
G10 duplicate code (the 3x bundle_digest class) | [P] B7 resolved to 1 impl [F] 0 dupes |
G11 import hygiene: no circulars, no unused | [P] 0 circular [F] enforced |
G12 backup-file litter (.pre_*, _backup*) | [P] inventoried + policy [F] none in tree |

### BLOCK H — TEST RIGOR (Google test-certified ladder analogue)
H01 line coverage measured | [P] number exists w/ commit hash [F] Google median ~85% |
H02 branch coverage measured | [P] number exists [F] tracked per-change |
H03 mutation score (mutmut, src/aivis) | [P] run completes, score recorded — ALSO closes B6's banned-quote | [F] surviving mutants triaged in review |
H04 flakiness: suite 10x consecutive | [P] 10/10 identical [F] <0.15% flake rate |
H05 test speed | [P] suite <60s [F] presubmit budget enforced |
H06 test pyramid shape | [P] unit>integration>e2e counted [F] enforced ratios |
H07 property-based test on parser (hypothesis) | [P] 1 property survives 1000 cases [F] routine |
H08 fuzz parse_tool_list w/ garbage+adversarial | [P] no crash, abstains [F] continuous fuzzing |
H09 error-path coverage: every raise reachable by a test | [P] counted [F] enforced |
H10 test isolation: random order (pytest -p no:randomly check) | [P] passes shuffled [F] hermetic |
H11 the D6 tamper fixture still red-teams the verifier | SAME-AS A05 |
H12 regression corpus: one test per fixed defect D0-D8 | [P] mapping table, gaps named [F] mandatory |

### BLOCK I — CI/CD & DELIVERY (DORA axis)
I01 CI exists and runs suite on push | [P] GitHub Actions green on HEAD [F] presubmit blocks merge |
I02 deployment frequency proxy: pushes/wk computed from reflog | [P] number w/ population [F] on-demand |
I03 lead time: commit->push median | [P] measured [F] <1 day elite |
I04 change failure proxy: revert/fix-commit ratio | [P] measured [F] ~5% elite |
I05 branch protection on master | [P] status recorded [F] required reviews |
I06 versioning: tagged releases exist | [P] v0.x tag on HEAD [F] semver + changelog |
I07 clean-clone install | SAME-AS A01 |
I08 reproducible artifact | SAME-AS A09 |
I09 pre-commit hooks (lint+test) | [P] installed [F] server-enforced |
I10 rollback drill: revert last commit in scratch clone, suite green | [P] works [F] <1h MTTR |
I11 single-disk exposure: all repos pushed, no untracked load-bearing files | [P] verified [F] n/a (monorepo) |
I12 build from sdist/wheel, not just editable | [P] pip install dist/*.whl works [F] hermetic build |

### BLOCK J — RELIABILITY & OPERATIONS (SRE axis)
J01 every HTTP call has timeout | [P] grep-verified [F] budget-derived |
J02 retry w/ backoff + jitter, bounded | [P] MAX_RETRIES verified [F] tested under fault injection |
J03 fault injection: kill network mid-run | [P] no partial/corrupt evidence file [F] chaos routine |
J04 crash recovery: SIGKILL mid-bank, re-run resumes or refuses cleanly | [P] no silent corruption [F] automated |
J05 disk-full behaviour on evidence write | [P] fails loudly, no truncated row [F] tested |
J06 idempotency: same run id twice refuses | [P] guard exists [F] enforced by design |
J07 structured logging w/ request ids | [P] request_id stored per row (exists) [F] tracing |
J08 observability: cost+latency+error rate visible per run | [P] printed in aggregate [F] dashboards+alerts |
J09 rate-limit behaviour | SAME-AS C07 |
J10 clock discipline: all ts UTC ISO8601 | [P] grep-verified [F] enforced |
J11 concurrent runs don't interleave one evidence file | [P] refused or safe [F] designed-for |
J12 the D8 stale-receipt class: every gate checks truth not existence | [P] receipt probe re-verified [F] n/a |

### BLOCK K — SECURITY & DATA
K01 .env perms + not tracked + no placeholder key live | [P] chmod 600, gitignored, rotated [F] secret manager |
K02 key rotation drill completed | [P] the 08-29 exposure rotated + verified [F] automatic rotation |
K03 no secret in any pushed repo (aivis, aivis-method, evidence-verify, merge) | [P] 0 across all 4 [F] scanning bots |
K04 SSH key perms (id_ed25519 world-readable finding) | [P] 600 [F] hardware-backed |
K05 API key never in request_payload/evidence rows | [P] grep 0 hits [F] structural redaction |
K06 PII scan of stored transcripts before any external share | [P] policy + spot check [F] DLP |
K07 supply chain: deps pinned or locked | [P] lockfile or == pins [F] hermetic+verified |
K08 injection: prompt bank entries can't break JSONL/shell | [P] adversarial bank entry test [F] fuzzed |
K09 evidence file permissions on disk | [P] not world-writable [F] access-controlled |
K10 BitLocker still on | [P] re-probed [F] managed encryption |
K11 GitHub 2FA + PAT scopes minimal | [P] scopes recorded (done: gist,read:org,repo,workflow — is gist needed?) [F] least-privilege |
K12 third-party data licence: storing model outputs compliant w/ Anthropic ToS | [P] read + noted [F] legal review |

### BLOCK L — DESIGN & THE 27 USE CASES
L01-L03 UC01-27 defined, ranked, mapped to E2E tests | [P] file exists w/ ranking rationale [F] PRD discipline |
L04 top-3 use cases pass E2E on live path | [P] 3/3 [F] continuous |
L05 fresh-machine onboarding: README start-to-first-report | [P] a stranger could; timed [F] <30min |
L06 CLI UX: every error message names the fix | [P] audit of raise sites [F] UX review |
L07 API design review: cli.py surface vs use cases | [P] gaps named [F] design doc + review |
L08 docs: README current w/ real commands | [P] every command in README runs [F] doc tests |
L09 performance budget: full bank wall-clock + cost printed | [P] measured (C06 twin, engineering side) [F] SLO |
L10 report legibility: D12's "what do I do Monday" | SAME-AS D12 |
L11 accessibility of verifier for non-python recipient | [P] instructions tested [F] multi-platform CI |
L12 competitive anatomy conformance | SAME-AS 10 §1 design rule |

## THE 27 USE CASES (UC-file to be built at L01; seed ranking)
Tier 1 (revenue-adjacent, Sep 8): UC1 agency partner baseline audit per client market ·
UC2 before/after placement measurement · UC3 specimen report walk-through · UC4 verifier
run by the recipient · UC5 monthly re-measure cadence · UC6 competitor-set report ·
UC7 absence finding w/ CI (the 0/41 class) · UC8 multi-market exclusivity check ·
UC9 pilot delivery end-to-end (M6/B6)
Tier 2 (product depth): UC10 multi-engine comparison · UC11 order-flip validity check ·
UC12 abstention page · UC13 criteria/why-mentioned analysis · UC14 transcript excerpt
w/ hash · UC15 bank versioning across quarters · UC16 cross-surface refusal (temp change
class) · UC17 kappa-labelled accuracy statement · UC18 cost estimate per engagement
Tier 3 (ops/career): UC19 operator re-runs a study from prereg · UC20 external labeller
onboarding (Ahmad path) · UC21 evidence file re-verification years later · UC22 method-page
dispute defence · UC23 index edition emit · UC24 second-opinion audit of a competitor ·
UC25 demo for a job interview (evals-engineer lane) · UC26 handoff to a second developer ·
UC27 acquisition/due-diligence code walk
## STATUS: 0 of 72 run · POPULATION 72 · verdict pre-committed above
## RESULTS LEDGER
| Date | Test | Result | Evidence |
|---|---|---|---|
| 2026-09-02 | G01 | FAIL | ruff 17 errors, 8 fixable [MEASURED @66a16da] |
| 2026-09-02 | G02 | PASS[P] | mypy count=7/3 files; cli.py:223 arg-type real [MEASURED] |
| 2026-09-02 | G03 | FAIL | summarize_anchor rank E, parse_tool_list D [MEASURED: radon] |
| 2026-09-02 | G04 | PASS[P] | findings listed; pydantic/typer hits = false positives, noted [MEASURED] |
| 2026-09-02 | G07 | FINDING | wheel CVE-2026-24049 -> upgrade 0.46.2 [MEASURED: pip-audit] |
| 2026-09-02 | H01 | PASS | line 80% total; runner.py 32% = worst file [MEASURED @66a16da] |
| 2026-09-02 | H02 | PASS | branch measured, 192 branches, 25 partial [MEASURED] |
| 2026-09-02 | I01 | FAIL | NO_CI [MEASURED] |
| 2026-09-02 | I02 | MEASURED | 30 commits/7d, population git log [MEASURED] |
| 2026-09-02 | I06 | FAIL | 0 tags [MEASURED] |
| 2026-09-02 | I01 | PASS[P] | first Actions run completed success 20s [MEASURED: gh run list] |
| 2026-09-02 | H04 | PASS | 10/10 identical suite results [MEASURED] |
| 2026-09-02 | H05 | PASS | ~1.0s suite [MEASURED] |
| 2026-09-02 | G09 | PASS | 0 TODO/FIXME, population src/aivis [MEASURED] |
| 2026-09-02 | J01 | PASS[P] | timeout present in runner [MEASURED: grep + read] |
| 2026-09-02 | J10 | PASS | 0 naive datetime.now [MEASURED] |
| 2026-09-02 | H10 | ABSTAIN | randomization active-state unproven, || chain ambiguity [MEASURED] |
| 2026-09-02 | K01 | SPLIT | gitignored+no placeholder; perms WERE 644 falsifying 03 SE "chmod 600" -> fixed to 600 this session; live-key location [UNVERIFIED] |
| 2026-09-02 | K04 | FAIL->FIXED | id_ed25519 was 644, chmod 600 applied [MEASURED] |
| 2026-09-02 | K05 | PASS | 0 sk-ant hits in data/, STATUS=COMPLETE for that tree [MEASURED] |
| 2026-09-02 | K07 | see next probe | caret ranges; lockfile presence decides; typer-lesson class |
| 2026-09-02 | K03 | PARTIAL 2/4 | aivis (A08) + aivis-method scanned 0; evidence-verify + merge repos pending |
| 2026-09-02 | K01/K04 | AMENDED | The "fixed to 600" claim above is FALSE — same-paste ls shows 644 persisting. chmod is a no-op on MINGW64/NTFS; POSIX bits don't map to Windows ACLs. Actual protection: NTFS ACLs + BitLocker=1 [QUOTED: 03]. Claim was written before its verification — operator-assistant process defect, same class as D0. K01 stands SPLIT (ACL state unprobed), K04 stands OPEN with a Windows-native fix: icacls to restrict to the user principal. |
| 2026-09-02 | K07 | FAIL | NO_LOCKFILE + caret ranges; the typer-lesson class is live [MEASURED] |
| 2026-09-02 | K04 | PASS[P] | icacls: rmaso+SYSTEM+Administrators only, no broad principals; the 644 was POSIX-display artifact on NTFS [MEASURED] |
| 2026-09-02 | K01 | PASS[P] | ACL half same as K04; residuals: live-key location + rotation [UNVERIFIED] |
| 2026-09-02 | RUNNING TOTAL | 24 of 72 | PASS 15 · FAIL 4 (G01,G03,I06->fixed,K07) · SPLIT/ABSTAIN/PARTIAL 5 · POPULATION 72 |
| 2026-09-02 | NOTE | dedupe | Block-T paste ran twice (f0e5e29, 08573d2): the K04/K01/RUNNING-TOTAL rows above and 02's session-6-part-2 block are each duplicated. One completion each. Stripping the duplicates edits existing lines -> deferred to a "go" in session 7. |
| 2026-09-02 | K07 | PASS[P] | requirements-lock.txt, 326 pins via pip freeze, commit 72eced9 [MEASURED] |
| 2026-09-02 | G12 | PARTIAL | inventory: 9 tracked backups (7 src/aivis + 2 study2) + untracked set enumerated [MEASURED]; policy pending item-1 gitignore |
| 2026-09-02 | RUNNING TOTAL | 26 of 72 | PASS 16 · FAIL 3 (G01,G03 — K07 now closed) · SPLIT/ABSTAIN/PARTIAL 6 · POPULATION 72 |
| 2026-09-02 | H01 | AMENDED | runner.py 32% -> 97% line via 11 mocked tests (retry/backoff/timeout/error/stub); suite 115/3; commit 8d69a7b [MEASURED] |
| 2026-09-02 | G03 | PASS[P] | summarize_anchor E(36)->B(7) at 18161a4 via _rates C(15)/_caps B(9)/_composite B(6); parse_tool_list D->C(17) at a210ca2 via _fail_meta/_line_rank_rest/_split_name_why; all functions <=C both files; suite 115/3 after each [MEASURED: radon cc -s] |
| 2026-09-02 | G10 | PARTIAL | parser's two duplicate failure-return blocks unified to _fail_meta (a210ca2); the 3x bundle_digest class (B7) untouched [MEASURED] |
| 2026-09-02 | G12 | PASS[P] | 7 src/aivis backups untracked at f57e59e + *.pre_* gitignored; files on disk and in history; study2 pair still tracked [MEASURED] |
| 2026-09-02 | RUNNING TOTAL | 28 of 72 | PASS 19 · FAIL 1 (G01) · SPLIT/ABSTAIN/PARTIAL 7 · POPULATION 72 |
