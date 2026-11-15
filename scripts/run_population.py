"""Comparison C: population-level tests of the hypotheses, as explicit sweeps over assumptions (no data identify them).  Usage: python scripts/run_population.py"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from mgmt_tax import population as pop  # noqa: E402

OUT = ROOT / "outputs" / "population"
tbl = pop.Table(OUT)
HFCS = ROOT / "data" / "hfcs_wealth_targets_BE_2023.csv"
nat = pop.NationalWealth(HFCS)
HH_TOTAL = 5.219e6   # private households, fitted in the earlier model to published composition data (derived)
N0_SUPPLIED = 351_000.0
SC = {"P1 (2027)": "P1_2027", "P2 2x (2028)": "P2x2_2028", "P2 3x (2028)": "P2x3_2028", "P3 mild (100%, 5y)": "P3_100pct_5y", "P3 central (90%, 3y)": "P3_90pct_3y",
      "P3 harsh (70%, 3y)": "P3_70pct_3y", "Combined mild": "COMB_P1_P2x2_P3_100pct_5y", "Combined central": "COMB_P1_P2x2_P3_90pct_3y", "Combined harsh": "COMB_P1_P2x3_P3_70pct_3y"}
COMBS = ["Combined mild", "Combined central", "Combined harsh"]
cache: dict = {}


def X(scn, hh="single", adapt=False):
    key = (scn, hh, adapt)
    if key not in cache:
        cache[key] = pop.tensors(tbl, scn, hh, adapt)
    return cache[key]


def central(N0=N0_SUPPLIED, median=90000.0, sigma=0.6, s1=0.40, wk=None):
    wk = np.array([0.10, 0.25, 0.10, 0.05, 0.15, 0.05, 0.05, 0.25]) if wk is None else np.asarray(wk, float)
    others = np.array([0.10, 0.15, 0.15, 0.10, 0.10])
    wc = np.concatenate([[s1], (1 - s1) * others / others.sum()])
    return pop.Mix(N0, wk / wk.sum(), wc, pop.lognormal_weights(median, sigma))


R = {}   # key numbers for the hypothesis report
rng = np.random.default_rng(20261115)

# ------------------------------------------------------------------------------------------------------------------ 1. static revenue over random mixes
n = 4000
med, sig = rng.uniform(45e3, 150e3, n), rng.uniform(0.3, 0.9, n)
WP = np.array([pop.lognormal_weights(m, s) for m, s in zip(med, sig, strict=True)])
WK = rng.dirichlet(np.ones(len(pop.CATS)), n)
s1 = rng.uniform(0, 1, n)
WC = np.concatenate([s1[:, None], (1 - s1)[:, None] * rng.dirichlet(np.ones(5), n)], axis=1)
N0s = rng.uniform(200e3, 450e3, n)
ix = lambda ys: [int(y - pop.YEARS[0]) for y in ys]  # noqa: E731


def period_tensor(Xd):
    d = Xd["scn_tax"] - Xd["base_tax"]
    return np.stack([d[..., ix([2027])].mean(-1), d[..., ix([2028, 2029])].mean(-1), d[..., ix(range(2030, 2040))].mean(-1), d[..., ix([2040])].mean(-1), d[..., ix(range(2027, 2041))].sum(-1)], axis=-1)


QN = ["2027", "2028-29", "2030-39", "2040", "cumulative 2027-2040"]
feat = pd.DataFrame({"median_revenue": med, "sigma": sig, "share_S1": s1, "N0": N0s, "share_OPT": WK[:, 7], "share_pay51_dividend_or_ordinary": WK[:, 0] + WK[:, 1] + WK[:, 6],
                     "share_reserve_routes": WK[:, 3] + WK[:, 5], "share_retain_lump": WK[:, 2]})
mc_rows, corr_rows = [], []
for name, scn in SC.items():
    for adapt in (False, True):
        D = period_tensor(X(scn, "single", adapt))
        out = np.einsum("n,nk,nc,np,kcpq->nq", N0s, WK, WC, WP, D) / 1e6    # EUR million
        for qi, q in enumerate(QN):
            mc_rows.append({"scenario": name, "adapt": adapt, "period": q, "p05": np.percentile(out[:, qi], 5), "p25": np.percentile(out[:, qi], 25), "median": np.median(out[:, qi]),
                            "p75": np.percentile(out[:, qi], 75), "p95": np.percentile(out[:, qi], 95), "max": out[:, qi].max(), "share_negative": float((out[:, qi] < 0).mean()),
                            "share_ge_300": float((out[:, qi] >= 300).mean()), "share_ge_450": float((out[:, qi] >= 450).mean())})
        if name == "Combined central" and not adapt:
            R["mc_comb_central_2028_29"] = out[:, 1]
            for f in feat.columns:
                corr_rows.append({"driver": f, "spearman_with_2028_29_revenue": float(pd.Series(feat[f]).corr(pd.Series(out[:, 1]), method="spearman"))})
        if name == "P1 (2027)" and not adapt:
            R["mc_p1_2027"] = out[:, 0]
mc = pd.DataFrame(mc_rows)
mc.to_csv(OUT / "static_revenue_mc.csv", index=False, float_format="%.4f")
pd.DataFrame(corr_rows).to_csv(OUT / "static_revenue_drivers.csv", index=False, float_format="%.4f")
# the largest possible static yield: every owner of the single most affected type
Dc = period_tensor(X("COMB_P1_P2x2_P3_90pct_3y", "single", False))
R["max_yield_per_owner_2028_29"] = float(Dc[..., 1].max())
R["max_static_2028_29_all_owners_most_affected_type_EURm"] = float(Dc[..., 1].max() * 450e3 / 1e6)
R["max_static_2028_29_at_supplied_N0_EURm"] = float(Dc[..., 1].max() * N0_SUPPLIED / 1e6)

# ------------------------------------------------------------------------------------------------------------------ 2. dynamic grid (central mix)
rows = []
for name in COMBS:
    scn = SC[name]
    for adapt in (False, True):
        Xd = X(scn, "single", adapt)
        mix = central()
        for eps in (0.0, 0.5):
            for s in (0.0, 0.01, 0.02, 0.05, 0.10):
                for phi in (0.0, 0.10, 0.25, 0.50, 1.0):
                    d = pop.dynamic(mix, Xd, scn, s, phi, eps)
                    st = pop.static_revenue(mix, Xd)
                    rows.append({"scenario": name, "adapt": adapt, "eps_employee_share": eps, "s_per_pp": s, "phi_stop": phi,
                                 "bv_owners_2030_pct": 100 * (d["bv_owners"][ix([2030])[0]] / mix.N0 - 1), "bv_owners_2040_pct": 100 * (d["bv_owners"][-1] / mix.N0 - 1),
                                 "self_employed_2040_pct": 100 * (d["self_employed_total"][-1] / mix.N0 - 1), "entrepreneurs_lost_2040": d["entrepreneurs_lost"][-1],
                                 "entrepreneurs_lost_2040_pct_of_S0": 100 * d["entrepreneurs_lost"][-1] / mix.N0, "bv_owners_lost_2040": mix.N0 - d["bv_owners"][-1],
                                 "revenue_2028_29_EURm": pop.periods(d["revenue"])["2028-29"] / 1e6, "revenue_cum_EURm": pop.periods(d["revenue"])["cumulative 2027-2040"] / 1e6,
                                 "static_2028_29_EURm": pop.periods(st)["2028-29"] / 1e6, "static_cum_EURm": pop.periods(st)["cumulative 2027-2040"] / 1e6})
dyn = pd.DataFrame(rows)
dyn.to_csv(OUT / "dynamic_grid_central.csv", index=False, float_format="%.4f")

# break-even stopping share over random mixes, and the number of owners who must stop activity to cancel the static gain
scn = SC["Combined central"]
Xd = X(scn, "single", True)
be_rows = []
for i in range(1500):
    mix = pop.Mix(N0s[i], WK[i], WC[i], WP[i])
    st = pop.periods(pop.static_revenue(mix, Xd))["2028-29"]
    rho = pop.mean_tax_per_owner(mix, Xd)
    nstop = st / rho if st > 0 else 0.0
    for s in (0.01, 0.02, 0.05, 0.10):
        r0 = pop.periods(pop.dynamic(mix, Xd, scn, s, 0.0, 0.5)["revenue"])["2028-29"]
        r1 = pop.periods(pop.dynamic(mix, Xd, scn, s, 1.0, 0.5)["revenue"])["2028-29"]
        phi_star = 0.0 if r0 <= 0 else (np.inf if r1 >= 0 else r0 / (r0 - r1))
        be_rows.append({"draw": i, "s_per_pp": s, "static_2028_29_EURm": st / 1e6, "r_phi0_EURm": r0 / 1e6, "r_phi1_EURm": r1 / 1e6, "phi_star": phi_star, "N0": mix.N0,
                        "owners_who_must_stop_to_cancel_static": nstop, "share_of_S0": nstop / mix.N0})
be = pd.DataFrame(be_rows)
be.to_csv(OUT / "breakeven_mc.csv", index=False, float_format="%.4f")
# the 450m question: owners who must stop all activity to remove EUR 450m of revenue, at the central mix
mixc = central()
rho_c = pop.mean_tax_per_owner(mixc, Xd)
R["tax_per_owner_central_2028_29"] = rho_c
R["owners_to_stop_to_remove_450m"] = 450e6 / rho_c
R["share_of_S0_to_stop_to_remove_450m"] = 450e6 / rho_c / N0_SUPPLIED

# ------------------------------------------------------------------------------------------------------------------ 3. strict perfect-optimiser bound and flip shares
rows = []
for name in COMBS + ["P1 (2027)", "P2 2x (2028)", "P2 3x (2028)", "P3 central (90%, 3y)"]:
    scn = SC[name]
    for adapt in (False, True):
        d = pop.dynamic(central(), X(scn, "single", adapt), scn, 0.0, 0.0, 0.5, strict=True)
        rows.append({"scenario": name, "adapt": adapt, "share_of_S0_leaving_if_every_owner_optimises_strictly": float(d["leavers"][-1] / central().N0)})
strict = pd.DataFrame(rows)
strict.to_csv(OUT / "strict_bound.csv", index=False, float_format="%.5f")
rows = []
Xc = X("COMB_P1_P2x2_P3_90pct_3y", "single", True)
for m in (50e3, 70e3, 100e3, 130e3):
    for sg in (0.4, 0.7):
        w = pop.lognormal_weights(m, sg)
        a0 = Xc["base_w"][7, 0, :] - Xc["sole_w"]
        a1 = Xc["scn_w"][7, 0, :] - Xc["sole_w"]
        rows.append({"median_revenue": m, "sigma": sg, "share_company_worse_than_sole_trader_today": float(w[a0 < 0].sum()), "share_company_worse_after_measures_one_client": float(w[a1 < 0].sum())})
flip = pd.DataFrame(rows)
flip["share_who_flip"] = flip.share_company_worse_after_measures_one_client - flip.share_company_worse_than_sole_trader_today
flip.to_csv(OUT / "flip_shares.csv", index=False, float_format="%.5f")

# ------------------------------------------------------------------------------------------------------------------ 4. national wealth bound
rows = []
for name in COMBS:
    scn = SC[name]
    for adapt in (False, True):
        for pl in pop.PLACEMENTS:
            r = pop.wealth_effect(nat, central(), X(scn, "single", adapt), HH_TOTAL, pl, 0.5, "static")
            rows.append({"case": f"{name}, owners {'re-plan' if adapt else 'keep planning'}", "placement": pl, **r})
for eps in (0.0, 0.5, 1.0):
    for pl in pop.PLACEMENTS:
        r = pop.wealth_effect(nat, central(), X(SC["Combined central"], "single", True), HH_TOTAL, pl, eps, "ban")
        rows.append({"case": f"NO management companies (leavers: {int(100 * eps)}% employees)", "placement": pl, **r})
wealth = pd.DataFrame(rows)
wealth["delta_gini"] = wealth.gini_after - wealth.gini_before
wealth.to_csv(OUT / "wealth_bound.csv", index=False, float_format="%.6f")
R["nat_fit"] = {"mean": float(nat.sample(200000).mean()), "gini": pop.gini(nat.sample(200000)), "top10": pop.top_share(nat.sample(200000), 0.9), "targets": nat.targets, "alpha": nat.alpha}

# ------------------------------------------------------------------------------------------------------------------ 5. "no management companies": budget and count bound
rows = []
for hh in ("single", "couple_one_earner_2kids"):
    Xb = X("COMB_P1_P2x2_P3_90pct_3y", hh, True)
    for eps in (0.0, 0.5, 1.0):
        mix = central()
        dest = eps * Xb["emp_tax"] + (1 - eps) * Xb["sole_tax"]
        d = mix.N0 * np.einsum("kcp,kcpt->t", mix.W(), dest[None, None] - Xb["base_tax"])
        rows.append({"household": hh, "leavers_employee_share": eps, "extra_tax_and_contributions_2028_29_EURm": pop.periods(d)["2028-29"] / 1e6,
                     "extra_cum_2027_2040_EURm": pop.periods(d)["cumulative 2027-2040"] / 1e6})
ban = pd.DataFrame(rows)
ban.to_csv(OUT / "ban_bound_budget.csv", index=False, float_format="%.3f")

# ------------------------------------------------------------------------------------------------------------------ 6. tornado
cs = "Combined central"
scn = SC[cs]


def metric(mix, hh="single", adapt=False, scname=cs, dyn_=False):
    sc_ = SC[scname]
    Xd_ = X(sc_, hh, adapt)
    if dyn_:
        return pop.periods(pop.dynamic(mix, Xd_, sc_, 0.02, 0.25, 0.5)["revenue"])["2028-29"] / 1e6
    return pop.periods(pop.static_revenue(mix, Xd_))["2028-29"] / 1e6


base_m = central()
rows = [{"factor": "central mix", "low_label": "", "low": metric(base_m), "high_label": "", "high": metric(base_m), "dyn_low": metric(base_m, dyn_=True), "dyn_high": metric(base_m, dyn_=True)}]
spec = [("median revenue", central(median=60e3), "60k", central(median=130e3), "130k"), ("revenue spread (sigma)", central(sigma=0.3), "0.3", central(sigma=0.9), "0.9"),
        ("share with one client (S1)", central(s1=0.10), "10%", central(s1=0.80), "80%"), ("size of S0 (N0)", central(N0=250e3), "250k", central(N0=450e3), "450k"),
        ("strategy mix", central(wk=[1, 0, 0, 0, 0, 0, 0, 0]), "all ordinary dividends", central(wk=[0, 0, 0, 0, 0, 0, 0, 1]), "all optimisers")]
for f, lo, ll, hi, hl in spec:
    rows.append({"factor": f, "low_label": ll, "low": metric(lo), "high_label": hl, "high": metric(hi), "dyn_low": metric(lo, dyn_=True), "dyn_high": metric(hi, dyn_=True)})
rows.append({"factor": "household", "low_label": "single", "low": metric(base_m), "high_label": "one earner, 2 children", "high": metric(base_m, hh="couple_one_earner_2kids"),
             "dyn_low": metric(base_m, dyn_=True), "dyn_high": metric(base_m, hh="couple_one_earner_2kids", dyn_=True)})
rows.append({"factor": "owners re-plan", "low_label": "keep planning", "low": metric(base_m), "high_label": "re-plan", "high": metric(base_m, adapt=True), "dyn_low": metric(base_m, dyn_=True), "dyn_high": metric(base_m, adapt=True, dyn_=True)})
rows.append({"factor": "measure parameters", "low_label": "mild", "low": metric(base_m, scname="Combined mild"), "high_label": "harsh", "high": metric(base_m, scname="Combined harsh"),
             "dyn_low": metric(base_m, scname="Combined mild", dyn_=True), "dyn_high": metric(base_m, scname="Combined harsh", dyn_=True)})
tor = pd.DataFrame(rows)
tor.to_csv(OUT / "tornado.csv", index=False, float_format="%.3f")

# ------------------------------------------------------------------------------------------------------------------ 7. deferral versus rate gap (comparison A)
rows = []
for lab in ("baseline", "return_2pct", "return_3pct"):
    a = pd.read_csv(ROOT / "outputs" / "comparison_A" / f"comparison_A_{lab}.csv")
    a = a[(a.household == "single") & (a.cohort == "mature") & (a.profit_level == 100000)].set_index("arrangement")
    adv = a.adv_vs_sole_wealth_mean
    rows.append({"real_return": {"baseline": 0.0, "return_2pct": 0.02, "return_3pct": 0.03}[lab], "best_company_advantage": adv["BV_BEST"], "annual_vvprbis_dividend": adv["BV:thr_dist_vvpr"],
                 "retain_then_vvprbis_at_end": adv["BV:thr_ret_vvpr_end"], "retain_then_lump_after_5y": adv["BV:thr_ret_vvpr_k5"], "retain_then_lump_after_3y": adv["BV:thr_ret_vvpr_k3"],
                 "deferral_gain_end_vs_annual": adv["BV:thr_ret_vvpr_end"] - adv["BV:thr_dist_vvpr"], "deferral_gain_as_share_of_best": (adv["BV:thr_ret_vvpr_end"] - adv["BV:thr_dist_vvpr"]) / adv["BV_BEST"]})
defer = pd.DataFrame(rows)
defer.to_csv(OUT / "deferral_test.csv", index=False, float_format="%.4f")

# ------------------------------------------------------------------------------------------------------------------ summary json
json_out = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in R.items() if not k.startswith("mc_")}
json_out["mc_p1_2027_percentiles"] = {str(p): float(np.percentile(R["mc_p1_2027"], p)) for p in (5, 25, 50, 75, 95)}
json_out["mc_comb_central_2028_29_percentiles"] = {str(p): float(np.percentile(R["mc_comb_central_2028_29"], p)) for p in (5, 25, 50, 75, 95)}
json_out["households_total"] = HH_TOTAL
json_out["N0_supplied"] = N0_SUPPLIED
json_out["n_mixes"] = n
(OUT / "population_summary.json").write_text(json.dumps(json_out, indent=2), encoding="utf-8")
np.save(OUT / "mc_p1_2027.npy", R["mc_p1_2027"])
np.save(OUT / "mc_comb_central_2028_29.npy", R["mc_comb_central_2028_29"])
print("population analysis done")
