"""Comparison A: employee vs sole trader vs one-person BV (many owner strategies) under a given policy path.

Profit level = expected annual revenue billed to the client (for the employee: total employer cost).  All arrangements face the
same revenue path (paired shocks), the same household, and start with the same wealth.  Output = long table by household x cohort x
profit level x arrangement/strategy, with paired differences against the sole trader and the employee.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from mgmt_tax.arrangements import TAX_KEYS, Household, Outcome, simulate_employee, simulate_sole_trader
from mgmt_tax.policy import PolicyPath
from mgmt_tax.shocks import paired_shocks
from mgmt_tax.strategies import BVStrategy, simulate_bv

HOUSEHOLDS = (
    Household("single", 1, 0, False),
    Household("couple_one_earner", 2, 0, False),
    Household("couple_one_earner_2kids", 2, 2, False),
    Household("couple_two_earners_2kids", 2, 2, True),
)
PROFITS = (40e3, 60e3, 80e3, 100e3, 130e3, 160e3, 200e3, 250e3)
COHORTS = {"mature": 5, "new": 1}  # first taxable period of the company in 2026 (pay condition applies from period 5)


def strategies() -> list[BVStrategy]:
    out = [BVStrategy("shell_full_pay", "full", "distribute", "ordinary", None, "liquidation")]
    for pay, tag in (("threshold", "thr"), ("liquidity", "min")):
        out += [
            BVStrategy(f"{tag}_dist_ord", pay, "distribute", "ordinary", None, "liquidation"),
            BVStrategy(f"{tag}_dist_vvpr", pay, "distribute", "vvprbis", None, "liquidation"),
            BVStrategy(f"{tag}_ret_vvpr_end", pay, "free_reserve", "vvprbis", None, "dividend"),
            BVStrategy(f"{tag}_ret_vvpr_k3", pay, "free_reserve", "vvprbis", 3, "dividend"),
            BVStrategy(f"{tag}_ret_vvpr_k5", pay, "free_reserve", "vvprbis", 5, "dividend"),
            BVStrategy(f"{tag}_ret_ord_liq", pay, "free_reserve", "ordinary", None, "liquidation"),
            BVStrategy(f"{tag}_lr_liq", pay, "liquidation_reserve", "vvprbis", None, "liquidation"),
            BVStrategy(f"{tag}_lr_div_k5", pay, "liquidation_reserve", "vvprbis", 5, "liquidation"),
            BVStrategy(f"{tag}_lr_liq_antiabuse", pay, "liquidation_reserve", "vvprbis", None, "liquidation", anti_abuse=True),
        ]
    return out


def run_cell(path: PolicyPath, hh: Household, first_period: int, n_rep: int, seed: int, profits=PROFITS, strats: list[BVStrategy] | None = None) -> tuple[dict[str, Outcome], np.ndarray]:
    pol0 = path.baseline
    years = list(range(int(pol0.v("asm.start_year")), int(pol0.v("asm.end_year")) + 1))
    m_emp, m_bus = paired_shocks(seed, n_rep, years, pol0)
    yb = np.asarray(profits, dtype=float)[None, :, None]
    y_emp, y_bus = yb * m_emp[:, None, :], yb * m_bus[:, None, :]
    shape = (len(profits), n_rep)
    outs = {"EMPLOYEE": simulate_employee(y_emp, years, path, hh, shape), "SOLE_TRADER": simulate_sole_trader(y_bus, years, path, hh, shape)}
    for s in (strats if strats is not None else strategies()):
        outs[f"BV:{s.name}"] = simulate_bv(y_bus, years, path, hh, s, shape, first_period=first_period)
    return outs, np.asarray(years)


def _q(x: np.ndarray, q: float) -> np.ndarray:
    return np.quantile(x, q, axis=1)


def summarise(outs: dict[str, Outcome], years: np.ndarray, profits, meta: dict) -> pd.DataFrame:
    n_years = len(years)
    sole, emp = outs["SOLE_TRADER"], outs["EMPLOYEE"]
    rows = []
    for key, o in outs.items():
        for pi, prof in enumerate(profits):
            tot = o.total_tax()[pi]
            r = {**meta, "profit_level": prof, "arrangement": key, "wealth_end_mean": o.wealth_end[pi].mean(), "wealth_end_p10": np.quantile(o.wealth_end[pi], .1),
                 "wealth_end_p90": np.quantile(o.wealth_end[pi], .9), "total_tax_and_contrib_mean": tot.mean(),
                 "tax_excl_ssc_mean": o.total_tax_excl_ssc()[pi].mean(), "ssc_mean": o.total_ssc()[pi].mean(), "admin_cost_mean": o.admin[pi].mean(),
                 "pension_base_per_year_mean": o.pension_base[pi].mean() / n_years, "owner_pay_per_year_mean": o.owner_pay[pi].mean() / n_years,
                 "liquidity_gap_per_year_mean": o.liquidity_gap[pi].mean() / n_years, "reduced_rate_years_mean": o.reduced_rate_years[pi].mean(),
                 "company_equity_before_exit_mean": o.equity_pre_exit[pi].mean(), "ledger_residual_max": o.ledger_residual}
            for k in TAX_KEYS:
                r[f"tax_{k}"] = o.taxes[k][pi].mean()
            for ref_name, ref in (("sole", sole), ("emp", emp)):
                d = o.wealth_end[pi] - ref.wealth_end[pi]
                r[f"adv_vs_{ref_name}_wealth_mean"] = d.mean()
                r[f"adv_vs_{ref_name}_wealth_p10"] = np.quantile(d, .1)
                r[f"adv_vs_{ref_name}_wealth_p90"] = np.quantile(d, .9)
                r[f"adv_vs_{ref_name}_share_positive"] = float((d > 0).mean())
                r[f"adv_vs_{ref_name}_pct_of_revenue"] = d.mean() / (prof * n_years)
                r[f"tax_saved_vs_{ref_name}_total"] = (ref.total_tax()[pi] - tot).mean()
                r[f"tax_saved_vs_{ref_name}_excl_ssc"] = (ref.total_tax_excl_ssc()[pi] - o.total_tax_excl_ssc()[pi]).mean()
                r[f"ssc_saved_vs_{ref_name}"] = (ref.total_ssc()[pi] - o.total_ssc()[pi]).mean()
            rows.append(r)
    df = pd.DataFrame(rows)
    # envelope: the best BV strategy by mean terminal wealth in each cell (the anti-abuse variants are sensitivity rows, not candidates)
    bv = df[df.arrangement.str.startswith("BV:") & ~df.arrangement.str.contains("antiabuse")]
    best = bv.loc[bv.groupby("profit_level")["wealth_end_mean"].idxmax()].copy()
    best["best_strategy"] = best["arrangement"]
    best["arrangement"] = "BV_BEST"
    df["best_strategy"] = ""
    return pd.concat([df, best], ignore_index=True)


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True, cwd=Path(__file__).parent).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def run_grid(path: PolicyPath, out_dir: Path, label: str, n_rep: int = 300, seed: int = 20261115, households=HOUSEHOLDS, cohorts=COHORTS, profits=PROFITS,
             strats: list[BVStrategy] | None = None) -> pd.DataFrame:
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for hh in households:
        for cname, fp in cohorts.items():
            outs, years = run_cell(path, hh, fp, n_rep, seed, profits, strats)
            meta = {"scenario": label, "household": hh.name, "cohort": cname}
            frames.append(summarise(outs, years, profits, meta))
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(out_dir / f"comparison_A_{label}.csv", index=False, float_format="%.4f", lineterminator="\n")
    path.used_table().to_csv(out_dir / f"rules_used_{label}.csv", index=False, lineterminator="\n")
    manifest = {"label": label, "n_rep": n_rep, "seed": seed, "profits": list(profits), "households": [asdict(h) for h in households], "cohorts": cohorts,
                "banner": path.banner, "git_commit": git_commit(), "max_ledger_residual": float(df.ledger_residual_max.max()),
                "n_rules_used": int(len(path.used_table())), "rule_status_counts": path.used_table().status.value_counts().to_dict()}
    (out_dir / f"manifest_{label}.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return df
