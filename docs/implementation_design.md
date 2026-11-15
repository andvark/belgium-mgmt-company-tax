# Implementation design (as built, 15 November 2026)

## Relationship to `belgium_abm`

`mgmt_tax` is a separate package. It imports one module from `belgium_abm` (`engines.crn`, counter-based common random numbers keyed by seed, stream, year and replicate id) and nothing else. `belgium_abm` is not modified: the research project has read access only, and the corrections of `research_plan.md` section 6c (allowance as a reduction after the brackets, surcharge, employer cost, two-rate corporate tax, dividend regimes, vintaged reserve, policy path) are implemented here as pure vectorised functions that the population model can call in WP3/4. Whether to upstream them into `belgium_abm` is a decision for the owner.

## Layout

| path | content |
|---|---|
| `configs/policy_be_2026_supplied.yaml` | every statutory rule: id, value, status (`supplied`, `interpretation`, `open`, `scenario`; never `checked` yet), source, `hand_check` |
| `configs/assumptions.yaml` | non-statutory inputs (status `assumed`) |
| `src/mgmt_tax/policy.py` | loader; `Policy.v(id)` records which rules a calculation used; `PolicyPath` = rules by calendar year (baseline plus dated overrides, overridden rules get status `scenario`) |
| `tax/pit.py` | brackets, then minus 25% x 11,550, then x 1.072 |
| `tax/contributions.py` | employee 13.07%, employer 25%, employer cost, self-employed tiers with net-of-contribution base and annual minimum |
| `tax/corporate.py` | two rates, pay condition (EUR 51,000 or profit before pay if lower; periods 1-4 exempt) |
| `tax/distributions.py` | dividend rates, liquidation-reserve levy and withholding, anti-abuse, ordinary liquidation |
| `reserves.py` | vintaged liquidation-reserve account with the lock |
| `arrangements.py` | employee and sole-trader simulations; household liquidity; private wealth |
| `strategies.py` | one-person BV with owner strategies, liquidity constraint, interim lumps, final exit |
| `shocks.py` | paired shocks (revenue multipliers, replicate mean rescaled to 1) |
| `compare_a.py` | grid runner and summary tables with paired differences |
| `scripts/` | `run_comparison_a.py`, `make_report_a.py` |

## Accounting identity

Every year, for every arrangement, strategy and replicate:

revenue + company interest + private interest = administrative costs + all taxes and contributions + owner spending need + change in private wealth + change in company equity.

The residual is stored and tested (< 1e-6; observed about 1e-9). Over the horizon, with zero return, total revenue = administrative costs + all taxes and contributions + total spending + final wealth.

## Owner strategy

A strategy is (pay rule, vehicle, dividend regime, interim lump year, final exit). Pay rules: `threshold` (pay min(51,000, profit before pay)), `liquidity` (smallest pay whose net covers the household need, found by bisection on a monotone function), `fixed`, `full`. Vehicles: annual distribution, free reserve, liquidation reserve. The household liquidity gap is financed by a dividend out of current post-tax profit plus the free reserve; any residual gap is recorded. The strategy set is fixed in code; `BV_BEST` is chosen per cell by mean terminal wealth.

## Tests (44)

- `tests/unit/test_worked_examples.py`: hand-computed examples (see `worked_examples.md`), policy path by calendar year, vintaged lock.
- `tests/invariants/test_invariants.py`: ledger reconciliation for every arrangement and strategy, 4 households, 2 company ages, 2 returns; conservation of resources; the allowance-as-reduction identity; monotone and continuous tax and contribution functions; BV with full pay equals a sole trader with the same costs; a no-op policy path reproduces the baseline; paired shocks; wealth increasing in profit level; exit-cost ordering and lock mechanics with exact arithmetic; pay solver; every rule has a source and a declared status; unmodelled condition raises.
- Marker `unconfirmed`: the tests check the engine against the *supplied* rules; no official published example was available, so passing tests do not confirm the rules.
