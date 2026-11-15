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

## Comparison B additions (proposals)

- `configs/proposals.yaml`: switches for P1, P2, P3 (status `scenario`, all off). `PolicyPath` turns them on from a calendar year (`compare_b.py` builds the scenario list).
- `strategies.simulate_bv` keeps the free reserve in two pools: `F_red` (amounts that keep the reduced regimes) and `F_ord` (amounts created in a year in which the P3 test binds). P2 is a yearly capacity (`cap`) consumed by reduced-regime dividends, allocations and reserve dividends. P1 is a flag on the reduced corporate rate plus the hire cost (an expense; its gross wage enters P2 payroll).
- `shocks.client_share_paths`: largest-client share by year (assumed process; 1.0 means one client); history before 2026 so the lookback is defined from the first year.
- With every switch off the refactored simulator reproduces the comparison A outputs exactly (max absolute difference 0 over all 10 cases).
- Strategy set for B: 28 (the 19 of A plus fixed pay 60k/80k/100k x {annual VVPRbis dividend, retain + VVPRbis lump after 5 years, liquidation reserve}). `BV_BEST` = best by mean terminal wealth (anti-abuse variants excluded); `BV_STATIC` = the strategy that was best under current law for that household and revenue level.
- Monotonicity checks (a proposal can only hurt a fixed strategy; tighter parameters hurt more) exclude two baseline-dominated strategies (`*_lr_div_k5`, `*_antiabuse`) that can gain when a proposal blocks an action that was costly for them.

## Tests

- `tests/unit/test_worked_examples.py`: hand-computed examples (see `worked_examples.md`), policy path by calendar year, vintaged lock.
- `tests/invariants/test_invariants.py`: ledger reconciliation for every arrangement and strategy, 4 households, 2 company ages, 2 returns; conservation of resources; the allowance-as-reduction identity; monotone and continuous tax and contribution functions; BV with full pay equals a sole trader with the same costs; a no-op policy path reproduces the baseline; paired shocks; wealth increasing in profit level; exit-cost ordering and lock mechanics with exact arithmetic; pay solver; every rule has a source and a declared status; unmodelled condition raises.
- `tests/unit/test_proposals.py`: hand-computed P1, P2, P3 cases (corporate tax with and without a hire, capped dividends at 2x and 3x, capped allocation, higher pay raising the cap, lookback window, threshold, grandfathering, hire start year).
- `tests/invariants/test_proposal_invariants.py`: ledger reconciliation under every proposal and combination, proposals only hurt a fixed (non-dominated) strategy pathwise, tighter parameters hurt more, employee and sole trader untouched, no effect on owners below the threshold.
- Marker `unconfirmed`: the tests check the engine against the *supplied* rules; no official published example was available, so passing tests do not confirm the rules.
