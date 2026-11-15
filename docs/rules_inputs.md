# Rule inputs

Status key: **supplied** = given by the project owner (with the citations they gave), not yet checked by me against the primary
source; **found** = seen in a web-search snippet only; **missing** = needed and not provided. Nothing here is verified legal text.

## A. Draft proposals (autumn 2026 budget draft; not law as of 15 November 2026)

| # | proposal | detail | status |
|---|---|---|---|
| P1 | Remove the reduced corporate rate for companies without employees | 20% -> 25% on the first EUR 100,000 of taxable profit | supplied |
| P2 | Tie access to reduced dividend tax to payroll (directors and employees) | multiple **open**; proposed start 1 January 2028 | supplied; parameter missing |
| P3 | Restrict reduced dividend regimes (VVPRbis, liquidation reserve) for long-term single-client companies | one director working almost exclusively for the same client for years; new amounts from 2028 | supplied; definition of "almost exclusively" and "years" missing |
| - | Government's projected revenue | EUR 300m (2027); EUR 450m a year (2028, 2029) | supplied; methodology unknown |

A secondary source reports that Belgian law has **no legal definition of "management company"**, so a no-employee test would
apply to every company without staff. The study therefore defines the segment by structure (zero-employee BV, single director) and
treats "management company" as a label. *(found: Brussels Times / law-firm commentaries; verify)*

## B. Current rules (2026) as supplied

| item | value | status |
|---|---|---|
| Personal income tax marginal rates | 25%, 40%, 45%, 50% | supplied |
| Tax-free allowance | EUR 11,550 | supplied; **conflict**: one guide found says EUR 10,910 in 2026 rising in stages to EUR 15,600 by 2030 |
| Bracket thresholds | - | **missing** |
| Municipal surcharge | varies by commune | missing (use national average, source needed) |
| Self-employed contributions (main occupation) | 20.5% up to EUR 75,024.54; 14.16% up to EUR 110,562.42; minimum EUR 890.42 per quarter | supplied |
| Contributions above the second ceiling | - | missing (assumed none or lower rate: verify) |
| Company annual contribution | EUR 409.30 or EUR 1,022.38 (by 2024 balance-sheet total) | supplied |
| Employee social contributions | - | **missing** (needed for the employee comparator) |
| Employer social contributions | - | **missing** |
| Corporate tax | 25% standard; 20% on first EUR 100,000 for qualifying small companies | supplied |
| Condition for reduced corporate rate | director remuneration at least EUR 51,000 (indexed; was 45,000) for a calendar-year company; test starts in the fifth taxable period; lower pay can qualify if it covers taxable profit; loses reduced rate if flat-rate benefits in kind exceed 20% of total director pay | supplied |
| Dividends, standard | 30% withholding | supplied |
| VVPRbis | 15% -> 18% from 1 July 2026 | supplied |
| Liquidation reserve | 10% levy at creation, then 9.8% withholding after a three-year wait: effective 18%; older reserves follow different rules | supplied |
| Liquidation of company | tax on liquidation distributions | **missing** |
| Capital gains on sale of private company shares | - | **missing**; a KPMG note found says a capital gains tax was prepared but adoption was on hold |
| VAT | 21% standard; small-business exemption up to EUR 25,000 turnover | supplied (same in both structures; excluded from comparison) |
| Statutory pension of self-employed vs employees | - | missing (needed to value retained earnings as a pension substitute) |
| Rules on what counts as an employee for P1 (hours, relatives, ...) | - | **missing** (drives the avoidance margin of hiring one employee) |

## C. Discrepancies and cautions to resolve first

1. **Tax-free allowance:** 11,550 (supplied) vs 10,910 (guide found). One of them is a different year, a different taxpayer type, or wrong.
2. **Dates:** the VVPRbis change (1 July 2026), the pay threshold (indexed) and the draft start dates (2027, 2028) imply a *policy path by calendar year*; the model's single-year policy must be extended.
3. **Pending reforms found in snippets:** a personal income tax reform, a capital gains tax and a dividend withholding increase are described as prepared, enacted or stalled depending on the source. Each changes the incentive to accumulate wealth in a company and must be checked before choosing the baseline.
4. **Draft vs law:** proposals are scenarios with parameters, not baseline rules.
5. **Existing project policy file** (`belgium_abm/configs/policy_illustrative.yaml`) is a placeholder and must not be reused for this study.

## D. What the project owner is asked to supply

- bracket thresholds, municipal surcharge, employee and employer contribution rates, liquidation-distribution rules, treatment of capital gains on share sales;
- a definition of the segment (zero employees? single director? single client?) and the preferred proxy for "almost exclusively one client";
- the draft text, or at least the payroll multiple range being discussed for P2;
- any administrative statistics on zero-employee BVs (counts, director pay, retained profits).
