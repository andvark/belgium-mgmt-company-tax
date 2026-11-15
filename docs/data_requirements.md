# Data requirements for the added effects

For each effect: what we need, what exists publicly, what was found so far (web search plus the Eurostat tables already used in
`belgium_abm`), and the fallback when no data identifies it. "Identified" means public data can pin the parameter for Belgium;
otherwise the parameter is a **swept sensitivity**, not an estimate.

## A. Core inputs (needed whatever else is added)

| need | public source (candidate) | found / status | identified? |
|---|---|---|---|
| Verified tax and contribution rules, thresholds, dates | FPS Finance, INASTI/RSVZ, RSZ/ONSS, Moniteur belge | partly supplied by the owner; see `rules_inputs.md` | yes once verified |
| Stock of zero-employee BVs, by single director and client | Statbel VAT-enterprise tables by legal form and employer class (2025 download), FPS Economy SME statistics, KBO/BCE | **partly found.** Statbel BeStat (checked): **997,481 VAT-registered enterprises with no employees (2024)**, 477,126 BV/SRL of all sizes; FPS Economy (supplied, page unreachable): 476,914 BV/SRL SMEs of which 73.7% with no employees, about 351,000. Single-director and one-client shares: **not found**. Other scale hints: Eurostat `bd_size` 2024 counts **729,925 enterprises with zero employees** (all legal forms, business economy), **67,369 births, 50,325 deaths**; LFS 2025 **514,000 self-employed without employees**. A law-firm commentary claims **more than 80,000** single-person management companies (about 25,000 seven years ago): **unverified secondary claim** | no: needs an administrative count |
| Distribution of taxable profit and director remuneration in zero-employee companies | NBB Central Balance Sheet Office (public annual accounts give reserves, profit carried forward and dividend allocations); FPS Finance form 281.20 records taxable director remuneration | no public distribution for zero-employee BVs found; accounts headings report profit allocated to directors, which is not annual remuneration | maybe (sample of filings) |
| Bunching of remuneration at the threshold | same | not found; would be the best validation of the owner strategy | maybe |
| Retained earnings and dividend payout of small companies | NBB annual accounts | not found | maybe |
| Government's revenue assumptions behind EUR 300m / 450m | draft budget notes, Federal Planning Bureau, Court of Audit | not found; Planning Bureau's list of 264 budget options (June 2026) exists but whether it scores this measure is unchecked | partly |

## B. Added economy-wide effects

| # | effect | what it needs | public data found | gap | fallback in the study |
|---|---|---|---|---|---|
| E1 | **Switching between arrangements (entry/exit elasticity)** | response of incorporation to the after-tax advantage, ideally Belgian | International estimates found (snippets, **papers not yet read**): a UK study reporting that a 10% increase in tax savings raises the hazard of incorporating by 2.3%; a European study estimating a semi-elasticity of about 1.0 per percentage-point widening of the personal-corporate gap; a Dutch study finding about 0.5% lower income for a 5 pp rate rise with heterogeneity of 2-10 times; Finnish work showing income shifting dominates the response. A Ghent University / NBB study on director pay is mentioned in a bank article but not located | no Belgian estimate found | sweep a range anchored on these studies; report the break-even sensitivity |
| E2 | **Income shifting and timing (pay vs retain vs distribute)** | payout and remuneration response to the tax gap | Finnish evidence above; Belgian company accounts would identify bunching | accounts not yet acquired | owner strategy is rule-based; sweep the share of owners who optimise |
| E3 | **Hiring one employee to keep the reduced rate (P1 avoidance)** | cost of a minimal employee vs EUR 5,000 maximum saving; legal definition of employee for the test | none | rule details missing | explicit margin with the cost of the cheapest qualifying employee; sweep take-up |
| E4 | **Tax incidence: pass-through to clients** | change in contractor fees after tax changes | UK IR35 evaluations (HMRC) found; contractor-body surveys are advocacy-biased; no Belgian data | no Belgian estimate | incidence parameter from 0 to 100% |
| E5 | **Client substitution: contractors vs employees** | elasticity of clients' demand for contractor services; Belgian rules on employment presumptions | HMRC reports: around 120,000 workers affected by the 2021 reform, roughly 40% of 280,000 moves from own payroll attributed to it, 41% of surveyed clients using fewer off-payroll contractors (snippets; **not verified against the full report**); no Belgian data | no Belgian estimate | substitution elasticity swept; employer-cost difference computed from the verified rules |
| E6 | **Macro consistency (wages, employment, GDP)** | official macro scoring of the measure | Federal Planning Bureau publishes macro projections and a list of 264 budget options; no scoring of this measure found | not found | static plus micro-behavioural only; compare with any official scoring; do not add a macro model |
| E7 | **Relocation abroad / change of tax residence** | stock and flows of emigrating owners | none found | no data | excluded; discussed as a limitation; optional sweep of a fixed share who leave |
| E8 | **Capital-market and investment effects of fewer retained profits** | what retained earnings are invested in; household vs corporate saving | HFCS wave 2023 (household wealth, business ownership 12.2% of households); NBB financial accounts (not acquired) | no link between company reserves and investment | excluded; discussed; report retained-equity change as an indicator |
| E9 | **Pension substitution** | self-employed statutory pensions, to value retained earnings as retirement saving | FPS Pensions / INASTI aggregates (candidate, not acquired) | not acquired | report pension entitlement separately; include the self-employed pension rule once verified |
| E10 | **Public-finance dynamics** | interest rates, debt path, other measures | Planning Bureau outlook (deficit 4.9% in 2026 rising to 6.3% in 2031 per a news report); interactions with other budget measures | other measures change over time | report the revenue effect only, not the deficit path |
| E11 | **Wealth tail** | distribution of closely held company equity | none (HFCS publishes only the share of households with business wealth) | no data | report the owner-manager group; treat national tail results as bounds |

## C. Acquisition plan (public first, order of value)

1. Primary-source verification of the rules (FPS Finance, INASTI, Moniteur belge): owner can speed this up.
2. A count and profile of zero-employee BVs (KBO/BCE public data, Statbel, FPS Finance statistics); if only counts exist, use them for calibration, not for profit distributions.
3. NBB annual-account aggregates for small companies (remuneration, retained earnings, dividends).
4. Read the key elasticity papers and the HMRC update in full, and record the chosen prior ranges with page references.
5. Planning Bureau and Court of Audit documentation of the draft's revenue scoring.

Restricted data (tax-return microdata, matched employer-employee data) would identify E1, E2 and E5 directly. They are assumed
unavailable here; the plan is built so the study stays honest without them.
