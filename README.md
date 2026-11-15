# Management-company taxation in Belgium: effect on entrepreneurs, wealth distribution and the budget

Research project built on the agent-based model in the sibling repository
`belgium_abm` (population generator, fiscal engine, lifecycle dynamics, scenario machinery). This repository holds the
research design, the rule inputs, the data requirements and the limitations, and (since 15 November 2026) the tax engine for the three arrangements (`src/mgmt_tax`) and comparison A.

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
| `docs/implementation_design.md` | how the engine is built, how it uses `belgium_abm`, the tests |
| `docs/worked_examples.md` | the hand-computed examples behind the unit tests |
| `docs/comparison_A_results.md` | employee vs sole trader vs one-person BV under current (supplied) rules |
| `docs/hand_check_list.md` | generated list of rule values to confirm against primary sources |
| `configs/` | `policy_be_2026_supplied.yaml` (rules, one entry each with status and source), `assumptions.yaml` |
| `data/sources.yaml` | registry of datasets to acquire (all `not_acquired` at this stage) |

## Status

WP1 (tax engine) and comparison A are done **on rules supplied by the owner and not independently confirmed**; no proposal (P1-P3) has been run, and no entrepreneur-count or budget result exists. Every number quoted from outside sources is flagged *unverified* until checked against the
primary source. Results from the earlier `belgium_abm` runs used an illustrative policy file and must not be quoted for this question.

## Reproduce

```bash
pip install -e /path/to/belgium_abm        # branch claude/statbel-data-integration-maq0e5 (only its crn module is used)
pip install numpy pandas pyyaml pytest
python3 -m pytest -q                        # 44 tests (worked examples, invariants)
python3 scripts/run_comparison_a.py         # writes outputs/comparison_A/
python3 scripts/make_report_a.py            # writes docs/comparison_A_results.md and docs/hand_check_list.md
```
