# Research plan

## 1. Questions and hypotheses

| id | question | working hypothesis | how it would be rejected |
|---|---|---|---|
| Q1 | How large is the tax advantage of a one-person company over employment or sole-trader status today, and who gets it? | Large for owners who pay themselves roughly the minimum needed for the reduced rate, retain the rest and extract it later at the reduced dividend rate | The three-arrangement comparison shows no material lifetime advantage at realistic profit levels |
| Q2 | How much of that advantage do the proposals remove? | Proposal 1 removes up to 5 pp x EUR 100,000 per year of corporate-level advantage; proposals 2-3 matter mostly for retain-and-extract strategies | Advantage unchanged for the typical owner |
| Q3 | Does the number of entrepreneurs fall, and by how much? | It falls, with the size set by an unknown sensitivity of the choice of arrangement to the net advantage | Net advantage falls but the stock of companies does not respond |
| Q4 | What happens to wealth distribution? | Owner-manager households accumulate less tax-sheltered wealth; the national distribution barely moves (bounded by the no-management-companies scenario) | The bounding scenario already moves national inequality materially |
| Q5 | What happens to the budget? | Static revenue gain is partly offset by behavioural responses and by deferral (reserves are released after a waiting period) | Behavioural offset is negligible, or revenue falls |

A by-product that answers a policy-relevant question without any elasticity: **the break-even sensitivity** at which behavioural
responses would cancel the government's projected EUR 450 million.

## 2. The comparisons

The study is organised around the three legal arrangements for the *same* economic activity and one population-level extreme.

| comparison | what | level | output |
|---|---|---|---|
| **A. Three arrangements, current law (2026)** | Employee vs sole trader (natural person) vs one-person BV with a tax-minimising owner strategy, same productivity, same household, same starting assets | micro, lifetime and annual, by profit level (e.g. EUR 40k to 250k) and household type | net income, pension entitlement, retained and private wealth, total tax and contributions paid, risk (paired shocks) |
| **B. Three arrangements, each proposal** | The same comparison under proposal 1, proposal 2, proposal 3 and all three combined, with start dates (2027 / 2028) | micro | change in the BV advantage by profit level; break-even profit level; who is affected (heatmap) |
| **C. Population scenarios** | Baseline vs proposals with an explicit choice of arrangement, entry and exit; plus **"no management companies"** (every owner becomes an employee or sole trader) as a bounding experiment | macro-micro (population of workers) | entrepreneur counts, budget path by tax type and year, wealth distribution (owner-manager group and national), winners and losers |

*Interpretation note:* "3 comparisons" is read here as the three-arrangement comparison (A, B) feeding the population scenarios (C),
with "no management companies" as the bounding case. If a different set was meant (e.g. the three proposals separately), the plan
accommodates it: B already runs each proposal alone and combined.

## 3. What has to be modelled (and what exists in `belgium_abm`)

| element | status in `belgium_abm` | needed here |
|---|---|---|
| Personal income tax | illustrative brackets, flat allowance | Belgian 2026 schedule (rates 25/40/45/50 given; **thresholds missing**), allowance (conflicting figures, see `rules_inputs.md`), average municipal surcharge, household allowances |
| Social contributions | one flat self-employed rate with minimum | 20.5% / 14.16% with ceilings and the minimum quarterly amount; **employee and employer contributions missing** for the employee comparator; company annual contribution |
| Corporate tax | one flat rate | 25% standard, 20% on the first EUR 100,000 **conditional on director remuneration** (EUR 51,000 indexed threshold, with exceptions); proposal 1 changes the condition |
| Dividends / reserves | flat 30%, fixed payout share, liquidation only at retirement | 30% standard, VVPRbis 18% (from 1 July 2026), liquidation reserve with 3-year lock (10% levy + 9.8%), liquidation at closure; proposals 2-3 conditions |
| Owner behaviour | fixed 60% pay share, 30% payout | **rule-based tax-minimising strategy with liquidity constraint**: remuneration level, retention, timing of extraction |
| Choice of arrangement | entry depends on wealth and education only | **net-advantage-driven choice** (logit) with calibrated taste term and a swept sensitivity parameter |
| Hiring one employee to keep the reduced rate | none | avoidance margin created by proposal 1: cost vs rate saving (rule details unverified) |
| Segment and sample | all BV owners, ~600 in a 20k sample | zero-employee BV owners; oversample or run a separate cohort |
| Policy timing | policy fixed over the run | policy path by calendar year (2027, 2028 start dates) |

