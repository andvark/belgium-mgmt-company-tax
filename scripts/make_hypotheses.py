"""Build docs/hypotheses.md: every hypothesis, how it was tested, the evidence (numbers read from outputs/) and the verdict."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
A, B, P = ROOT / "outputs" / "comparison_A", ROOT / "outputs" / "comparison_B", ROOT / "outputs" / "population"
N = 15
eur = lambda x: f"{x:,.0f}"  # noqa: E731
pct = lambda x: f"{100 * x:.0f}%"  # noqa: E731
a = pd.read_csv(A / "comparison_A_baseline.csv")
s = a[(a.household == "single") & (a.cohort == "mature")]
eff = pd.read_csv(B / "comparison_B_effects.csv")
runs = pd.read_csv(B / "comparison_B_runs.csv")
mc = pd.read_csv(P / "static_revenue_mc.csv")
dyn = pd.read_csv(P / "dynamic_grid_central.csv")
strict = pd.read_csv(P / "strict_bound.csv")
be = pd.read_csv(P / "breakeven_mc.csv")
wb = pd.read_csv(P / "wealth_bound.csv")
ban = pd.read_csv(P / "ban_bound_budget.csv")
tor = pd.read_csv(P / "tornado.csv")
flip = pd.read_csv(P / "flip_shares.csv")
defer = pd.read_csv(P / "deferral_test.csv")
summ = json.load(open(P / "population_summary.json"))
allstrat = pd.read_csv(B / "comparison_B_headline_all_strategies.csv")
paths = pd.read_csv(B / "taxpath_B_headline.csv")
COMB = "COMB_P1_P2x2_P3_90pct_3y"


def e(sc, conc, p, col):
    return eff[(eff.scenario == sc) & (eff.concentration == conc) & (eff.household == "single") & (eff.profit_level == p)][col].iloc[0]


def bv(p, col="adv_vs_sole_wealth_mean", arr="BV_BEST"):
    return s[(s.arrangement == arr) & (s.profit_level == p)][col].iloc[0]


def mcv(scn, per, col, adapt=False):
    return mc[(mc.scenario == scn) & (mc.period == per) & (mc.adapt == adapt)][col].iloc[0]


def dv(scn, adapt, eps, sv, phi, col):
    return dyn[(dyn.scenario == scn) & (dyn.adapt == adapt) & (dyn.eps_employee_share == eps) & (dyn.s_per_pp == sv) & (dyn.phi_stop == phi)][col].iloc[0]


def breakeven(wbv, wref):
    d = (wbv - wref).sort_index()
    x, y = np.array(d.index, float), np.array(d.values, float)
    for i in range(1, len(x)):
        if y[i] > 0 >= y[i - 1]:
            return x[i - 1] + (0 - y[i - 1]) * (x[i] - x[i - 1]) / (y[i] - y[i - 1])
    return float("nan")


rb = runs[runs.household == "single"]
be0 = breakeven(rb[(rb.scenario == "baseline") & (rb.arrangement == "BV_BEST")].set_index("profit_level").wealth_end_mean, rb[(rb.scenario == "baseline") & (rb.arrangement == "SOLE_TRADER")].set_index("profit_level").wealth_end_mean)
emp100 = -bv(100000, arr="EMPLOYEE") / N
st_c = strict[(strict.scenario == "Combined central") & (~strict.adapt)].iloc[0, 2]
st_h = strict[(strict.scenario == "Combined harsh") & (~strict.adapt)].iloc[0, 2]
st_1 = strict[(strict.scenario == "P1 (2027)") & (~strict.adapt)].iloc[0, 2]
st_2 = strict[(strict.scenario == "P2 2x (2028)") & (~strict.adapt)].iloc[0, 2]
st_3 = strict[(strict.scenario == "P3 central (90%, 3y)") & (~strict.adapt)].iloc[0, 2]
cc = "Combined central"
w_m = wb[wb.case.str.startswith("Combined")]
w_b = wb[wb.case.str.startswith("NO")]
b2 = be[be.s_per_pp == 0.02]
b2p = b2[b2.r_phi0_EURm > 0]
phi_med = {sv: float(be[(be.s_per_pp == sv) & (be.r_phi0_EURm > 0)].phi_star.replace(np.inf, 2).median()) for sv in (0.02, 0.05, 0.10)}
nonrow = be.drop_duplicates("draw")
flips = flip.set_index(["median_revenue", "sigma"])


def hire_breakeven(sc, p, hh="single"):
    sub = runs[(runs.scenario == sc) & (runs.household == hh) & (runs.profit_level == p) & (runs.arrangement == "BV_BEST")].set_index("hire_cost").wealth_end_mean
    no = sub.get(0.0)
    pts = sub[[c for c in sub.index if c >= 1.0]]
    cs, ws = np.array(pts.index, float), np.array(pts.values, float)
    if ws[0] <= no:
        return 0.0
    if ws[-1] > no:
        return float("inf")
    return float(np.interp(no, ws[::-1], cs[::-1]))


def arch_loss(key, sc, p=100000):
    g = allstrat[(allstrat.arrangement == key) & (allstrat.profit_level == p) & (allstrat.hire_cost == 0)]
    b0 = g[g.scenario == "baseline"].wealth_end_mean.iloc[0]
    r = g[(g.scenario == sc) & (g.concentration == 1.0)].wealth_end_mean.iloc[0]
    return (b0 - r) / N


def d2040(arch, sc=COMB):
    pp = paths[(paths.profit_level == 100e3) & (paths.concentration == 1.0) & (paths.hire_cost == 0) & (paths.arrangement == arch)]
    return float(pp[(pp.scenario == sc) & (pp.year == 2040)].tax_total_mean.iloc[0] - pp[(pp.scenario == "baseline") & (pp.year == 2040)].tax_total_mean.iloc[0])


rows = []


def H(i, stmt, test, evid, verdict):
    rows.append((i, stmt, test, evid, verdict))


H("H1", "A one-person company gives a material tax advantage over working as an employee or a sole trader (the project owner's starting point).",
  "Comparison A: terminal wealth of the best-planned company vs sole trader and employee, same revenue, 300 paired paths.",
  f"EUR {eur(bv(100000) / N)} a year better than a sole trader at EUR 100k revenue ({pct(bv(100000, 'adv_vs_sole_pct_of_revenue'))} of revenue), EUR {eur(bv(250000) / N)} at EUR 250k; break-even revenue about EUR {be0 / 1000:.0f}k; the sole trader is EUR {eur(emp100)} a year ahead of the employee.",
  "**Supported** (on rules reported confirmed in the owner's review; work bonus and employer reductions not modelled)")
H("H2", "The advantage comes from retaining profits and extracting a lump sum after 3-5 years (deferral).",
  "Compare 'retain, then VVPRbis lump after 3 / 5 years or at the end' with 'pay the 18% dividend every year', at 0%, 2% and 3% real return.",
  f"Identical at 0% return (all three equal EUR {eur(defer.annual_vvprbis_dividend.iloc[0])} over 15 years); with 2% / 3% return deferral adds only EUR {eur(defer.deferral_gain_end_vs_annual.iloc[1])} / {eur(defer.deferral_gain_end_vs_annual.iloc[2])} = {pct(defer.deferral_gain_as_share_of_best.iloc[1])} / {pct(defer.deferral_gain_as_share_of_best.iloc[2])} of the best advantage.",
  "**Not supported.** The rate gap between the 9-18% exit and the 45-50% marginal rate on salary is the source; deferral is a minor extra")
lo, hi = flips.share_company_worse_than_sole_trader_today.min(), flips.share_company_worse_than_sole_trader_today.max()
H("H3", "Many one-person companies exist for tax optimisation (prevalence).",
  "Not testable without owner-level data. Indirect check: under 8 assumed revenue distributions, what share of owners would be better off as a sole trader today (and so must have other reasons)?",
  f"Between {pct(lo)} and {pct(hi)} of owners, depending on the assumed revenue distribution (median EUR 130k to 50k); the measures push an extra {pct(flip.share_who_flip.min())}-{pct(flip.share_who_flip.max())} of owners below break-even.",
  "**Cannot be tested** with the available data (needs the distribution of director pay, retained profits and revenue in S0). Conditional table only")
H("H4", "The proposals remove a large part of the company advantage.",
  "Comparison B: static and re-optimised loss for P1, P2 (2x, 3x), P3 (threshold 70-100% x lookback 3/5) and combined, by revenue and client concentration.",
  f"One-client owner at EUR 100k: P1 {pct(e('P1_2027', 1.0, 100000, 'removed_reopt'))}, P2 2x {pct(e('P2x2_2028', 1.0, 100000, 'removed_reopt'))}, P2 3x {pct(e('P2x3_2028', 1.0, 100000, 'removed_reopt'))}, P3 {pct(e('P3_90pct_3y', 1.0, 100000, 'removed_reopt'))}, all three {pct(e(COMB, 1.0, 100000, 'removed_reopt'))}. Owner with 80% from the biggest client under a 90% threshold: {pct(e('P3_90pct_3y', 0.8, 100000, 'removed_reopt'))}.",
  "**Supported for owners with one client; not supported for owners below the client threshold**")
_keys = ["BV:thr_dist_vvpr", "BV:thr_ret_vvpr_k5", "BV:thr_lr_liq", "BV:min_dist_vvpr", "BV:min_lr_liq", "BV:thr_dist_ord"]
_scs = ["P1_2027", "P2x2_2028", "P2x3_2028", "P3_90pct_3y", COMB]
_vals = np.array([[arch_loss(k_, s_) for s_ in _scs] for k_ in _keys])
H("H5", "The measures affect different owners very differently.",
  "Loss per owner by payout strategy (heatmap, EUR 100k revenue).", f"From EUR {eur(_vals.min())} to about EUR {eur(_vals.max())} a year across six payout strategies and five measure sets (e.g. an ordinary-dividend owner pays nothing extra under P2 or P3 but EUR {eur(arch_loss('BV:thr_dist_ord', 'P1_2027'))} under P1; the 'minimum pay' owner pays EUR {eur(arch_loss('BV:min_dist_vvpr', 'P1_2027'))} under P1 and EUR {eur(arch_loss('BV:min_dist_vvpr', 'P3_90pct_3y'))} under P3).", "**Supported**")
_be = {p_: hire_breakeven("P1_2027", p_) for p_ in (60e3, 100e3, 160e3, 250e3)}
_kk = ["adv"]
_hc = runs[(runs.scenario.isin(["P1_2027", "P1_2028"])) & (runs.arrangement == "BV_BEST") & (runs.hire_cost >= 5000)]
_g = _hc.groupby(["scenario", "household", "profit_level"]).wealth_end_mean.max().reset_index()
_no = runs[(runs.scenario.isin(["P1_2027", "P1_2028"])) & (runs.arrangement == "BV_BEST") & (runs.hire_cost == 0)].set_index(["scenario", "household", "profit_level"]).wealth_end_mean
_g["no"] = _g.set_index(["scenario", "household", "profit_level"]).index.map(_no)
_wins = int((_g.wealth_end_mean > _g.no + 1e-6).sum())
H("H6", "P1 can be avoided by hiring one employee.", "Hire grid (EUR 5k-20k a year, plus EUR 1 as a diagnostic); break-even hire cost.",
  f"Break-even hire cost for a single owner: EUR {eur(min(_be.values()))}-{eur(max(_be.values()))} a year across EUR 60k-250k of revenue, far below any realistic hire; a hire of EUR 5,000 beats no hire in {_wins} of {len(_g)} P1 cells (revenue, household, start year). Owners mostly switch to minimum pay instead.", "**Not supported** (hiring is rarely worth it; strategy switching is the avoidance)")
_p2 = eff[(eff.family == "P2") & (eff.concentration == 1.0) & (eff.household == "single")]
_off = ((_p2.loss_static - _p2.loss_reopt) / N)
H("H7", "P2 can be offset by paying a higher salary.", "Re-optimised vs static loss with fixed pay levels of EUR 60k/80k/100k in the strategy set.",
  f"At EUR 100k: static loss EUR {eur(e('P2x2_2028', 1.0, 100000, 'loss_static') / N)} vs re-optimised EUR {eur(e('P2x2_2028', 1.0, 100000, 'loss_reopt') / N)} a year (2x); the largest offset anywhere in the grid is EUR {eur(_off.max())} a year.", "**Not supported** (raising pay barely offsets the cap)" if _off.max() < 200 else "**Partly supported** (small offset)")
H("H8", "The P3 threshold and lookback matter.", "8 threshold x lookback settings x 6 client concentrations.",
  f"No effect for an owner with exactly one client (always caught: {pct(e('P3_90pct_3y', 1.0, 100000, 'removed_reopt'))} removed at every setting). For an owner with 90% of revenue from the biggest client the removed share runs from {pct(e('P3_100pct_3y', 0.9, 100000, 'removed_reopt'))} (100% threshold) to {pct(e('P3_70pct_3y', 0.9, 100000, 'removed_reopt'))} (70%).", "**Conditional on client concentration**, which is unknown")
H("H9", "The number of company owners (management companies) falls.",
  "Population layer: (i) strict bound - only owners whose advantage turns from non-negative to negative leave; (ii) smooth response, a fall of s per percentage point of lost advantage, s = 1-10%.",
  f"Strict bound: {100 * st_c:.1f}% of S0 for all three measures ({100 * st_h:.1f}% harsh), P1 {100 * st_1:.1f}%, P3 {100 * st_3:.1f}%, P2 {100 * st_2:.1f}%; at 351,000 owners that is about {round(st_c * 351000, -3):,.0f}. Smooth: {dv(cc, True, 0.5, 0.02, 0.0, 'bv_owners_2040_pct'):.1f}% by 2040 at s = 2% (an anchor from an unread UK study), {dv(cc, True, 0.5, 0.10, 0.0, 'bv_owners_2040_pct'):.1f}% at s = 10%.",
  "**Supported in sign; the size is conditional** on a sensitivity that no Belgian estimate identifies")
H("H10", "The number of entrepreneurs (company owners plus sole traders) falls.", "Same sweep, counting leavers who become sole traders as entrepreneurs.",
  f"Falls only through leavers who become employees or stop: with half of leavers employees, {dv(cc, True, 0.5, 0.02, 0.0, 'self_employed_2040_pct'):.1f}% at s = 2% and {dv(cc, True, 0.5, 0.10, 0.0, 'self_employed_2040_pct'):.1f}% at s = 10% by 2040, about half the fall in company owners; zero if all leavers become sole traders.",
  "**Not supported in general**: it depends on where leavers go")
H("H11", "Owner-manager households accumulate less wealth.", "Per-owner 15-year terminal wealth, measures vs current law, aggregated over the central mix.",
  f"Mean loss about EUR {round(w_m.mean_loss.mean(), -3) / 1000:.0f}k per owner over 15 years ({100 * w_m.loss_share_of_total_wealth.mean():.1f}% of national net wealth across all S0 owners).", "**Supported** (conditional on rules and mix)")
H("H12", "The national wealth distribution barely moves, bounded by the 'no management companies' case.", "National distribution rebuilt from observed HFCS 2023 aggregates (Gini fit 0.596 vs 0.604); S0 owners placed at assumed percentiles; measures and ban applied.",
  f"Change in national wealth Gini: {w_m.delta_gini.min():+.4f} to {w_m.delta_gini.max():+.4f} for the measures; {w_b.delta_gini.min():+.4f} to {w_b.delta_gini.max():+.4f} for the ban. Sign depends on where owners sit in the distribution.", "**Supported** (movement is small; direction not identified)")
H("H13", "The measures improve the budget.", "Static revenue over 4,000 random owner mixes (revenue, payout strategy, client concentration, size of S0 200-450k).",
  f"P1 alone: positive in every mix (median EUR {mcv('P1 (2027)', '2027', 'median'):,.0f}m in 2027). All three, 2028-29: median EUR {mcv(cc, '2028-29', 'median'):,.0f}m, but negative in {pct(mcv(cc, '2028-29', 'share_negative'))} of mixes.",
  "**Conditional**: P1 yes; the P2/P3 part can lower revenue in 2028-39")
H("H14", "The government's EUR 300m (2027) and EUR 450m a year (2028-29) are attainable.", "Share of random mixes reaching each projection (S0 up to 450k).",
  f"{pct(mcv('P1 (2027)', '2027', 'share_ge_300'))} of mixes reach EUR 300m from P1 alone in 2027; {pct(mcv(cc, '2028-29', 'share_ge_450'))} reach EUR 450m in 2028-29 (central mix, by assumption: EUR {dv(cc, True, 0.5, 0.0, 0.0, 'static_2028_29_EURm'):.0f}-{tor[tor.factor == 'central mix'].low.iloc[0]:.0f}m).", "**Plausible but not implied**: P1 alone reaches the 2027 figure in most mixes; EUR 450m in 2028-29 needs a mix with few reserve-route owners")
H("H15", "The revenue profile is back-loaded (deferral).", "Static revenue by period over random mixes.",
  f"Combined, median EUR {mcv(cc, '2028-29', 'median'):,.0f}m in 2028-29 vs EUR {mcv(cc, '2030-39', 'median'):,.0f}m in 2030-39; owners using the liquidation reserve pay less in 2028-39 and far more in the liquidation year (EUR +{d2040('ARCH:thr_lr_liq') / 1000:,.0f}k and +{d2040('ARCH:min_lr_liq') / 1000:,.0f}k per owner in 2040).", "**Supported** for reserve-route owners")
_pc = summ["phi_cross_static_by_s"]
_pz = summ["phi_zero_by_s"]
H("H16", "Behavioural responses cancel the static budget gain.", "Entry/exit response with leavers becoming sole traders, employees or stopping altogether; break-even share who stop.",
  f"Leavers who become sole traders or employees ADD revenue (they pay more than company owners): EUR {dv(cc, True, 0.5, 0.02, 0.0, 'revenue_2028_29_EURm'):,.0f}m vs EUR {dv(cc, True, 0.5, 0.0, 0.0, 'revenue_2028_29_EURm'):,.0f}m static at s = 2%. The response only brings revenue back to the static level if about {pct(np.mean(list(_pc.values())))} of leavers stop working altogether, and to zero at {pct(_pz['0.1'])}-{pct(_pz['0.02'])} of leavers (central mix; {pct(phi_med[0.10])}-{pct(phi_med[0.02])} median over random mixes). EUR 450m is wiped out if {eur(summ['owners_to_stop_to_remove_450m'])} owners ({100 * summ['share_of_S0_to_stop_to_remove_450m']:.1f}% of S0, central mix; median {eur(nonrow.owners_who_must_stop_to_cancel_static.median())} across mixes) stop all activity.",
  "**Not supported for switching of arrangement; supported only for loss of activity** (stopping, emigration, reduced effort)")
H("H17", "Abolishing management companies altogether would raise far more than the draft.", "'Ban' bound: every owner becomes a sole trader or employee.",
  f"Extra tax and contributions EUR {ban[ban.household == 'single'].extra_tax_and_contributions_2028_29_EURm.min() / 1000:.1f}-{ban[ban.household == 'single'].extra_tax_and_contributions_2028_29_EURm.max() / 1000:.1f}bn a year (2028-29, single owner), so the combined measures capture about {pct(dv(cc, True, 0.5, 0.0, 0.0, 'static_2028_29_EURm') / ban[(ban.household == 'single') & (ban.leavers_employee_share == 0.5)].extra_tax_and_contributions_2028_29_EURm.iloc[0])} of that ceiling.", "**Supported** (an upper bound, not a policy option)")
H("H18", "The conclusions are robust to the assumptions.", "One-at-a-time changes from the central mix; random mixes.",
  f"Per-owner advantage and loss: robust to the design parameters tested. Budget 2028-29: from EUR {tor.loc[tor.factor == 'strategy mix', ['low', 'high']].min().min():,.0f}m to EUR {tor.loc[tor.factor == 'strategy mix', ['low', 'high']].max().max():,.0f}m by payout-strategy mix alone, EUR {tor.loc[tor.factor == 'median revenue', 'low'].iloc[0]:,.0f}-{tor.loc[tor.factor == 'median revenue', 'high'].iloc[0]:,.0f}m by median revenue.",
  "**Per-owner results robust; budget results not robust** to the owner mix")

L = ["# Hypotheses: how each was tested and what the model says\n",
     "> **Every verdict is conditional on (1) tax rules supplied by the project owner (most reported confirmed in the owner's checklist review of 15 November 2026; this analysis has not opened the primary pages itself), (2) proposal parameters that are scenario assumptions, and (3) for the population-level hypotheses, assumptions about the owner mix, the size of S0 and the response of owners that no data identify.** "
     "'Tested' means: run against the model under explicit sweeps; it does not mean the answer is known for Belgium. Generated by `scripts/make_hypotheses.py` from `outputs/`.\n",
     "| # | hypothesis | test | evidence | verdict |", "|---|---|---|---|---|"]
for r in rows:
    L.append("| " + " | ".join(x.replace("|", "/") for x in r) + " |")
nsup = sum(1 for r in rows if r[4].startswith("**Supported"))
L.append(f"\nSummary: {len(rows)} hypotheses; {nsup} supported, the rest not supported, partly supported, conditional on an unknown input, or untestable with available data. Hypothesis H3 (prevalence of tax-motivated companies) cannot be tested at all without owner-level data.\n")
L.append("## What would change the verdicts\n")
L.append("- **Rules** (`hand_check_list.md`): most are reported confirmed; H1, H2 and H4-H8 would still move with whether the owner's shares meet the VVPRbis conditions, the timing of the anti-abuse rule, the 7.2% municipal average, and the benefits-in-kind rule.\n"
         "- **The draft text** instead of second-hand excerpts: H4, H7, H8 and the budget hypotheses H13-H15.\n"
         "- **Owner-level data** (director pay, retained profits, revenue, client concentration in S0): H3, H13-H15 and H18 become testable; the owner mix is the largest single driver of the budget result.\n"
         "- **An estimate of how owners respond** (incorporation elasticity for Belgium): H9, H10 and H16.\n")
(ROOT / "docs" / "hypotheses.md").write_text("\n".join(L), encoding="utf-8")
print("hypotheses.md written;", len(rows), "hypotheses")
