## Referral-surface presence (deterministic pre-pass)

Canon `referral_surfaces_v0.1` · sha256 `8655137737de2e0e…` · rows clean 191 of attempted 210 · status **UNVALIDATED_PARSE_PENDING_KAPPA**

### Behavior modes per cell

| engine | search | family | NAMES | REFERS | REFUSES | OTHER | n | naming-sparse |
|---|---|---|---|---|---|---|---|---|
| anthropic | unknown | buyer_intent | 7 | 28 | 0 | 6 | 41 | **YES** |
| anthropic | unknown | category | 25 | 5 | 0 | 11 | 41 | no |
| anthropic | unknown | comparison | 12 | 0 | 0 | 13 | 25 | no |
| anthropic | unknown | long_tail | 0 | 3 | 0 | 39 | 42 | **YES** |
| anthropic | unknown | problem | 0 | 21 | 0 | 21 | 42 | **YES** |

### Surfaces the engine routes buyers to

| surface | engine | family | count/n | low-n | subject presence |
|---|---|---|---|---|---|
| journalist_matching | anthropic | buyer_intent | 16/41 |  | NOT_MEASURED |
| professional_directory | anthropic | buyer_intent | 8/41 |  | NOT_MEASURED |
| review_marketplace | anthropic | buyer_intent | 9/41 |  | NOT_MEASURED |
| trade_press | anthropic | buyer_intent | 2/41 | yes | NOT_MEASURED |
| media_database | anthropic | buyer_intent | 14/41 |  | NOT_MEASURED |
| peer_referral | anthropic | buyer_intent | 8/41 |  | NOT_MEASURED |
| journalist_matching | anthropic | category | 2/41 | yes | NOT_MEASURED |
| professional_directory | anthropic | category | 1/41 | yes | NOT_MEASURED |
| review_marketplace | anthropic | category | 7/41 |  | NOT_MEASURED |
| trade_press | anthropic | category | 5/41 |  | NOT_MEASURED |
| media_database | anthropic | category | 4/41 |  | NOT_MEASURED |
| peer_referral | anthropic | category | 1/41 | yes | NOT_MEASURED |
| journalist_matching | anthropic | long_tail | 1/42 | yes | NOT_MEASURED |
| media_database | anthropic | long_tail | 1/42 | yes | NOT_MEASURED |
| peer_referral | anthropic | long_tail | 2/42 | yes | NOT_MEASURED |
| journalist_matching | anthropic | problem | 18/42 |  | NOT_MEASURED |
| professional_directory | anthropic | problem | 3/42 |  | NOT_MEASURED |

Subject presence is measured separately and supplied via `--presence`; NOT_MEASURED is printed, never guessed.
