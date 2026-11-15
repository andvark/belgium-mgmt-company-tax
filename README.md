# Management-company taxation in Belgium: effect on entrepreneurs, wealth distribution and the budget

Research project (planning stage, **no code yet**) built on the agent-based model in the sibling repository
`belgium_abm` (population generator, fiscal engine, lifecycle dynamics, scenario machinery). This repository holds the
research design, the rule inputs, the data requirements and the limitations. Code will be added only after the plan is agreed.

## The question

The federal government's autumn-2026 budget draft (not law as of 15 November 2026; coalition still negotiating) proposes to
narrow the tax advantages of one-person companies ("management companies"):

1. reduced corporate tax rate (20% on the first EUR 100,000) withdrawn for companies without employees;
2. reduced dividend regimes tied to payroll (multiple left open; proposed start 1 January 2028);
3. reduced dividend regimes (VVPRbis, liquidation reserve) withdrawn for long-term single-client, single-director companies, for new amounts from 2028.

The government's draft projects EUR 300 million extra revenue in 2027 and EUR 450 million a year in 2028 and 2029.

**Will the proposals reduce the number of entrepreneurs, change the wealth distribution, and by how much do they improve the budget?**
The working hypothesis (from the project owner) is that many companies exist because of tax optimisation: pay yourself a minimum,
retain profits, and take a large lump sum out after 3-5 years at a low rate (VVPRbis / liquidation reserve).

## Contents

| file | purpose |
|---|---|
| `docs/research_plan.md` | questions, hypotheses, the comparisons, work packages, deliverables, validation, decisions needed |
| `docs/rules_inputs.md` | the tax rules supplied by the project owner, what is verified, discrepancies found, parameters still missing |
| `docs/data_requirements.md` | for every behavioural / economy-wide effect we might add: data needed, what exists publicly, what was found, fallback |
| `docs/evidence_found.md` | literature and statistics found so far, with links and reliability notes |
| `docs/limitations.md` | what the study cannot show |
| `data/sources.yaml` | registry of datasets to acquire (all `not_acquired` at this stage) |

## Status

Plan drafted, nothing estimated. Every number quoted from outside sources is flagged *unverified* until checked against the
primary source. Results from the earlier `belgium_abm` runs used an illustrative policy file and must not be quoted for this question.
