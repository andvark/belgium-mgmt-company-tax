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
| **0. Rules and data** | Confirm the supplied rules against primary pages (blocked from this session: list in `rules_inputs.md` section F); fill missing parameters; segment definition settled (S0, S1); counts partly checked | `rules_inputs.md` completed, `sources.yaml` statuses | project owner input | every rule has source, date, status |
| **1. Tax engine for the three arrangements** | Encode the supplied rules as a versioned policy (status per rule); owner strategy with vintaged reserves (lock period) and liquidity constraint; household variants | policy file + unit tests with hand-computed worked examples. **Done 15 Nov 2026**: `src/mgmt_tax`, 44 tests; see `docs/implementation_design.md`, `docs/worked_examples.md` | WP0 (rules still only *supplied*) | worked examples hand-computed (no published official examples were available); invariants: ledger reconciles every year, no double counting |
| **2. Comparisons A and B** (A and B done on supplied rules and scenario assumptions: `docs/comparison_A_results.md`, `docs/comparison_B_results.md`) | Run the three arrangements under current law and each proposal over a grid of profit levels and household types, with paired shocks | tables, plots, break-even profit levels | WP1 | monotone sanity checks; BV advantage at the threshold behaves as the rules imply |
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

## 6. Design choices (settled and open)

**Settled by the project owner (15 November 2026):** segment S1 = zero employees, single director, one client (S0 = zero employees only, reported alongside); alternatives = employee and sole trader; horizon 2026-2040.

Open (defaults in brackets):

1. Optimisation: heuristic strategy including **exit route and timing** (liquidation reserve at about 10% vs dividend after three years at about 18% vs 30% ordinary) (default) vs full dynamic programme (rejected for now).
2. Household: individual taxation with the EUR 11,550 allowance applied as a 25% tax reduction (EUR 2,887.50), partner income held fixed (default).
3. Scale: separate cohort calibrated to the real stock of S0 (about 351,000 zero-employee BV/SRL SMEs, unverified share) with S1 as a flagged fraction once its size is known (default) vs oversampling in the full population.

## 6b. Scenario grid

| scenario | definition |
|---|---|
| Baseline | current rules as supplied (see `rules_inputs.md`), start of policy path 2026 |
| P1 | reduced rate withdrawn for S0 from 2027 (20% -> 25% on first EUR 100,000); employee test open: sub-scenarios "no hire", "minimal hire at cost c" with take-up swept |
| P2 | dividend regimes require payroll >= 2x (or 3x) the dividend, from 1 January 2028; separate scenarios for 2x and 3x |
| P3 | reduced dividend regimes withdrawn for single-client single-director companies for new amounts from 2028; client threshold grid (for example 70, 80, 90, 100%) and lookback grid (3, 5 years) |
| Combined | P1 + P2 + P3 |
| No management companies | bounding case: S1 (and S0 as a variant) converted to employees or sole traders |

## 6c. Required corrections to the existing engine

- income-tax allowance as a 25% tax reduction after applying the brackets (currently deducted from income first);
- municipal surcharge (7.2% of income tax);
- employee comparison with 13.07% employee and 25% employer contributions, comparing contracting income with total employer cost;
- two-rate corporate tax with the director-remuneration condition;
- dividend regimes, vintaged liquidation-reserve account with a three-year lock, liquidation-route tax and the anti-abuse rule;
- policy path by calendar year.

## 7. Risks

- Rules supplied are partial and the primary pages could not be opened from this session; results are only as good as WP0.
- The drafts of P2 and P3 are known only through second-hand excerpts (2x/3x and 90% are scenario values); results must be labelled as scenarios, not as the proposal.
- The behavioural sensitivity is not identified from Belgian data; conclusions on entrepreneur numbers are conditional (see `limitations.md`).
- The draft is still being negotiated: parameters (notably the payroll multiple in proposal 2) are open, so scenarios must be parameterised, not hard-coded.
- The count of "management companies" is uncertain (see `evidence_found.md`): calibration targets may be wrong by a large factor.

