"""Comparison B: the same three arrangements under each draft proposal (scenario assumptions) and combinations.

Everything is paired with the baseline: same revenue paths, same client-share paths, same household.  Two views of an owner's response:
  static      the baseline-best strategy is kept (fixed behaviour, no hire);
  re-optimised the best strategy under the new rules, including the choice to hire (P1/P2) - the owner adapts, entry/exit does not.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from mgmt_tax.arrangements import Household, Outcome, simulate_employee, simulate_sole_trader
from mgmt_tax.compare_a import strategies
from mgmt_tax.policy import PathChange, PolicyPath
from mgmt_tax.shocks import client_share_paths, paired_shocks
from mgmt_tax.strategies import BVStrategy, simulate_bv

PROFITS_B = (30e3, 40e3, 50e3, 60e3, 80e3, 100e3, 130e3, 160e3, 200e3, 250e3)
N_YEARS = 15


def strategies_ext() -> list[BVStrategy]:
    """Baseline strategy set plus higher fixed pay levels (the owner's response to a payroll-linked cap, P2)."""
    out = strategies()
    for pay in (60e3, 80e3, 100e3):
        tag = f"fx{int(pay / 1000)}"
        out += [BVStrategy(f"{tag}_dist_vvpr", "fixed", "distribute", "vvprbis", None, "liquidation", pay_amount=pay),
                BVStrategy(f"{tag}_ret_vvpr_k5", "fixed", "free_reserve", "vvprbis", 5, "dividend", pay_amount=pay),
                BVStrategy(f"{tag}_lr_liq", "fixed", "liquidation_reserve", "vvprbis", None, "liquidation", pay_amount=pay)]
    return out


@dataclass(frozen=True)
class Scenario:
    label: str
    family: str                       # baseline | P1 | P2 | P3 | combined
    changes: tuple[PathChange, ...]
    hire_costs: tuple[float, ...] = (0.0,)
    concentrations: tuple[float, ...] = (1.0,)
    params: tuple[tuple[str, object], ...] = ()

    @property
    def hire_from(self) -> int:
        """A hire is made when P1 starts (never before)."""
        starts = [c.start_year for c in self.changes if any(k.startswith("p1.") for k in c.overrides)]
        return min(starts) if starts else 0


# hire_cost 0 = no employee; 1 = a hire at (almost) zero cost, used to locate the break-even hire cost; the others are annual employer costs in EUR (scenario sweep)
HIRES = (0.0, 1.0, 5000.0, 10000.0, 15000.0, 20000.0)
HIRES_COMB = (0.0, 5000.0, 10000.0, 20000.0)
CONCS = (1.0, 0.95, 0.90, 0.80, 0.70, 0.50)  # mean share of the largest client; 1.0 = exactly one client (segment S1)
CONCS_COMB = (1.0, 0.90, 0.70)


def p1(start=2027):
    return PathChange(start, {"p1.reduced_rate_requires_employee": True}, "P1")


def p2(m, start=2028):
    return PathChange(start, {"p2.payroll_multiple": m}, f"P2x{m}")


def p3(thr, look, start=2028):
    return PathChange(start, {"p3.active": True, "p3.client_threshold": thr, "p3.lookback_years": look}, f"P3_{int(thr * 100)}pct_{look}y")


def scenario_list() -> list[Scenario]:
    sc = [Scenario("baseline", "baseline", ())]
    sc += [Scenario("P1_2027", "P1", (p1(2027),), HIRES), Scenario("P1_2028", "P1", (p1(2028),), HIRES)]
    for m in (2, 3):
        sc += [Scenario(f"P2x{m}_2028", "P2", (p2(m, 2028),)), Scenario(f"P2x{m}_2027", "P2", (p2(m, 2027),))]
    for thr in (0.7, 0.8, 0.9, 1.0):
        for look in (3, 5):
            ch = p3(thr, look)
            sc.append(Scenario(ch.label, "P3", (ch,), (0.0,), CONCS, (("threshold", thr), ("lookback", look))))
    for m in (2, 3):
        for thr, look in ((0.7, 3), (0.9, 3), (0.9, 5), (1.0, 3), (1.0, 5)):
            ch3 = p3(thr, look)
            sc.append(Scenario(f"COMB_P1_P2x{m}_{ch3.label}", "combined", (p1(2027), p2(m), ch3), HIRES_COMB, CONCS_COMB, (("m", m), ("threshold", thr), ("lookback", look))))
    return sc


def run_one(path: PolicyPath, hh: Household, first_period: int, n_rep: int, seed: int, profits, strats, hire_cost: float, conc: float, hire_from: int = 0) -> tuple[dict[str, Outcome], list[int]]:
    pol0 = path.baseline
    y0, y1 = int(pol0.v("asm.start_year")), int(pol0.v("asm.end_year"))
    years = list(range(y0, y1 + 1))
    burn = int(pol0.v("asm.client_share_burn_in_years"))
    m_emp, m_bus = paired_shocks(seed, n_rep, years, pol0)
    share = client_share_paths(seed, n_rep, y0 - burn, y1, conc, pol0)
    yb = np.asarray(profits, dtype=float)[None, :, None]
    shape = (len(profits), n_rep)
    outs = {"EMPLOYEE": simulate_employee(yb * m_emp[:, None, :], years, path, hh, shape), "SOLE_TRADER": simulate_sole_trader(yb * m_bus[:, None, :], years, path, hh, shape)}
    for s in strats:
        outs[f"BV:{s.name}"] = simulate_bv(yb * m_bus[:, None, :], years, path, hh, s, shape, first_period, hire_cost=hire_cost, client_share=share, burn=burn, hire_from=hire_from)
    return outs, years


def rows_from(outs: dict[str, Outcome], profits, meta: dict, static_names: dict[float, str] | None, keep_all: bool) -> tuple[list[dict], dict]:
    """Compact long rows: employee, sole trader, BV_BEST (highest mean terminal wealth, anti-abuse variants excluded), BV_STATIC (baseline-best strategy)
    and, if keep_all, every strategy.  Also returns per-profit arrays needed for tax paths."""
    sole, emp = outs["SOLE_TRADER"], outs["EMPLOYEE"]
    bv_names = [k for k in outs if k.startswith("BV:") and "antiabuse" not in k]
    wmean = np.array([outs[k].wealth_end.mean(axis=1) for k in bv_names])  # (strategies, profits)
    best_idx = wmean.argmax(axis=0)
    rows = []
    chosen: dict[str, list[str]] = {"BV_BEST": [], "BV_STATIC": []}

    def add(label, name, pi, prof):
        o = outs[name]
        d_sole, d_emp = o.wealth_end[pi] - sole.wealth_end[pi], o.wealth_end[pi] - emp.wealth_end[pi]
        rows.append({**meta, "profit_level": prof, "arrangement": label, "strategy": name, "wealth_end_mean": o.wealth_end[pi].mean(),
                     "total_tax_and_contrib_mean": o.total_tax()[pi].mean(), "tax_excl_ssc_mean": o.total_tax_excl_ssc()[pi].mean(), "ssc_mean": o.total_ssc()[pi].mean(),
                     "admin_cost_mean": o.admin[pi].mean(), "pension_base_per_year_mean": o.pension_base[pi].mean() / N_YEARS,
                     "owner_pay_per_year_mean": o.owner_pay[pi].mean() / N_YEARS, "reduced_rate_years_mean": o.reduced_rate_years[pi].mean(),
                     "adv_vs_sole_wealth_mean": d_sole.mean(), "adv_vs_sole_wealth_p10": np.quantile(d_sole, .1), "adv_vs_sole_wealth_p90": np.quantile(d_sole, .9),
                     "adv_vs_emp_wealth_mean": d_emp.mean(), "ledger_residual_max": o.ledger_residual})

    for pi, prof in enumerate(profits):
        for k in ("EMPLOYEE", "SOLE_TRADER"):
            add(k, k, pi, prof)
        add("BV_BEST", bv_names[best_idx[pi]], pi, prof)
        chosen["BV_BEST"].append(bv_names[best_idx[pi]])
        if static_names is not None:
            add("BV_STATIC", static_names[prof], pi, prof)
            chosen["BV_STATIC"].append(static_names[prof])
        if keep_all:
            for k in outs:
                if k.startswith("BV:"):
                    add(k, k, pi, prof)
    return rows, chosen


def taxpath_rows(outs: dict[str, Outcome], profits, names_by_label: dict[str, list[str]], meta: dict, years: list[int]) -> list[dict]:
    rows = []
    for label, names in names_by_label.items():
        for pi, prof in enumerate(profits):
            o = outs[names[pi]]
            tot = np.array([a[pi].mean() for a in o.tax_year_total])
            ssc = np.array([a[pi].mean() for a in o.tax_year_ssc])
            for y, a, b in zip(years, tot, ssc, strict=True):
                rows.append({**meta, "profit_level": prof, "arrangement": label, "strategy": names[pi], "year": y, "tax_total_mean": a, "tax_ssc_mean": b})
    return rows
