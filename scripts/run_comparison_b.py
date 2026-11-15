"""Run comparison B: baseline and every proposal scenario (parallel).  Usage: python scripts/run_comparison_b.py [out_dir]"""
import json
import multiprocessing as mp
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mgmt_tax.compare_a import HOUSEHOLDS, git_commit  # noqa: E402
from mgmt_tax.compare_b import PROFITS_B, n_runs, rows_from, run_one, scenario_list, strategies_ext, taxpath_rows  # noqa: E402
from mgmt_tax.policy import PolicyPath, load_policy  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "outputs" / "comparison_B"
N_REP, SEED, FIRST_PERIOD = 300, 20261115, 5          # mature company (pay condition applies from 2026); same seed as comparison A
HH = {h.name: h for h in HOUSEHOLDS if h.name in ("single", "couple_one_earner_2kids", "couple_two_earners_2kids")}
POL = load_policy(ROOT / "configs" / "policy_be_2026_supplied.yaml", ROOT / "configs" / "assumptions.yaml", ROOT / "configs" / "proposals.yaml")
STRATS = strategies_ext()
SCEN = scenario_list()
HEADLINE = ("baseline", "P1_2027", "P2x2_2028", "P2x3_2028", "P3_90pct_3y", "COMB_P1_P2x2_P3_90pct_3y")


def job(args):
    si, hire, conc, hh_name, static_map = args
    sc, hh = SCEN[si], HH[hh_name]
    path = PolicyPath(POL, sc.changes)
    outs, years = run_one(path, hh, FIRST_PERIOD, N_REP, SEED, PROFITS_B, STRATS, hire, conc, sc.hire_from)
    meta = {"scenario": sc.label, "family": sc.family, "hire_cost": hire, "concentration": conc, "household": hh_name, "cohort": "mature", **dict(sc.params)}
    rows, chosen = rows_from(outs, PROFITS_B, meta, static_map, keep_all=False)
    if sc.label == "baseline":
        static_map = dict(zip(PROFITS_B, chosen["BV_BEST"], strict=True))
        rows, chosen = rows_from(outs, PROFITS_B, meta, static_map, keep_all=False)
    full, paths = [], []
    if hh_name == "single" and sc.label in HEADLINE and hire in (0.0, 5000.0, 10000.0) and conc in (1.0, 0.9, 0.7):
        r_all, _ = rows_from(outs, PROFITS_B, meta, static_map, keep_all=True)
        full = [r for r in r_all if r["arrangement"].startswith("BV:") or r["arrangement"] in ("EMPLOYEE", "SOLE_TRADER")]
        names = {"BV_BEST": chosen["BV_BEST"], "BV_STATIC": chosen["BV_STATIC"], "SOLE_TRADER": ["SOLE_TRADER"] * len(PROFITS_B), "EMPLOYEE": ["EMPLOYEE"] * len(PROFITS_B)}
        for a in ("thr_dist_vvpr", "thr_lr_liq", "min_dist_vvpr", "min_lr_liq"):   # archetype owners (fixed strategies), for the timing tables
            names[f"ARCH:{a}"] = [f"BV:{a}"] * len(PROFITS_B)
        paths = taxpath_rows(outs, PROFITS_B, names, meta, years)
    return {"rows": rows, "chosen": chosen["BV_BEST"], "full": full, "paths": paths, "used": path.used_table().assign(scenario=sc.label),
            "ledger": max(r["ledger_residual_max"] for r in rows), "hh": hh_name, "scenario": sc.label}


def tasks(first: bool, static):
    out = []
    for si, sc in enumerate(SCEN):
        if (sc.label == "baseline") != first:
            continue
        for hire in sc.hire_costs:
            for conc in sc.concentrations:
                for hh_name in HH:
                    out.append((si, hire, conc, hh_name, None if first else {p: static[(hh_name, p)] for p in PROFITS_B}))
    return out


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    workers = min(4, mp.cpu_count())
    results, static = [], {}
    with ProcessPoolExecutor(workers, mp_context=mp.get_context("fork")) as ex:
        for r in ex.map(job, tasks(True, None)):
            results.append(r)
            for p, nm in zip(PROFITS_B, r["chosen"], strict=True):
                static[(r["hh"], p)] = nm
        print(f"baseline done {time.time() - t0:.0f}s", flush=True)
        rest = tasks(False, static)
        for i, r in enumerate(ex.map(job, rest, chunksize=2)):
            results.append(r)
            if i % 50 == 0:
                print(f"{i}/{len(rest)} jobs, {time.time() - t0:.0f}s", flush=True)
    compact = [x for r in results for x in r["rows"]]
    pd.DataFrame(compact).to_csv(OUT / "comparison_B_runs.csv", index=False, float_format="%.4f", lineterminator="\n")
    pd.DataFrame([x for r in results for x in r["full"]]).drop_duplicates().to_csv(OUT / "comparison_B_headline_all_strategies.csv", index=False, float_format="%.4f", lineterminator="\n")
    pd.DataFrame([x for r in results for x in r["paths"]]).to_csv(OUT / "taxpath_B_headline.csv", index=False, float_format="%.2f", lineterminator="\n")
    ru = pd.concat([r["used"] for r in results]).drop_duplicates(["rule_id", "value", "status"])
    ru.to_csv(OUT / "rules_used_B.csv", index=False, lineterminator="\n")
    ledger = max(r["ledger"] for r in results)
    (OUT / "manifest_B.json").write_text(json.dumps({"n_rep": N_REP, "seed": SEED, "cohort": "mature (5th taxable period in 2026)", "profits": list(PROFITS_B), "households": list(HH),
                                                     "n_strategies": len(STRATS), "git_commit": git_commit(), "max_ledger_residual": ledger, "n_scenarios": len(SCEN), "n_runs": n_runs(),
                                                     "n_simulations": n_runs() * len(HH), "rule_status_counts": ru.drop_duplicates("rule_id").status.value_counts().to_dict(),
                                                     "banner": "RULES SUPPLIED, NOT CONFIRMED; PROPOSAL PARAMETERS ARE SCENARIO ASSUMPTIONS, NOT THE DRAFT"}, indent=2), encoding="utf-8")
    print("finished", f"{time.time() - t0:.0f}s", "max ledger residual", ledger, flush=True)
