"""Population layer (comparison C): owner mixes, entry/exit response, budget, entrepreneur counts and a national-wealth bound.

NOTHING HERE IS ESTIMATED FROM DATA.  The mix of owner types in S0 (revenue, how profit is paid out, client concentration), the size of S0, the
sensitivity of the choice of arrangement, the destination of leavers and the speed of adjustment are all ASSUMPTIONS that are swept; the results
are conditional on them.  Per-owner tax paths and wealth come from the micro engine (outputs/population/*).

Owner type = (strategy category k, client concentration c, revenue level p); the mix is a product of three weight vectors (independence is an
assumption).  Categories: seven fixed archetype strategies plus 'OPT' (an owner who plans optimally: under current law the baseline-best strategy;
after a measure either keeps it (adapt=False, fixed behaviour) or re-optimises (adapt=True)).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from mgmt_tax.compare_b import PROFITS_B, REF_ONE_CLIENT, scenario_list

YEARS = np.arange(2026, 2041)
T = len(YEARS)
ARCH = ["thr_dist_ord", "thr_dist_vvpr", "thr_ret_vvpr_k5", "thr_lr_liq", "min_dist_vvpr", "min_lr_liq", "min_dist_ord"]
CATS = [*ARCH, "OPT"]
CONCS = (1.0, 0.95, 0.90, 0.80, 0.70, 0.50)
PROF = np.array(PROFITS_B, dtype=float)
START = {s.label: min([c.start_year for c in s.changes], default=0) for s in scenario_list()}


@dataclass(frozen=True)
class Mix:
    N0: float                 # number of S0 owners (supplied: about 351,000 zero-employee BV/SRL SMEs, share unverified)
    w_k: np.ndarray           # shares over CATS
    w_c: np.ndarray           # shares over CONCS
    w_p: np.ndarray           # shares over PROFITS_B

    def W(self) -> np.ndarray:
        return self.w_k[:, None, None] * self.w_c[None, :, None] * self.w_p[None, None, :]


def lognormal_weights(median: float, sigma: float) -> np.ndarray:
    """Discretise a lognormal revenue distribution on the profit grid (cells are the intervals between grid midpoints in logs)."""
    from math import erf, log, sqrt
    cdf = lambda x: 0.5 * (1 + erf((log(x) - log(median)) / (sigma * sqrt(2))))  # noqa: E731
    edges = np.concatenate([[0.0], np.sqrt(PROF[:-1] * PROF[1:]), [np.inf]])
    c = np.array([0.0 if e == 0 else (1.0 if np.isinf(e) else cdf(e)) for e in edges])
    w = np.diff(c)
    return w / w.sum()


class Table:
    """Per-owner yearly taxes and terminal wealth from outputs/population."""

    def __init__(self, folder: Path):
        tax = pd.read_csv(folder / "taxpath_all.csv.gz")
        wl = pd.read_csv(folder / "wealth_all.csv")
        self.tax: dict[tuple, np.ndarray] = {}
        self.wealth: dict[tuple, np.ndarray] = {}
        self.strategy: dict[tuple, list[str]] = {}
        for key, g in tax.groupby(["scenario", "concentration", "household", "arrangement"]):
            self.tax[key] = g.pivot(index="profit_level", columns="year", values="tax_total").sort_index().to_numpy()
        for key, g in wl.groupby(["scenario", "concentration", "household", "arrangement"]):
            g = g.sort_values("profit_level")
            self.wealth[key] = g.wealth_end.to_numpy()
            self.strategy[key] = g.strategy.tolist()

    def _k(self, scn: str, conc: float, hh: str, arr: str) -> tuple:
        for key in ((scn, conc, hh, arr), (scn, 1.0, hh, arr)):
            if key in self.tax:
                return key
        if scn.startswith("P3_") and conc == 1.0:
            return (REF_ONE_CLIENT["P3"], 1.0, hh, arr)
        raise KeyError((scn, conc, hh, arr))

    def t(self, scn, conc, hh, arr):
        return self.tax[self._k(scn, conc, hh, arr)]

    def w(self, scn, conc, hh, arr):
        return self.wealth[self._k(scn, conc, hh, arr)]

    def best_names(self, hh):
        return self.strategy[("baseline", 1.0, hh, "BV_BEST")]


def tensors(tbl: Table, scn: str, hh: str, adapt: bool) -> dict[str, np.ndarray]:
    """Arrays indexed [category, concentration, profit(, year)] for current law ('base') and the scenario ('scn')."""
    K, C, P = len(CATS), len(CONCS), len(PROF)
    bt, st = np.zeros((K, C, P, T)), np.zeros((K, C, P, T))
    bw, sw = np.zeros((K, C, P)), np.zeros((K, C, P))
    names = tbl.best_names(hh)
    for ki, cat in enumerate(CATS):
        for ci, conc in enumerate(CONCS):
            if cat != "OPT":
                bt[ki, ci], bw[ki, ci] = tbl.t("baseline", 1.0, hh, f"ARCH:{cat}"), tbl.w("baseline", 1.0, hh, f"ARCH:{cat}")
                st[ki, ci], sw[ki, ci] = tbl.t(scn, conc, hh, f"ARCH:{cat}"), tbl.w(scn, conc, hh, f"ARCH:{cat}")
            else:
                bt[ki, ci], bw[ki, ci] = tbl.t("baseline", 1.0, hh, "BV_BEST"), tbl.w("baseline", 1.0, hh, "BV_BEST")
                if adapt:
                    st[ki, ci], sw[ki, ci] = tbl.t(scn, conc, hh, "BV_BEST"), tbl.w(scn, conc, hh, "BV_BEST")
                else:   # keeps the baseline-best strategy of the revenue level
                    for pi, nm in enumerate(names):
                        a = nm.replace("BV:", "ARCH:")
                        st[ki, ci, pi], sw[ki, ci, pi] = tbl.t(scn, conc, hh, a)[pi], tbl.w(scn, conc, hh, a)[pi]
    return {"base_tax": bt, "scn_tax": st, "base_w": bw, "scn_w": sw, "sole_tax": tbl.t("baseline", 1.0, hh, "SOLE_TRADER"), "emp_tax": tbl.t("baseline", 1.0, hh, "EMPLOYEE"),
            "sole_w": tbl.w("baseline", 1.0, hh, "SOLE_TRADER"), "emp_w": tbl.w("baseline", 1.0, hh, "EMPLOYEE")}


def static_revenue(mix: Mix, X: dict) -> np.ndarray:
    """Yearly change in tax and contributions (EUR) with fixed behaviour and no entry/exit."""
    return mix.N0 * np.einsum("kcp,kcpt->t", mix.W(), X["scn_tax"] - X["base_tax"])


def periods(v: np.ndarray) -> dict[str, float]:
    ix = lambda ys: [int(y - YEARS[0]) for y in ys]  # noqa: E731
    return {"2027": float(v[ix([2027])].mean()), "2028-29": float(v[ix([2028, 2029])].mean()), "2030-39": float(v[ix(range(2030, 2040))].mean()), "2040": float(v[ix([2040])].mean()),
            "cumulative 2027-2040": float(v[ix(range(2027, 2041))].sum())}


def dynamic(mix: Mix, X: dict, scn: str, s: float, phi: float, eps: float, tau: float = 3.0, strict: bool = False) -> dict:
    """Entry/exit response.  loss_pp = fall in the owner's advantage over a sole trader in percentage points of revenue a year; the target stock of owners
    of the type is exp(-s * loss_pp) of today's (s = proportional fall per percentage point), approached with a lag of ``tau`` years from the start
    year of the scenario.  strict=True instead makes every owner whose advantage turns negative leave (the perfect-optimiser bound).  Leavers: a share
    phi stops all activity (their tax is lost), the rest becomes an employee (share eps) or a sole trader."""
    W = mix.W() * mix.N0
    loss_pp = np.clip((X["base_w"] - X["scn_w"]) / (len(YEARS) * PROF[None, None, :]) * 100.0, 0.0, None)
    adv_scn = X["scn_w"] - X["sole_w"][None, None, :]
    f = np.where(adv_scn < 0, 0.0, 1.0) if strict else np.exp(-s * loss_pp)
    f = np.minimum(f, 1.0)
    N = np.zeros((len(CATS), len(CONCS), len(PROF), T))
    N[..., 0] = W
    start = START[scn]
    for t in range(1, T):
        if YEARS[t] >= start:
            N[..., t] = N[..., t - 1] + (f * W - N[..., t - 1]) / tau
        else:
            N[..., t] = W
    L = W[..., None] - N
    dest = (1 - phi) * (eps * X["emp_tax"][None, None] + (1 - eps) * X["sole_tax"][None, None])
    rev = (N * (X["scn_tax"] - X["base_tax"]) + L * (dest - X["base_tax"])).sum(axis=(0, 1, 2))
    bv = N.sum(axis=(0, 1, 2))
    sole_new = (L * (1 - phi) * (1 - eps)).sum(axis=(0, 1, 2))
    lost = (L * (phi + (1 - phi) * eps)).sum(axis=(0, 1, 2))
    return {"revenue": rev, "bv_owners": bv, "self_employed_total": bv + sole_new, "entrepreneurs_lost": lost, "leavers": L.sum(axis=(0, 1, 2)), "N": N, "loss_pp": loss_pp, "f": f}


def mean_tax_per_owner(mix: Mix, X: dict, years=(2028, 2029)) -> float:
    ix = [int(y - YEARS[0]) for y in years]
    return float(np.einsum("kcp,kcpt->t", mix.W(), X["scn_tax"])[ix].mean())


# ---------------------------------------------------------------------------------------------------------------- national wealth bound
class NationalWealth:
    """Net-wealth quantile function of Belgian households from the observed HFCS 2023 aggregates (deciles p10-p90, mean) with a Pareto tail above p90."""

    def __init__(self, hfcs_csv: Path):
        rows = [ln for ln in open(hfcs_csv, encoding="utf-8") if not ln.startswith("#")]
        d = pd.read_csv(pd.io.common.StringIO("".join(rows)))
        pc = d[d.indicator == "net_wealth_percentile"].set_index("group").value
        self.targets = {"mean": float(d[(d.indicator == "net_wealth_mean")].value.iloc[0]), "median": float(d[(d.indicator == "net_wealth_median") & (d.group == "TOTAL")].value.iloc[0]),
                        "gini": float(d[d.indicator == "net_wealth_gini"].value.iloc[0]), "top10": float(d[d.indicator == "net_wealth_share_top10"].value.iloc[0]),
                        "top5": float(d[d.indicator == "net_wealth_share_top5"].value.iloc[0])}
        self.u = np.array([0.0] + [i / 10 for i in range(1, 10)])
        self.q = np.array([0.0] + [float(pc[f"p{10 * i}"]) for i in range(1, 10)])
        lower = np.trapezoid(self.q, self.u)   # integral of the piecewise-linear part over [0, 0.9]
        tail = self.targets["mean"] - lower
        r = tail / (0.1 * self.q[-1])
        self.alpha = r / (r - 1.0)
        self.p90 = self.q[-1]

    def quantile(self, u: np.ndarray) -> np.ndarray:
        u = np.asarray(u, dtype=float)
        low = np.interp(u, self.u, self.q)
        tail = self.p90 * (0.1 / np.clip(1 - u, 1e-12, None)) ** (1 / self.alpha)
        return np.where(u <= 0.9, low, tail)

    def sample(self, m: int) -> np.ndarray:
        return self.quantile((np.arange(m) + 0.5) / m)


def gini(w: np.ndarray) -> float:
    x = np.sort(np.asarray(w, dtype=float))
    n = len(x)
    cum = np.cumsum(x)
    return float((n + 1 - 2 * (cum / cum[-1]).sum()) / n)


def top_share(w: np.ndarray, q: float) -> float:
    x = np.sort(w)
    k = int(len(x) * q)
    return float(x[k:].sum() / x.sum())


PLACEMENTS = {   # density of owner-manager households over the national wealth percentile (assumptions)
    "above the median (50-95th percentile)": lambda u: ((u >= 0.5) & (u <= 0.95)).astype(float),
    "middle (30-80th percentile)": lambda u: ((u >= 0.3) & (u <= 0.8)).astype(float),
    "top-heavy (70-99th percentile)": lambda u: ((u >= 0.7) & (u <= 0.99)).astype(float),
}


def wealth_effect(nat: NationalWealth, mix: Mix, X: dict, hh_total: float, placement: str, eps: float, mode: str, seed: int = 1, m: int = 200_000) -> dict:
    """Change in the national wealth Gini if S0 owners lose ``mode`` = 'static' (the measures, fixed behaviour) or 'ban' (no management companies: every owner
    becomes an employee (share eps) or a sole trader) of their wealth, measured as the difference in 15-year accumulated wealth, placed at assumed
    positions of the national distribution.  The national distribution is held at the HFCS shape (steady-state comparison)."""
    rng = np.random.default_rng(seed)
    w = nat.sample(m)
    n_own = int(round(mix.N0 / hh_total * m))
    dens = PLACEMENTS[placement]((np.arange(m) + 0.5) / m)
    idx = rng.choice(m, size=n_own, replace=False, p=dens / dens.sum())
    W = mix.W().ravel()
    draw = rng.choice(len(W), size=n_own, p=W / W.sum())
    k, c, p = np.unravel_index(draw, mix.W().shape)
    if mode == "static":
        loss = X["base_w"][k, c, p] - X["scn_w"][k, c, p]
    else:
        dest = eps * X["emp_w"][p] + (1 - eps) * X["sole_w"][p]
        loss = X["base_w"][k, c, p] - dest
    w2 = w.copy()
    w2[idx] = np.clip(w2[idx] - loss, 0.0, None)
    return {"gini_before": gini(w), "gini_after": gini(w2), "top10_before": top_share(w, 0.9), "top10_after": top_share(w2, 0.9), "owner_share_of_wealth": float(w[idx].sum() / w.sum()),
            "mean_loss": float(loss.mean()), "loss_share_of_total_wealth": float(loss.sum() / w.sum()), "n_owners": n_own}