## 8. Progress log

- **15 Nov 2026, WP1 and comparison A.** Engine built as a separate package (`mgmt_tax`) that imports only the common-random-number module of `belgium_abm`; `belgium_abm` itself is untouched (read-only for this project; the corrections of section 6c live in `mgmt_tax`, to be used when WP3/4 wire the population model). All section 6c corrections implemented: allowance as a 25% reduction after the brackets, 7.2% surcharge, 13.07%/25% with employer-cost comparison, two-rate corporate tax with the pay condition, dividend/liquidation-reserve/liquidation routes with anti-abuse flag, vintaged reserve with lock, policy path by calendar year (tested with a generic dated override; no proposal logic yet). Comparison A run on the supplied rules over 8 profit levels x 4 household types x 2 company ages x 19 BV strategies, 300 paired replicates, plus 9 one-at-a-time sensitivity cases. Results and caveats: `docs/comparison_A_results.md`. Values to confirm by hand: `docs/hand_check_list.md`.
- **15 Nov 2026, comparison B.** P1 (from 2027 and 2028), P2 at 2x and 3x (from 2028 and 2027), P3 over thresholds 70/80/90/100% x lookbacks 3/5 years and owner concentrations 100/95/90/80/70/50%, and combined scenarios, each with static (fixed strategy) and re-optimised (strategy, pay level, hire) owner responses, for three household types, on the same paired replicates as the baseline. All proposal mechanics are scenario assumptions (`docs/rules_inputs.md` section I). 25 scenarios, ledger residual < 2e-9, 64 tests. Findings in `docs/comparison_B_results.md`; main points: P1 hits only owners paying at least EUR 51,000; P3 removes about half of the BV advantage of a one-client owner whatever the threshold and lookback (the grid matters only for multi-client owners); P2 hits lump-sum extraction hardest and can be partly offset by higher pay; for owners on the liquidation-reserve route P2 and P3 *defer* revenue (negative in 2028-39, large at liquidation).
- **15 Nov 2026, consolidation.** Redundant comparison-B runs dropped (185 -> 101 distinct runs; one-client owners run once per family, equivalence proved by a test and by an exact comparison with the full grid: 12,120 shared rows, maximum difference 0) and the runner parallelised (about 95 s instead of 11 min). Stand-alone report `docs/report.md` and seven figures in `docs/figures/` added. Correction: an earlier statement that a hire is never chosen was wrong - a EUR 5,000 hire is chosen in some cells (revenue of EUR 160k and above, one-earner household, and some combined cases); the hire grid was kept for that reason.
- **15 Nov 2026, comparison C (WP3-4 as sweeps).** With no additional data available, the population stage was built as explicit sweeps: 4,000 random owner mixes (revenue, payout strategy, client concentration, size of S0), a smooth and a strict entry/exit response, leavers who become sole traders, employees or stop, a break-even on the share who stop, a tornado, and a national-wealth bound from observed HFCS aggregates; plus a 'no management companies' ceiling. 18 hypotheses registered and tested (`docs/hypotheses.md`): 8 supported, the others not supported, partly supported, conditional on an unknown input, or untestable (H3: prevalence of tax-motivated companies needs owner-level data). Key results: switching legal form raises revenue, only stopping activity cancels it; the budget result is dominated by the owner mix (from negative to over EUR 1bn); the national wealth Gini moves by less than 0.01. Everything at population level is conditional.
- **Next (needs owner go-ahead; WP3-4 are now done as sweeps):** WP3 (choice of arrangement, calibration; needs the open inputs: distribution of director pay and retained profits in S0, share with one client) and WP4 (population scenarios, bounding case, break-even sensitivity against EUR 450m). Both depend on data not yet available; the micro results can be re-run in minutes once `hand_check_list.md` is confirmed.
