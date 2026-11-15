# What this study cannot show

Stated up front so that no result is read as more than it is.

## Cannot be answered with public data

1. **The true response of entrepreneur numbers to the tax change.** No Belgian estimate of the incorporation elasticity was found. The number of entrepreneurs is reported as a function of an assumed sensitivity, with the break-even level, not as a forecast.
2. **The size of the avoidance responses** (hiring a minimal employee, restructuring, changing the pay mix). They can be represented but their take-up is a swept parameter.
3. **Who bears the tax** (owner, client, employees). Incidence is a parameter from 0 to 100%.
4. **The government's own revenue figures.** Their method is unknown; agreement or disagreement with EUR 300m / 450m is a plausibility check, not a validation.
5. **The distribution of company equity at the very top.** Closely held large companies and holdings are not in the model; national top-wealth results are bounds.

## Outside the model by design

6. **General-equilibrium effects:** wages, prices, interest rates, exchange of labour between sectors, aggregate demand.
7. **Relocation of owners or companies abroad**, and changes of tax residence.
8. **Investment and capital-market effects** of lower retained profits; the effect on lending, start-ups or growth.
9. **Evasion and other avoidance routes** beyond those explicitly modelled (family structures, other legal forms, cash).
10. **Effects on large companies, non-profit bodies and employers**, except through the incidence and substitution parameters.
11. **Administrative and compliance costs**, legal challenges, transitional rules not in the draft.
12. **Welfare and non-tax motives** for entrepreneurship, other than the calibrated taste term; the model cannot say whether fewer entrepreneurs is good or bad.
13. **The business cycle and macro shocks**; constant prices and no inflation of thresholds beyond the indexation rules supplied.
14. **Interactions with other budget measures** (personal income tax reform, capital gains tax, other dividend changes) unless they are verified and added to the baseline.

## Simplifications that affect interpretation

15. **Owner behaviour is a heuristic** (tax-minimising rule with a liquidity constraint), not a solved dynamic programme; real owners may be more or less sophisticated. The share who optimise is swept.
16. **Individual taxation with household allowances:** no full treatment of partner income splitting or the details of family taxation.
17. **Municipal surcharge** is a national average.
18. **One-person BVs are treated as a homogeneous segment** apart from profit level and occupation proxies; professions differ widely (consultants, liberal professions, tradespeople).
19. **Lifetime comparison uses simulated paths** with assumed earnings persistence and business risk; those parameters are not identified from public data (sensitivity reported).
20. **Pensions** are valued with a stylised rule unless verified statutory formulas are added.
21. **Sample noise:** even with oversampling, results for the top tail rest on few households; intervals across replicates are reported, and small groups are flagged.
23. **Source quality for the draft:** P2 (2x/3x) and P3 (client threshold, lookback) rest on second-hand excerpts; results are labelled as scenarios and replaced once the draft text is available.
22. **Policy status:** the proposals are drafts, parameters are open, and baseline rules may change before any result is published; every table states the policy version and date.

## Added with comparison A (15 November 2026)

24. **Perfect-foresight owners.** `BV_BEST` is the best of 19 fixed strategies by mean terminal wealth, evaluated with full knowledge of the rules. It is an upper bound on what a tax-minimising owner gets, not a description of owners.
25. **Comparators are not optimised.** Sole traders and employees get no tax-advantaged private pension saving, third-pillar saving or other deductions, and the employee gets no professional-expense lump sum or work bonus (inputs not supplied). This overstates the BV advantage.
26. **Household type acts only through liquidity.** Taxation is individual and family tax rules were not supplied; household results differ because the owner must finance more or less spending.
27. **A real return of 0%** in the baseline means timing of extraction is worth nothing; the sensitivity cases with 2-3% show the effect.
28. **Pension entitlements are not valued.** A large share of the BV's advantage is lower social contributions, which buy lower pension-relevant income.
29. **No indexation** of thresholds over 2026-2040; constant 2026 euros.
30. **Stylised shocks** (sizes taken from `belgium_abm`, assumed) and stylised household spending needs; none is data.

## Added with comparison B (15 November 2026)

31. **The proposals are modelled from second-hand descriptions.** The mechanics of P1 (employee test, hire cost), P2 (payroll definition, treatment of excess, old reserves) and P3 (client definition, window, grandfathering) are my choices; the results show what these specific scenarios do, not what the draft does.
32. **Client concentration is not data.** P3 results are reported by assumed owner concentration with an assumed fluctuation process; the distribution of concentration in S0 is unknown. A one-client owner is always caught; everything else depends on that unknown distribution.
33. **Owner responses are limited to strategy, pay level and a hire.** No diversification of clients, restructuring, relocation, change of arrangement, entry or exit; the strategy set is fixed.
34. **Per-owner tax effects are not a budget.** They are for archetype owners; the budget needs the mixture of owner types (open), and the 2040 liquidation in each simulated path is a horizon artefact that dominates late-year effects of P2 and P3.
35. **Timing.** Static revenue effects of P2 and P3 can be negative in the early years for owners on the liquidation-reserve route and positive later; comparing with the government's EUR 300m / 450m profile requires the owner mix and a population model.
36. **A hire is treated as a cost that leaves the system**; the taxes and contributions on the hire's wage are not counted, which understates revenue under P1 for owners who hire.

## What the study can credibly claim

- the size and structure of the current tax advantage by profit level and household type under the verified rules;
- how each proposal changes that advantage, mechanically;
- the budget effect under fixed behaviour, with timing, compared with the government's figures;
- how large a behavioural response would have to be to cancel the budget gain (break-even);
- how far the national distribution could move at most (bounding scenario), and how the owner-manager group is affected.