## 4. Work packages

| WP | content | deliverable | dependency | acceptance test |
|---|---|---|---|---|
| **0. Rules and data** | Verify the supplied rules against primary sources; fill missing parameters; settle definitions (what is a "management company"); acquire counts | `rules_inputs.md` completed, `sources.yaml` statuses | project owner input | every rule has source, date, status |
| **1. Tax engine for the three arrangements** | Encode the verified rules as a versioned policy; owner strategy with vintaged reserves (lock period) and liquidity constraint; household variants | policy file + unit tests with hand-computed worked examples | WP0 | reproduces published worked examples; invariants: no double counting, ledger reconciles |
| **2. Comparisons A and B** | Run the three arrangements under current law and each proposal over a grid of profit levels and household types, with paired shocks | tables, plots, break-even profit levels | WP1 | monotone sanity checks; BV advantage at the threshold behaves as the rules imply |
| **3. Choice of arrangement and calibration** | Entry/exit as a function of net advantage; calibrate taste term to the stock of zero-employee BVs and observed births and closures; sweep the sensitivity | calibrated module, sensitivity grid | WP1, WP2, data | baseline reproduces stock and flows within tolerance |
| **4. Population scenarios (comparison C)** | Baseline vs proposals vs no-management-companies, 2026-2040, replicates with common random numbers, static vs dynamic effect | scenario results with bands | WP3 | scenario with unchanged policy equals baseline; bounding scenario brackets the others |
| **5. Extension effects** | Add the economy-wide layers in order of cost: incidence, client substitution, macro consistency, relocation, capital-market effect (see `data_requirements.md`) | each layer switchable and reported as a sweep | WP4, data | with the layer off, results equal WP4 |
| **6. Validation** | Compare with the government's projected revenue, stock and flow counts, bunching of remuneration at the threshold if data exist | validation report | all | documented gaps, no result presented without its validation |
| **7. Reporting** | Report with scenario tables, break-even sensitivity, limitations | report, reproducible outputs | all | every table states policy version, vintage, weighting unit, uncertainty |

## 5. Outputs and metrics

- **Entrepreneurs:** stock and annual flows of zero-employee BVs, sole traders, employees in the same occupations; share that switch.
- **Budget:** annual revenue change by tax type (corporate tax, personal income tax, social contributions, dividend withholding), static vs dynamic, 2027-2040, including deferral; cumulative effect; **break-even sensitivity** against the government's EUR 300m / 450m.
- **Wealth:** owner-manager households (company retained equity and private wealth separately), national Gini and top shares, **pension entitlements shown separately** so that a shift to employment is not read as lost wealth.
- **Fairness:** net income of equal-productivity workers by arrangement before and after the proposals (horizontal equity).
- **Winners and losers:** by profit level, household type, region, age.

## 6. Design choices to settle

1. Population: one-person BV owners only, or all BV owners (default: zero-employee BVs, as the draft's rule applies to every company without staff).
2. Alternative arrangements: employee and sole trader (default: both).
3. Horizon: 2026-2040 (default), calendar-year policy path.
4. Optimisation: heuristic strategy (default) vs full dynamic programme (rejected for now: opaque and slow).
5. Household: individual taxation plus family allowances (default), partner income held fixed.
6. Scale: separate cohort calibrated to the real stock (default) vs oversampling in the full population.

## 7. Risks

- Rules supplied are partial and some conflict with other sources; results are only as good as WP0.
- The behavioural sensitivity is not identified from Belgian data; conclusions on entrepreneur numbers are conditional (see `limitations.md`).
- The draft is still being negotiated: parameters (notably the payroll multiple in proposal 2) are open, so scenarios must be parameterised, not hard-coded.
- The count of "management companies" is uncertain (see `evidence_found.md`): calibration targets may be wrong by a large factor.
