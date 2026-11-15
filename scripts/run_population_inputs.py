"""Per-owner yearly tax paths and terminal wealth for every proposal scenario: the input of the population layer.  Usage: python scripts/run_population_inputs.py [out_dir]"""
import multiprocessing as mp
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from mgmt_tax.compare_a import HOUSEHOLDS  # noqa: E402
from mgmt_tax.compare_b import PROFITS_B, run_one, scenario_list, strategies_ext  # noqa: E402
from mgmt_tax.policy import PolicyPath, load_policy  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "outputs" / "population"
N_REP, SEED, FIRST_PERIOD = 300, 20261115, 5
HH = {h.name: h for h in HOUSEHOLDS if h.name in ("single", "couple_one_earner_2kids")}
POL = load_policy(ROOT / "configs" / "policy_be_2026_supplied.yaml", ROOT / "configs" / "assumptions.yaml", ROOT / "configs" / "proposals.yaml")
STRATS = strategies_ext()
SCEN = scenario_list()
ARCH = ["thr_dist_ord", "thr_dist_vvpr", "thr_ret_vvpr_k5", "thr_lr_liq", "min_dist_vvpr", "min_lr_liq", "min_dist_ord"]
ARCH += ["fx60_lr_liq", "fx80_lr_liq", "fx100_lr_liq"]   # not owner categories: needed to follow the baseline-best strategy of owners who plan optimally


def job(args):
    si, conc, hh_name = args
    sc = SCEN[si]
    path = PolicyPath(POL, sc.changes)
    outs, years = run_one(path, HH[hh_name], FIRST_PERIOD, N_REP, SEED, PROFITS_B, STRATS, 0.0, conc, sc.hire_from)
    bv = [k for k in outs if k.startswith("BV:") and "antiabuse" not in k]
    best = np.array([outs[k].wealth_end.mean(axis=1) for k in bv]).argmax(axis=0)
    labels = {f"ARCH:{a}": [f"BV:{a}"] * len(PROFITS_B) for a in ARCH}
    labels["BV_BEST"] = [bv[i] for i in best]
    labels["SOLE_TRADER"] = ["SOLE_TRADER"] * len(PROFITS_B)
    labels["EMPLOYEE"] = ["EMPLOYEE"] * len(PROFITS_B)
    tax, wealth = [], []
    for lab, names in labels.items():
        for pi, prof in enumerate(PROFITS_B):
            o = outs[names[pi]]
            wealth.append((sc.label, conc, hh_name, lab, prof, names[pi], float(o.wealth_end[pi].mean())))
            for t, y in enumerate(years):
                tax.append((sc.label, conc, hh_name, lab, prof, y, float(o.tax_year_total[t][pi].mean()), float(o.tax_year_ssc[t][pi].mean())))
    return tax, wealth


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    ALL = (1.0, 0.95, 0.90, 0.80, 0.70, 0.50)   # combined scenarios need every concentration (the population layer mixes them); P3-only one-client results are shared via REF_ONE_CLIENT
    jobs = [(si, c, h) for si, sc in enumerate(SCEN) for c in (ALL if sc.family == "combined" else sc.concentrations) for h in HH]
    t0 = time.time()
    with ProcessPoolExecutor(min(4, mp.cpu_count()), mp_context=mp.get_context("fork")) as ex:
        res = list(ex.map(job, jobs, chunksize=2))
    tax = pd.DataFrame([r for t, _ in res for r in t], columns=["scenario", "concentration", "household", "arrangement", "profit_level", "year", "tax_total", "tax_ssc"])
    wealth = pd.DataFrame([r for _, w in res for r in w], columns=["scenario", "concentration", "household", "arrangement", "profit_level", "strategy", "wealth_end"])
    tax.to_csv(OUT / "taxpath_all.csv.gz", index=False, float_format="%.2f", compression="gzip")
    wealth.to_csv(OUT / "wealth_all.csv", index=False, float_format="%.2f")
    print(f"{len(jobs)} jobs, {len(tax)} tax rows, {time.time() - t0:.0f}s")
