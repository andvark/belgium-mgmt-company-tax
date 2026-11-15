"""Build docs/comparison_B_results.md from outputs/comparison_B (no hand-typed results)."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from mgmt_tax.compare_b import REF_ONE_CLIENT, scenario_list  # noqa: E402
from mgmt_tax.policy import load_policy  # noqa: E402
from mgmt_tax.shocks import client_share_paths  # noqa: E402

OUT = ROOT / "outputs" / "comparison_B"
N = 15
man = json.load(open(OUT / "manifest_B.json"))
runs = pd.read_csv(OUT / "comparison_B_runs.csv")
allstrat = pd.read_csv(OUT / "comparison_B_headline_all_strategies.csv")
paths = pd.read_csv(OUT / "taxpath_B_headline.csv")
pol = load_policy(ROOT / "configs" / "policy_be_2026_supplied.yaml", ROOT / "configs" / "assumptions.yaml", ROOT / "configs" / "proposals.yaml")

# One-client owners (concentration 100%) are simulated once per family; every other P3 / combined setting gives the SAME result for the arrangements
# reported here (BV_BEST, BV_STATIC, employee, sole trader) - verified exactly in the earlier full grid and by tests/invariants - so it is copied.
_copies = []
for _fam, _ref in REF_ONE_CLIENT.items():
    _rr = runs[(runs.scenario == _ref) & (runs.concentration == 1.0)]
    for _sc in scenario_list():
        if _sc.family == _fam and _sc.label != _ref:
            _c = _rr[_rr.hire_cost.isin((0.0,) if _fam == "P3" else (0.0, 5000.0))].copy()
            _c["scenario"] = _sc.label
            for _k, _v in _sc.params:
                _c[_k] = _v
            _copies.append(_c)
runs = pd.concat([runs, *_copies], ignore_index=True)
eur = lambda x: f"{x:,.0f}"  # noqa: E731
pct = lambda x: f"{100 * x:.0f}%"  # noqa: E731
HH, KEYP = "single", [60e3, 100e3, 160e3, 250e3]
K = ["household", "profit_level"]


def md(df):
    return "| " + " | ".join(df.columns) + " |\n|" + "|".join("---" for _ in df.columns) + "|\n" + "\n".join("| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)) + "\n"


# ------------------------------------------------------------------ core table: per (scenario, conc, household, profit) static and re-optimised effects
base = runs[runs.scenario == "baseline"]
b_best = base[base.arrangement == "BV_BEST"].set_index(K)
b_sole = base[base.arrangement == "SOLE_TRADER"].set_index(K)
b_emp = base[base.arrangement == "EMPLOYEE"].set_index(K)
W0 = b_best.wealth_end_mean
T0 = b_best.total_tax_and_contrib_mean
ADV0 = W0 - b_sole.wealth_end_mean          # baseline BV advantage over the sole trader (15 years, EUR)
scn = runs[runs.scenario != "baseline"]
gkeys = ["scenario", "family", "concentration", "household", "profit_level"]
extra = [c for c in ("m", "threshold", "lookback") if c in scn.columns]

static = scn[(scn.arrangement == "BV_STATIC") & (scn.hire_cost == 0)].set_index(gkeys + extra if False else gkeys)
bestrows = scn[(scn.arrangement == "BV_BEST") & (scn.hire_cost != 1.0)].copy()          # hire_cost 1 is a diagnostic, not a feasible choice
idx = bestrows.groupby(gkeys)["wealth_end_mean"].idxmax()
reopt = bestrows.loc[idx].set_index(gkeys)
sole_s = scn[(scn.arrangement == "SOLE_TRADER") & (scn.hire_cost == 0)].set_index(gkeys)
core = pd.DataFrame({"w_static": static.wealth_end_mean, "tax_static": static.total_tax_and_contrib_mean, "strat_static": static.strategy,
                     "w_reopt": reopt.wealth_end_mean, "tax_reopt": reopt.total_tax_and_contrib_mean, "strat_reopt": reopt.strategy, "hire": reopt.hire_cost,
                     "w_sole": sole_s.wealth_end_mean}).reset_index()
core = core.merge(W0.rename("w0").reset_index(), on=K).merge(T0.rename("t0").reset_index(), on=K).merge(ADV0.rename("adv0").reset_index(), on=K)
core["strat0"] = core.set_index(K).index.map(b_best.strategy)
core["loss_static"] = core.w0 - core.w_static
core["loss_reopt"] = core.w0 - core.w_reopt
core["tax_gain_static"] = core.tax_static - core.t0
core["tax_gain_reopt"] = core.tax_reopt - core.t0
core["removed_static"] = core.loss_static / core.adv0
core["removed_reopt"] = core.loss_reopt / core.adv0
core["adv_scn"] = core.w_reopt - core.w_sole


def pick(sc, conc=1.0, hh=HH, profits=KEYP):
    c = core[(core.scenario == sc) & (core.concentration == conc) & (core.household == hh) & core.profit_level.isin(profits)]
    return c.sort_values("profit_level")


L = []
L.append("# Comparison B: the three arrangements under each draft proposal (scenario assumptions)\n")
L.append(f"> **{man['banner']}.**\n>\n> **This is not an analysis of the government's proposal.** The draft text was not available. P1 (EUR 100,000 band, no employees) is as reported; P2 (payroll multiple 2x/3x) and P3 (client threshold 70-100%, lookback 3/5 years) "
         "come from second-hand excerpts and are run as grids of scenario assumptions; the mechanics below (what counts as payroll, how a cap is applied, how the client test is evaluated, what a hire costs) are **my modelling choices**, listed in section 1. "
         f"The rules underneath are the supplied, unconfirmed ones (status counts of rules used: `{man['rule_status_counts']}`; none is `checked`) - see [`hand_check_list.md`](hand_check_list.md). "
         "No entrepreneur count, behavioural response in entry/exit, or budget figure is computed here: that is comparison C.\n")
L.append(f"Generated by `scripts/make_report_b.py` from `outputs/comparison_B/` (code commit `{man['git_commit']}`; seed {man['seed']}; {man['n_rep']} paired replicates, identical revenue and client-share paths in every scenario; "
         f"{man['n_scenarios']} scenarios, {man['n_runs']} distinct runs x 3 household types = {man['n_simulations']} simulations (one-client owners are run once per family and copied: see the script); max ledger residual {man['max_ledger_residual']:.1e}). Mature company (already in its 5th taxable period in 2026), horizon 2026-2040, single owner unless stated.\n")

L.append("## 1. Scenario definitions (all assumptions)\n")
L.append("| proposal | start | as modelled | open / unknown |\n|---|---|---|---|\n"
         "| **P1** | 2027 (also 2028) | the 20% rate on the first EUR 100,000 requires the company to have a paid employee. An owner may hire at an annual employer cost c (EUR 5,000 / 10,000 / 15,000 / 20,000; c = 1 is a diagnostic 'free hire'); the cost is treated as an expense leaving the system (no tax on it counted) | what counts as an employee (hours, months, relatives, flexi-jobs); minimum cost c |\n"
         "| **P2** | 2028 (also 2027) | in each year the reduced regimes (VVPRbis dividends, liquidation-reserve allocations and dividends) are limited to payroll / m, payroll = director pay + hired employee's gross wage in the same year; the excess dividend is taxed at 30%, the excess allocation stays in the free reserve; the cap applies to old reserves too. m = 2 and 3 | payroll period, treatment of the excess, old reserves, liquidation payouts |\n"
         "| **P3** | 2028 | profit of a year in which the owner's largest-client share was >= threshold in every year of the lookback window (current year included) goes to an ordinary reserve (30% dividend or liquidation) and cannot enter the liquidation reserve; amounts of earlier years keep their regime. Threshold 70/80/90/100%, lookback 3/5 years | client definition, intermediaries and related clients, number of years, treatment of existing reserves |\n"
         "| **combined** | P1 2027, P2 and P3 2028 | all of the above together; owners may also raise their pay (fixed-pay strategies 60k/80k/100k) and hire | |\n\n"
         "Client concentration is **not data**: owners are simulated with a mean largest-client share of 100% (exactly one client: segment S1), 95, 90, 80, 70 or 50% and an assumed year-to-year fluctuation (sd 8 points, persistence 0.5, 5 years of history). Owners below the threshold are in S0 but untouched by P3. "
         "The share of S0 owners at each concentration is unknown (open input), so results are reported by concentration, not as an average.\n\n"
         "Two views of an owner's response are shown: **static** = keep the strategy that was best under current law and do not hire (fixed behaviour); **re-optimised** = the best of 28 strategies (including higher pay levels) and, for P1, the best hire choice, "
         "i.e. the owner adapts the tax planning but still exists. Neither includes entry or exit of companies.\n")

# ---------------------------------------------------------------- P1
L.append("## 2. P1: reduced corporate rate requires an employee\n")
rows = []
for p in KEYP:
    r = pick("P1_2027", profits=[p]).iloc[0]
    sub = runs[(runs.scenario == "P1_2027") & (runs.household == HH) & (runs.profit_level == p) & (runs.arrangement == "BV_BEST")].set_index("hire_cost").wealth_end_mean
    no, free = sub.get(0.0), sub.get(1.0)
    # break-even annual employer cost: linear interpolation of best-strategy wealth with a hire between cost 1 and the sweep points
    pts = sub[[c for c in sub.index if c >= 1.0]]
    cs, ws = np.array(pts.index, float), np.array(pts.values, float)
    cstar = "never worth it" if ws[0] <= no else (">20,000" if ws[-1] > no else eur(np.interp(no, ws[::-1], cs[::-1])))
    rows.append({"revenue/yr": eur(p), "baseline best strategy": r.strat0.replace("BV:", ""), "BV advantage vs sole trader, EUR/yr": eur(r.adv0 / N),
                 "P1 static loss, EUR/yr": eur(r.loss_static / N), "P1 re-optimised loss, EUR/yr": eur(r.loss_reopt / N), "chosen hire cost": "none" if r.hire == 0 else eur(r.hire),
                 "break-even hire cost, EUR/yr": cstar, "re-optimised strategy": r.strat_reopt.replace("BV:", "")})
L.append(md(pd.DataFrame(rows)))
arch = allstrat[(allstrat.scenario.isin(["baseline", "P1_2027"])) & (allstrat.hire_cost == 0) & (allstrat.profit_level == 100e3)].set_index(["scenario", "arrangement"]) if len(allstrat) else None
L.append("Reading: P1 changes the corporate rate only for a company that pays its director at least EUR 51,000 (otherwise the 20% rate was already lost after the first four periods). "
         "So the owners who are hit are those following the EUR 51,000 pay rule; owners on the 'minimum salary' strategy (best below about EUR 130,000 revenue under current law) are **unaffected**, which is why the static loss is zero at the lower revenue levels. "
         "The tax effect of P1 on the budget therefore depends on how many owners pay EUR 51,000 or more - the distribution of director pay in S0 is an open input (not available).\n")

# ---------------------------------------------------------------- archetypes
L.append("## 3. Who is hit by which proposal: archetype owners (single owner, EUR 100,000 and EUR 160,000 revenue, loss over 15 years per year, EUR)\n")
heads = [("P1_2027", "P1 (2027), no hire"), ("P2x2_2028", "P2 2x (2028)"), ("P2x3_2028", "P2 3x (2028)"), ("P3_90pct_3y", "P3 90%/3y, one client"), ("COMB_P1_P2x2_P3_90pct_3y", "combined 2x + 90%/3y, one client")]
arch_names = {"BV:thr_dist_vvpr": "pay 51k, annual VVPRbis dividend", "BV:thr_ret_vvpr_k5": "pay 51k, retain, VVPRbis lump", "BV:thr_lr_liq": "pay 51k, liquidation reserve, liquidate",
              "BV:min_dist_vvpr": "minimum pay, annual VVPRbis dividend", "BV:min_lr_liq": "minimum pay, liquidation reserve, liquidate", "BV:thr_dist_ord": "pay 51k, ordinary dividend only"}
tab = []
for p in (100e3, 160e3):
    for k, nm in arch_names.items():
        base_r = allstrat[(allstrat.scenario == "baseline") & (allstrat.arrangement == k) & (allstrat.profit_level == p) & (allstrat.hire_cost == 0)]
        if base_r.empty:
            continue
        row = {"revenue": eur(p), "owner strategy": nm}
        for sc, lab in heads:
            conc = 1.0
            r = allstrat[(allstrat.scenario == sc) & (allstrat.arrangement == k) & (allstrat.profit_level == p) & (allstrat.hire_cost == 0) & (allstrat.concentration == conc)]
            row[lab] = eur((base_r.wealth_end_mean.iloc[0] - r.wealth_end_mean.iloc[0]) / N) if len(r) else "n/a"
        tab.append(row)
L.append(md(pd.DataFrame(tab)))
L.append("A loss here is the owner's after-tax loss with behaviour held fixed (no hire, same strategy); at zero return it equals the extra tax paid over the 15 years, per year. **The government's static revenue depends on the mix of these owner types in S0/S1, which is not known.** "
         "Pattern in the table: P1 touches only owners who pay EUR 51,000 or more and leaves the 'minimum pay' owners and the ordinary-dividend owner (who gets no reduced regime anyway) untouched or only through the corporate rate; "
         "for annual-dividend and liquidation-reserve owners with one client P3 is the largest single hit; for 'retain, then take a lump after five years' P2 is the largest hit, because a lump exceeds the yearly capacity payroll / m; and an owner who uses only the ordinary 30% routes is unaffected by P2 and P3.\n")

# ---------------------------------------------------------------- P2
L.append("## 4. P2: payroll-linked cap on the reduced dividend regimes (single owner)\n")
rows = []
for sc, lab in (("P2x2_2028", "2x from 2028"), ("P2x3_2028", "3x from 2028"), ("P2x2_2027", "2x from 2027"), ("P2x3_2027", "3x from 2027")):
    for p in KEYP:
        r = pick(sc, profits=[p]).iloc[0]
        rows.append({"scenario": lab, "revenue/yr": eur(p), "baseline best": r.strat0.replace("BV:", ""), "static loss EUR/yr": eur(r.loss_static / N), "re-optimised loss EUR/yr": eur(r.loss_reopt / N),
                     "% of BV advantage removed (re-optimised)": pct(r.removed_reopt), "re-optimised strategy": r.strat_reopt.replace("BV:", "")})
L.append(md(pd.DataFrame(rows)))
L.append("Owners can partly neutralise a payroll-linked cap by raising their own pay (fixed-pay strategies at 60k/80k/100k are in the strategy set) - at the price of 45-50% income tax plus contributions on the extra pay; the re-optimised column shows what is left after that response. "
         "A hire adds only its gross wage to payroll and never pays for itself under P2 alone.\n")

# ---------------------------------------------------------------- P3 grid
L.append("## 5. P3: client-concentration test (single owner, EUR 100,000 revenue)\n")
for conc, lab in ((1.0, "one client (S1: concentration 100%)"), (0.9, "mean largest-client share 90%"), (0.8, "mean largest-client share 80%")):
    t = core[(core.family == "P3") & (core.concentration == conc) & (core.household == HH) & (core.profit_level == 100e3)].copy()
    if t.empty:
        continue
    t["threshold"] = t.scenario.str.extract(r"P3_(\d+)pct")[0].astype(int)
    t["lookback"] = t.scenario.str.extract(r"_(\d)y")[0].astype(int)
    piv = t.pivot(index="threshold", columns="lookback", values="removed_reopt").map(pct)
    piv.columns = [f"lookback {c}y" for c in piv.columns]
    piv.insert(0, "threshold", [f"{i}%" for i in piv.index])
    L.append(f"**Owner with {lab}: share of the BV advantage over a sole trader removed (re-optimised)**\n")
    L.append(md(piv.reset_index(drop=True)))
rows = []
for conc in (1.0, 0.95, 0.90, 0.80, 0.70, 0.50):
    r = {"mean largest-client share": f"{conc:.0%}"}
    for sc, lab in (("P3_70pct_3y", "70%/3y"), ("P3_90pct_3y", "90%/3y"), ("P3_90pct_5y", "90%/5y"), ("P3_100pct_3y", "100%/3y")):
        c = core[(core.scenario == sc) & (core.concentration == conc) & (core.household == HH) & (core.profit_level == 100e3)]
        r[lab] = pct(c.removed_reopt.iloc[0]) if len(c) else "n/a"
    rows.append(r)
L.append("**By owner concentration: share of the BV advantage removed (re-optimised, EUR 100,000 revenue, single owner)**\n")
L.append(md(pd.DataFrame(rows)))
# binding frequency diagnostic
diag = []
for conc in (1.0, 0.95, 0.90, 0.80, 0.70):
    sh = client_share_paths(man["seed"], man["n_rep"], 2021, 2040, conc, pol)
    row = {"mean client share": f"{conc:.0%}"}
    for thr in (0.7, 0.9, 1.0):
        for look in (3, 5):
            bind = np.array([sh[i - look + 1:i + 1].min(axis=0) >= thr - 1e-12 for i in range(5 + 2, sh.shape[0])])   # years 2028-2040 (index 7+)
            row[f"{int(thr * 100)}%/{look}y"] = pct(bind[:13].mean())
    diag.append(row)
L.append("**How often the test binds** (share of owner-years 2028-2040 in which the profit of the year loses the reduced regimes, by the owner's mean client share; a diagnostic of the assumed client-share process, not data):\n")
L.append(md(pd.DataFrame(diag)))
L.append("An owner with exactly one client is always caught whatever the threshold and lookback; the grid only matters for owners with several clients, and **how many such owners exist in S0 is the open data input** (the 80,000 'single-person management companies' claim is unverified and defined differently from S1).\n")

# ---------------------------------------------------------------- combined
L.append("## 6. Combined (P1 2027 + P2 + P3 2028), re-optimised, single owner\n")
c1 = core[(core.family == "combined") & (core.concentration == 1.0) & (core.household == HH) & core.profit_level.isin([100e3, 160e3])]
same = c1.groupby("profit_level").loss_reopt.nunique().max() == 1
L.append("**Owner with exactly one client (S1).** " + ("Every P2 multiple and every P3 threshold/lookback gives the **same** result (P3 always binds for such an owner and removes the reduced regimes altogether, so a payroll cap on them is moot): " if same else "") +
         "; ".join(f"at EUR {eur(p)} revenue the BV advantage over a sole trader falls from {eur(g.adv0.iloc[0] / N)} to {eur(g.adv_scn.iloc[0] / N)} a year ({pct(g.removed_reopt.iloc[0])} removed; best strategy {g.strat_reopt.iloc[0].replace('BV:', '')}, hire: {'none' if g.hire.iloc[0] == 0 else eur(g.hire.iloc[0])})"
                   for p, g in c1[c1.scenario == "COMB_P1_P2x2_P3_90pct_3y"].groupby("profit_level")) + ".\n")
rows = []
for sc in sorted(core[core.family == "combined"].scenario.unique()):
    r = core[(core.scenario == sc) & (core.concentration == 0.9) & (core.household == HH) & (core.profit_level == 100e3)]
    if r.empty:
        continue
    r = r.iloc[0]
    rows.append({"scenario": sc.replace("COMB_P1_", ""), "static loss EUR/yr": eur(r.loss_static / N), "re-optimised loss EUR/yr": eur(r.loss_reopt / N), "% of advantage removed": pct(r.removed_reopt),
                 "BV advantage after, EUR/yr": eur(r.adv_scn / N), "re-optimised strategy": r.strat_reopt.replace("BV:", ""), "hire": "none" if r.hire == 0 else eur(r.hire)})
L.append("**Owner with a mean largest-client share of 90% (EUR 100,000 revenue):** here the P2 multiple and the P3 parameters matter.\n")
L.append(md(pd.DataFrame(rows)))

# ---------------------------------------------------------------- break-even revenue
def breakeven(wbv: pd.Series, wref: pd.Series):
    d = (wbv - wref).sort_index()
    x, y = np.array(d.index, float), np.array(d.values, float)
    if y[0] > 0:
        return "<30k"
    for i in range(1, len(x)):
        if y[i] > 0 >= y[i - 1]:
            return eur(x[i - 1] + (0 - y[i - 1]) * (x[i] - x[i - 1]) / (y[i] - y[i - 1]))
    return ">250k"


L.append("## 7. Break-even revenue: below this a one-person BV is worse than a sole trader / an employee (single owner, EUR per year of revenue)\n")
rows = []
b = runs[(runs.household == HH)]
sole0 = b[(b.scenario == "baseline") & (b.arrangement == "SOLE_TRADER")].set_index("profit_level").wealth_end_mean
emp0 = b[(b.scenario == "baseline") & (b.arrangement == "EMPLOYEE")].set_index("profit_level").wealth_end_mean
bv0 = b[(b.scenario == "baseline") & (b.arrangement == "BV_BEST")].set_index("profit_level").wealth_end_mean
rows.append({"scenario": "current law", "vs sole trader": breakeven(bv0, sole0), "vs employee": breakeven(bv0, emp0)})
for sc, conc in (("P1_2027", 1.0), ("P2x2_2028", 1.0), ("P2x3_2028", 1.0), ("P3_90pct_3y", 1.0), ("P3_70pct_3y", 1.0), ("COMB_P1_P2x2_P3_90pct_3y", 1.0), ("COMB_P1_P2x3_P3_70pct_3y", 1.0)):
    s = b[(b.scenario == sc) & (b.concentration == conc) & (b.arrangement == "BV_BEST") & (b.hire_cost != 1.0)]
    best = s.groupby("profit_level").wealth_end_mean.max()
    rows.append({"scenario": f"{sc} (one client)", "vs sole trader": breakeven(best, sole0), "vs employee": breakeven(best, emp0)})
L.append(md(pd.DataFrame(rows)))
L.append("The vs-employee break-even is low (or below the grid) mostly because the supplied rules give the employee 38% social contributions and no professional-expense allowance (open input); treat it with the caveats of comparison A.\n")

# ---------------------------------------------------------------- timing and fiscal arithmetic per owner
L.append("## 8. Timing of the extra tax per owner and what it implies for the government's profile (single owner, EUR 100,000 revenue, one client, fixed strategy)\n")
arch8 = {"ARCH:thr_dist_vvpr": "pay 51k, annual VVPRbis dividend", "ARCH:thr_lr_liq": "pay 51k, liquidation reserve", "ARCH:min_dist_vvpr": "minimum pay, annual VVPRbis dividend", "ARCH:min_lr_liq": "minimum pay, liquidation reserve"}
pp = paths[(paths.profit_level == 100e3) & (paths.concentration == 1.0) & (paths.hire_cost == 0)]
periods = {"2027": [2027], "2028-29": [2028, 2029], "2030-39": list(range(2030, 2040)), "2040 (incl. liquidation)": [2040]}
rows = []
for a, alab in arch8.items():
    b0 = pp[(pp.scenario == "baseline") & (pp.arrangement == a)].set_index("year").tax_total_mean
    for sc, lab in heads:
        d = pp[(pp.scenario == sc) & (pp.arrangement == a)].set_index("year").tax_total_mean - b0
        r = {"owner": alab, "scenario": lab}
        for pl, ys in periods.items():
            r[pl] = eur(d.loc[ys].mean())
        rows.append(r)
tim = pd.DataFrame(rows)
L.append("Extra tax and contributions per owner per year (EUR; scenario minus current law, same replicates; **negative = the state collects less in that period**):\n")
L.append(md(tim))
L.append("**Deferral.** An owner who keeps the profit in the liquidation reserve pays the 10% levy every year under current law. When P2 or P3 keeps part of that profit out of the reserve, the levy is not paid and the extra tax (30% on liquidation) arrives only when the company is wound up - here in 2040, an artefact of the 15-year horizon. "
         "So for owners on this route the static effect on revenue in 2028-2039 is **negative** and positive only at the end; for owners who pay annual dividends the effect is positive at once. "
         "The sign and size of the early-year revenue therefore depend on the mix of owner types, which is not known.\n")
rows = []
for target, lab, per, sc in ((300e6, "2027 (EUR 300m projected)", "2027", "P1_2027"), (450e6, "2028-29 (EUR 450m a year projected)", "2028-29", "COMB_P1_P2x2_P3_90pct_3y")):
    for a, alab in arch8.items():
        b0 = pp[(pp.scenario == "baseline") & (pp.arrangement == a)].set_index("year").tax_total_mean
        d = (pp[(pp.scenario == sc) & (pp.arrangement == a)].set_index("year").tax_total_mean - b0).loc[periods[per]].mean()
        rows.append({"period": lab, "scenario": "P1" if sc == "P1_2027" else "combined 2x + 90%/3y", "owner archetype": alab, "extra tax per owner and year": eur(d),
                     "owners needed to reach the projection": eur(target / d) if d > 0 else "none: revenue falls or is zero"})
L.append("**Illustrative arithmetic, not an estimate.** Owners of a single archetype needed to raise the projected amount in that period (projection divided by the extra tax per owner and year); "
         "for scale, about 351,000 zero-employee BV/SRL SMEs were supplied (share unverified) and the size of S1 is unknown. It uses one revenue level and one archetype at a time; the real population is a mixture over revenue, pay and concentration.\n")
L.append(md(pd.DataFrame(rows)))

L.append("## 9. Household type (EUR 100,000 revenue, combined 2x + 90%/3y, one client): share of the BV advantage removed (re-optimised)\n")
rows = []
for hh in ("single", "couple_one_earner_2kids", "couple_two_earners_2kids"):
    r = core[(core.scenario == "COMB_P1_P2x2_P3_90pct_3y") & (core.concentration == 1.0) & (core.household == hh) & (core.profit_level == 100e3)].iloc[0]
    rows.append({"household": hh, "baseline BV advantage EUR/yr": eur(r.adv0 / N), "loss static EUR/yr": eur(r.loss_static / N), "loss re-optimised EUR/yr": eur(r.loss_reopt / N), "% removed": pct(r.removed_reopt)})
L.append(md(pd.DataFrame(rows)))

L.append("## 10. What this does and does not show\n")
L.append("- It shows, **under supplied-but-unconfirmed rules and my reading of second-hand proposal descriptions**, how each proposal changes the tax advantage of a one-person BV for a tax-minimising owner, by revenue level and owner type, and where the avoidance margins are (hire, higher pay, diversifying clients - the last is not modelled).\n"
         "- It does **not** show the number of entrepreneurs, the budget, or the wealth distribution, and does not model entry/exit, relocation, incidence or the choice of arrangement (WP3-4).\n"
         "- Owner types are archetypes: the distribution of director pay, retained profits and client concentration across S0 and S1 is **not known**; the budget result depends on it more than on any proposal parameter.\n"
         "- The loss columns use the 15-year terminal wealth including a liquidation in 2040; per-year figures are averages over 2026-2040 (so proposals starting in 2027/2028 are diluted by pre-start years).\n"
         "- A P3 owner could dip below the threshold by adding a minor client (cost unknown): not modelled; it would reduce the P3 effect.\n")
(ROOT / "docs" / "comparison_B_results.md").write_text("\n".join(L), encoding="utf-8")
core.to_csv(OUT / "comparison_B_effects.csv", index=False, float_format="%.8f", lineterminator="\n")
print("report written")
