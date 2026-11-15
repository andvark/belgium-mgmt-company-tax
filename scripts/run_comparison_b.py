"""Run comparison B: baseline and every proposal scenario.  Usage: python scripts/run_comparison_b.py [out_dir]"""
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mgmt_tax.compare_a import HOUSEHOLDS, git_commit  # noqa: E402
from mgmt_tax.compare_b import PROFITS_B, rows_from, run_one, scenario_list, strategies_ext, taxpath_rows  # noqa: E402
from mgmt_tax.policy import PolicyPath, load_policy  # noqa: E402

out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "outputs" / "comparison_B"
out.mkdir(parents=True, exist_ok=True)
N_REP, SEED, FIRST_PERIOD = 300, 20261115, 5          # mature company (pay condition applies from 2026); same seed as comparison A
HH = [h for h in HOUSEHOLDS if h.name in ("single", "couple_one_earner_2kids", "couple_two_earners_2kids")]
pol = load_policy(ROOT / "configs" / "policy_be_2026_supplied.yaml", ROOT / "configs" / "assumptions.yaml", ROOT / "configs" / "proposals.yaml")
strats = strategies_ext()


def headline(sc_label: str, hire: float, conc: float) -> bool:
    return (sc_label in ("baseline", "P1_2027", "P2x2_2028", "P2x3_2028", "P3_90pct_3y", "COMB_P1_P2x2_P3_90pct_3y")) and hire in (0.0, 10000.0) and conc in (1.0, 0.9)


compact, full, paths, used = [], [], [], []
static: dict[tuple[str, float], str] = {}
t0 = time.time()
ledger = 0.0
for sc in scenario_list():
    path = PolicyPath(pol, sc.changes)
    for hire in sc.hire_costs:
        for conc in sc.concentrations:
            for hh in HH:
                outs, years = run_one(path, hh, FIRST_PERIOD, N_REP, SEED, PROFITS_B, strats, hire, conc, sc.hire_from)
                meta = {"scenario": sc.label, "family": sc.family, "hire_cost": hire, "concentration": conc, "household": hh.name, "cohort": "mature", **dict(sc.params)}
                rows, chosen = rows_from(outs, PROFITS_B, meta, None if sc.label == "baseline" else {p: static[(hh.name, p)] for p in PROFITS_B}, keep_all=False)
                if sc.label == "baseline":
                    for p, nm in zip(PROFITS_B, chosen["BV_BEST"], strict=True):
                        static[(hh.name, p)] = nm
                    rows, chosen = rows_from(outs, PROFITS_B, meta, {p: static[(hh.name, p)] for p in PROFITS_B}, keep_all=False)
                compact += rows
                ledger = max(ledger, max(r["ledger_residual_max"] for r in rows))
                if hh.name == "single" and headline(sc.label, hire, conc):
                    r_all, _ = rows_from(outs, PROFITS_B, meta, {p: static[(hh.name, p)] for p in PROFITS_B}, keep_all=True)
                    full += [r for r in r_all if r["arrangement"].startswith("BV:") or r["arrangement"] in ("EMPLOYEE", "SOLE_TRADER")]
                    names = {"BV_BEST": chosen["BV_BEST"], "BV_STATIC": chosen["BV_STATIC"], "SOLE_TRADER": ["SOLE_TRADER"] * len(PROFITS_B), "EMPLOYEE": ["EMPLOYEE"] * len(PROFITS_B)}
                    for a in ("thr_dist_vvpr", "thr_lr_liq", "min_dist_vvpr", "min_lr_liq"):   # archetype owners (fixed strategies), for the timing tables
                        names[f"ARCH:{a}"] = [f"BV:{a}"] * len(PROFITS_B)
                    paths += taxpath_rows(outs, PROFITS_B, names, meta, years)
    used.append(path.used_table().assign(scenario=sc.label))
    print(f"{sc.label}: done at {time.time() - t0:.0f}s", flush=True)

pd.DataFrame(compact).to_csv(out / "comparison_B_runs.csv", index=False, float_format="%.4f", lineterminator="\n")
pd.DataFrame(full).drop_duplicates().to_csv(out / "comparison_B_headline_all_strategies.csv", index=False, float_format="%.4f", lineterminator="\n")
pd.DataFrame(paths).to_csv(out / "taxpath_B_headline.csv", index=False, float_format="%.2f", lineterminator="\n")
ru = pd.concat(used).drop_duplicates(["rule_id", "value", "status"])
ru.to_csv(out / "rules_used_B.csv", index=False, lineterminator="\n")
(out / "manifest_B.json").write_text(json.dumps({"n_rep": N_REP, "seed": SEED, "cohort": "mature (5th taxable period in 2026)", "profits": list(PROFITS_B), "households": [h.name for h in HH],
                                                 "n_strategies": len(strats), "git_commit": git_commit(), "max_ledger_residual": ledger, "n_scenarios": len(scenario_list()),
                                                 "rule_status_counts": ru.drop_duplicates("rule_id").status.value_counts().to_dict(),
                                                 "banner": "RULES SUPPLIED, NOT CONFIRMED; PROPOSAL PARAMETERS ARE SCENARIO ASSUMPTIONS, NOT THE DRAFT"}, indent=2), encoding="utf-8")
print("finished", f"{time.time() - t0:.0f}s", "max ledger residual", ledger)
