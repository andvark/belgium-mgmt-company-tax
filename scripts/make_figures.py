"""Social-media-ready figures (16:9, 2400x1350 px) from the comparison A and B outputs.  No number is typed by hand: everything is read from
outputs/ and the underlying values are written to docs/figures/figure_data.csv (the 'table view' of every chart).

Design rules (dataviz skill): validated categorical slots in fixed order (blue, orange, aqua, yellow, magenta), thin marks, solid hairline grid,
legend for >= 2 series plus selective direct labels, text in text colours (never the series colour), a surface-coloured ring on dots.
Every image carries its own caveat footer, because an image travels without the text around it.
"""

import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
A, B = ROOT / "outputs" / "comparison_A", ROOT / "outputs" / "comparison_B"
FIG = ROOT / "docs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
N = 15

for f in font_manager.findSystemFonts():
    if "/inter/" in f.lower() and "display" not in f.lower():
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]

# ---- tokens (reference palette; light surface) ----------------------------------------------------------------------------
SURF, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8985", "#e6e5e1"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#c9c8c2"
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95"]   # sequential blue 100 -> 600

FOOT = ("Model results under the project owner's tax rules (reported confirmed in the owner's own review, not checked here); proposals are scenario assumptions from "
        "second-hand descriptions, not the draft. Single owner, EUR 2026, 2026-2040, 300 simulated paths. Not a forecast.")
SRC = "Source: belgium-mgmt-company-tax model (open code and data in the repository)"

data_rows = []   # figure, series, x, y  -> docs/figures/figure_data.csv


def record(fig, series, x, y, note=""):
    data_rows.append({"figure": fig, "series": series, "x": x, "y": y, "note": note})


def canvas(title, subtitle, wrap=64, h=6.75):
    fig = plt.figure(figsize=(12, h), facecolor=SURF)
    t = "\n".join(textwrap.wrap(title, wrap))
    fig.text(0.05, 0.955, t, fontsize=23, fontweight="bold", color=INK, va="top", linespacing=1.15)
    nl = t.count("\n") + 1
    fig.text(0.05, 0.955 - 0.075 * nl - 0.01, "\n".join(textwrap.wrap(subtitle, 110)), fontsize=11.5, color=INK2, va="top", linespacing=1.3)
    fig.text(0.05, 0.072, "\n".join(textwrap.wrap(FOOT + "  " + SRC + ".", 160)), fontsize=7.6, color=MUTED, va="top", linespacing=1.35)
    return fig, nl


def style(ax, grid="y"):
    ax.set_facecolor(SURF)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=10.5, length=0)
    if grid == "y":
        ax.grid(axis="y", color=GRID, linewidth=1, linestyle="-")
    elif grid == "x":
        ax.grid(axis="x", color=GRID, linewidth=1, linestyle="-")
    ax.set_axisbelow(True)


def dot(ax, x, y, c, r=7):
    ax.plot([x], [y], "o", ms=r, color=c, mec=SURF, mew=2, zorder=5, clip_on=False)


def eur(x):
    return f"{x:,.0f}"


def k(x):
    return f"{x / 1000:,.1f}k"


# ---- data ---------------------------------------------------------------------------------------------------------------
eff = pd.read_csv(B / "comparison_B_effects.csv")
allstrat = pd.read_csv(B / "comparison_B_headline_all_strategies.csv")
paths = pd.read_csv(B / "taxpath_B_headline.csv")
runs = pd.read_csv(B / "comparison_B_runs.csv")
a = pd.read_csv(A / "comparison_A_baseline.csv")
a1 = a[(a.household == "single") & (a.cohort == "mature") & (a.profit_level == 100000)].set_index("arrangement")
COMB = "COMB_P1_P2x2_P3_90pct_3y"


def eff_row(sc, conc, p, hh="single"):
    r = eff[(eff.scenario == sc) & (eff.concentration == conc) & (eff.household == hh) & (eff.profit_level == p)]
    return r.iloc[0]


# =============================================================================================================================
# 1. headline card
# =============================================================================================================================
r_one = eff_row(COMB, 1.0, 100000)
r_90 = eff_row(COMB, 0.9, 100000)
r_80 = eff_row("P3_90pct_3y", 0.8, 100000)
fig, nl = canvas("One-person companies: how much of the tax advantage would the proposed measures remove?",
                 "Model scenarios built from reported draft measures (not the draft text): how much better off a one-person BV (company) owner is than a sole trader doing the same work, at EUR 100,000 annual revenue.")
tiles = [
    ("Today (current law)", f"EUR {k(r_one.adv0 / N)}", "a year better off as a one-person company than as a sole trader (best tax planning)", BLUE),
    ("After all three measures, owner with ONE client", f"EUR {k(r_one.adv_scn / N)}", f"a year: {r_one.removed_reopt:.0%} of the advantage removed, even after the owner re-plans", ORANGE),
    ("Owner with SEVERAL clients (80% from the biggest)", f"{r_80.removed_reopt:.0%}", "of the advantage removed under a 90% client threshold: the client test mostly misses them", AQUA),
]
for i, (lab, big, sub, c) in enumerate(tiles):
    x0 = 0.05 + i * 0.3125
    ax = fig.add_axes([x0, 0.24, 0.285, 0.42])
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.03", transform=ax.transAxes, fc="#f4f3ef", ec="none"))
    ax.add_patch(FancyBboxPatch((0.0, 0.0), 0.022, 1, boxstyle="square,pad=0", transform=ax.transAxes, fc=c, ec="none"))
    ax.text(0.09, 0.88, "\n".join(textwrap.wrap(lab, 30)), transform=ax.transAxes, fontsize=11.5, color=INK2, va="top", fontweight="semibold", linespacing=1.2)
    ax.text(0.09, 0.50, big, transform=ax.transAxes, fontsize=38, color=INK, va="center", fontweight="bold")
    ax.text(0.09, 0.27, "\n".join(textwrap.wrap(sub, 34)), transform=ax.transAxes, fontsize=10.5, color=INK2, va="top", linespacing=1.3)
    record("01_headline", lab, "value", big)
fig.savefig(FIG / "01_headline.png", dpi=200, facecolor=SURF)
plt.close(fig)

# =============================================================================================================================
# 2. advantage by revenue, today vs after (lines)
# =============================================================================================================================
profits = sorted(eff.profit_level.unique())
cur, one, s90 = [], [], []
for p in profits:
    cur.append(eff_row(COMB, 1.0, p).adv0 / N)
    one.append(eff_row(COMB, 1.0, p).adv_scn / N)
    s90.append(eff_row(COMB, 0.9, p).adv_scn / N)
fig, nl = canvas("The proposals would remove about half of the one-person-company advantage for a one-client owner",
                 "Yearly advantage of the best-planned one-person BV over a sole trader, by annual revenue. All three measures together (P1 from 2027, P2 at 2x payroll and P3 at a 90% client threshold from 2028).")
ax = fig.add_axes([0.07, 0.17, 0.74, 0.50 - 0.055 * (nl - 2)])
style(ax)
xs = np.array(profits) / 1000
for ys, c, lab in ((cur, BLUE, "Current law"), (s90, AQUA, "After all three: owner whose largest client is 90% of revenue"), (one, ORANGE, "After all three: owner with exactly one client")):
    ax.plot(xs, np.array(ys) / 1000, color=c, lw=2, solid_capstyle="round", solid_joinstyle="round", label=lab)
    dot(ax, xs[-1], ys[-1] / 1000, c)
    for xx, yy in zip(xs, ys, strict=True):
        record("02_advantage_by_revenue", lab, xx * 1000, round(yy, 1))
ax.axhline(0, color=INK2, lw=1)
ax.set_xlim(30, 250)
ax.set_xticks([50, 100, 150, 200, 250])
ax.set_xticklabels(["EUR 50k", "100k", "150k", "200k", "250k"])
ax.set_yticks(range(0, 51, 10))
ax.set_yticklabels([f"{v}k" if v else "0" for v in range(0, 51, 10)])
ax.set_ylim(-3, 54)
ax.set_xlabel("annual revenue billed to the client", color=INK2, fontsize=10.5, labelpad=8)
ax.set_ylabel("EUR per year", color=INK2, fontsize=10.5)
for ys, c, off in ((cur, BLUE, 0), (s90, AQUA, 0), (one, ORANGE, 0)):
    ax.text(xs[-1] + 4, ys[-1] / 1000, f"EUR {k(ys[-1])}", color=INK, fontsize=10.5, va="center", fontweight="semibold")
ax.legend(loc="upper left", frameon=False, fontsize=10.5, labelcolor=INK2, handlelength=1.6)
fig.savefig(FIG / "02_advantage_by_revenue.png", dpi=200, facecolor=SURF)
plt.close(fig)

# =============================================================================================================================
# 3. where each EUR 100 goes (stacked horizontal bars)
# =============================================================================================================================
rev = 100000 * N
rows = [("Employee", "EMPLOYEE"), ("Sole trader", "SOLE_TRADER"), ("One-person company:\nqualifying pay + dividends", "BV:thr_dist_vvpr"), ("One-person company:\nqualifying pay + liquidation reserve", "BV:thr_lr_liq")]
parts = ["Left to the owner", "Social contributions", "Personal income tax", "Corporate tax and annual fee", "Dividend, reserve and liquidation taxes", "Running costs"]
cols = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GRAY]
M = {}
for lab, key in rows:
    r = a1.loc[key]
    tax_ssc, tax_pit = r.ssc_mean, r.tax_pit
    corp = r.tax_corp_tax + r.tax_company_contribution
    div = r.tax_lr_levy + r.tax_dividend_wht + r.tax_liquidation_tax
    adm = r.admin_cost_mean
    kept = rev - tax_ssc - tax_pit - corp - div - adm
    M[lab] = [kept, tax_ssc, tax_pit, corp, div, adm]
    for pn, v in zip(parts, M[lab], strict=True):
        record("03_where_100_euro_goes", f"{lab.replace(chr(10), ' ')} | {pn}", "EUR per 100 billed", round(100 * v / rev, 2))
kept_emp, kept_bv = M[rows[0][0]][0] / rev, M[rows[3][0]][0] / rev
fig, nl = canvas(f"Out of EUR 100 billed to a client, the owner keeps about {100 * kept_emp:.0f} as an employee and {100 * kept_bv:.0f} with the best-planned company",
                 "Where EUR 100 of revenue goes over 15 years, at EUR 100,000 a year, single owner, current law. The employee bar is the employer's total cost (with the statutory professional-expense lump sum; work bonus not modelled). Lower contributions also mean lower pension-relevant income.", wrap=66)
ax = fig.add_axes([0.25, 0.31, 0.70, 0.33])
style(ax, grid="x")
ax.spines["bottom"].set_visible(False)
ypos = np.arange(len(rows))[::-1]
for yy, (lab, _) in zip(ypos, rows, strict=True):
    left = 0.0
    for v, c in zip(M[lab], cols, strict=True):
        w = 100 * v / rev
        ax.barh(yy, w - 0.35, left=left + 0.175, height=0.52, color=c, ec="none", zorder=3)
        if w >= 4.6:
            ax.text(left + w / 2, yy, f"{w:.0f}", ha="center", va="center", fontsize=11.5, fontweight="bold", color=INK if c in (YELLOW, GRAY, AQUA, MAGENTA) else "#ffffff", zorder=4)
        left += w
ax.set_yticks(ypos)
ax.set_yticklabels([r[0] for r in rows], fontsize=10.5, color=INK)
ax.set_xlim(0, 100)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0", "25", "50", "75", "EUR 100"])
handles = [plt.Rectangle((0, 0), 1, 1, fc=c) for c in cols]
fig.legend(handles, parts, loc="upper left", bbox_to_anchor=(0.05, 0.26), ncol=3, frameon=False, fontsize=9.5, labelcolor=INK2, handlelength=1.1, columnspacing=1.6)
fig.savefig(FIG / "03_where_100_euro_goes.png", dpi=200, facecolor=SURF)
plt.close(fig)

# =============================================================================================================================
# 4. advantage by strategy / exit route (ranked bars)
# =============================================================================================================================
names = [("thr_lr_liq", "Qualifying pay, profit in the liquidation reserve, liquidate (9.1% in total)"), ("min_lr_liq", "Minimum pay, liquidation reserve, liquidate (9.1%)"),
         ("thr_dist_vvpr", "Qualifying pay, dividends every year at 18% (VVPRbis)"), ("min_dist_vvpr", "Minimum pay, dividends every year at 18% (VVPRbis)"),
         ("thr_dist_ord", "Qualifying pay, ordinary dividends at 30%"), ("thr_lr_liq_antiabuse", "Reserve route, but the anti-abuse rule applies (payout taxed 30%)"),
         ("shell_full_pay", "Company that pays out all profit as salary")]
vals = [(lab, a1.loc[f"BV:{n}", "adv_vs_sole_wealth_mean"] / N) for n, lab in names]
fig, nl = canvas("The advantage is mostly the gap between a 9-18% exit rate and a 45-50% marginal rate on pay",
                 "Yearly advantage over a sole trader at EUR 100,000 revenue, by how the owner pays out profit. Holding profit back and taking it later adds nothing at 0% return: the rate matters, not the timing.", wrap=66)
ax = fig.add_axes([0.40, 0.17, 0.52, 0.52])
style(ax, grid="x")
ax.spines["bottom"].set_visible(False)
y = np.arange(len(vals))[::-1]
for yy, (lab, v) in zip(y, vals, strict=True):
    ax.barh(yy, v, height=0.5, color=BLUE if v > 0 else GRAY, ec="none", zorder=3)
    ax.text(max(v, 0) + 250, yy, f"{'+' if v > 0 else '-'}{eur(abs(v))}", va="center", ha="left", fontsize=10.5, fontweight="semibold", color=INK)
    record("04_advantage_by_exit_route", lab, "EUR per year vs sole trader", round(v, 1))
ax.set_yticks(y)
ax.set_yticklabels(["\n".join(textwrap.wrap(v[0], 46)) for v in vals], fontsize=9.6, color=INK, linespacing=1.15)
ax.set_xlim(-2000, 19500)
ax.set_xticks([0, 5000, 10000, 15000])
ax.set_xticklabels(["0", "5k", "10k", "EUR 15k"])
ax.axvline(0, color=INK2, lw=1)
fig.savefig(FIG / "04_advantage_by_exit_route.png", dpi=200, facecolor=SURF)
plt.close(fig)

# =============================================================================================================================
# 5. who is hit by which measure (heatmap with values)
# =============================================================================================================================
heads = [("P1_2027", "P1\nrate needs\nan employee"), ("P2x2_2028", "P2 at 2x\npayroll cap"), ("P2x3_2028", "P2 at 3x\npayroll cap"), ("P3_90pct_3y", "P3\nclient test\n(one client)"), (COMB, "All three\n(one client)")]
arch = [("BV:thr_lr_liq", "Qualifying pay, reserve, liquidate"), ("BV:min_lr_liq", "Minimum pay, reserve, liquidate"), ("BV:thr_dist_vvpr", "Qualifying pay, annual dividends"),
        ("BV:min_dist_vvpr", "Minimum pay, annual dividends"), ("BV:thr_ret_vvpr_k5", "Qualifying pay, retain, lump sum after 5 years"), ("BV:thr_dist_ord", "Qualifying pay, ordinary dividends only")]
base = allstrat[(allstrat.scenario == "baseline") & (allstrat.hire_cost == 0) & (allstrat.profit_level == 100000)].set_index("arrangement").wealth_end_mean
Mx = np.zeros((len(arch), len(heads)))
for i, (key, lab) in enumerate(arch):
    for j, (sc, hl) in enumerate(heads):
        r = allstrat[(allstrat.scenario == sc) & (allstrat.hire_cost == 0) & (allstrat.concentration == 1.0) & (allstrat.profit_level == 100000) & (allstrat.arrangement == key)]
        Mx[i, j] = (base[key] - r.wealth_end_mean.iloc[0]) / N
        record("05_who_is_hit", f"{lab} | {hl.replace(chr(10), ' ')}", "EUR per year lost", round(Mx[i, j], 1))
fig, nl = canvas("Who loses depends on how the owner pays out profit",
                 "Yearly after-tax loss for an owner who keeps the same tax planning (no re-planning), EUR 100,000 revenue, one client. Deeper blue = bigger loss.", wrap=66)
ax = fig.add_axes([0.33, 0.17, 0.62, 0.46 - 0.05 * (nl - 1)])
ax.set_facecolor(SURF)
for s in ax.spines.values():
    s.set_visible(False)
vmax = Mx.max()
for i in range(len(arch)):
    for j in range(len(heads)):
        v = Mx[i, j]
        idx = 0 if v < 1 else min(int(v / vmax * 5.99) + (0 if v / vmax > 0.04 else 0), 5)
        c = "#eeede9" if v < 1 else SEQ[idx]
        ax.add_patch(plt.Rectangle((j + 0.03, len(arch) - 1 - i + 0.04), 0.94, 0.92, fc=c, ec="none"))
        ax.text(j + 0.5, len(arch) - 1 - i + 0.5, "0" if v < 1 else eur(v), ha="center", va="center", fontsize=12, fontweight="bold" if v >= 1 else "normal",
                color="#ffffff" if (v >= 1 and idx >= 3) else INK)
ax.set_xlim(0, len(heads))
ax.set_ylim(0, len(arch))
ax.set_xticks(np.arange(len(heads)) + 0.5)
ax.set_xticklabels([h[1] for h in heads], fontsize=10, color=INK, linespacing=1.15)
ax.xaxis.tick_top()
ax.set_yticks(np.arange(len(arch)) + 0.5)
ax.set_yticklabels([x[1] for x in arch][::-1], fontsize=10, color=INK)
ax.tick_params(length=0)
fig.savefig(FIG / "05_who_is_hit.png", dpi=200, facecolor=SURF)
plt.close(fig)

# =============================================================================================================================
# 6. P3: client concentration
# =============================================================================================================================
concs = [0.5, 0.7, 0.8, 0.9, 0.95, 1.0]
fig, nl = canvas("The client test is a cliff: an owner with one client is always caught, one with several mostly is not",
                 "Share of the one-person-company advantage removed by P3, by the owner's average share of revenue from the biggest client (EUR 100,000 revenue; client-share fluctuation is an assumption, not data).", wrap=66)
ax = fig.add_axes([0.07, 0.24, 0.74, 0.38])
style(ax)
xpos = np.arange(len(concs))
series = [("P3_70pct_3y", "threshold 70%", BLUE), ("P3_90pct_3y", "threshold 90%", ORANGE), ("P3_100pct_3y", "threshold 100%", AQUA)]
for sc, lab, c in series:
    ys = []
    for cc in concs:
        r = eff[(eff.scenario == sc) & (eff.concentration == cc) & (eff.household == "single") & (eff.profit_level == 100000)]
        ys.append(100 * r.removed_reopt.iloc[0])
        record("06_client_test_cliff", f"{lab} (lookback 3 years)", cc, round(ys[-1], 1))
    ax.plot(xpos, ys, color=c, lw=2, marker="o", ms=8, mec=SURF, mew=2, label=f"{lab}, 3-year lookback", clip_on=False)
    j = 3
    ax.text(xpos[j] + 0.08, ys[j] + (3 if lab.endswith("70%") else (3 if lab.endswith("90%") else 3.5)), f"{ys[j]:.0f}%", color=INK, fontsize=10.5, fontweight="semibold", va="bottom")
ax.set_xticks(xpos)
ax.set_xticklabels([f"{int(c * 100)}%" if c < 1 else "100%\n(one client)" for c in concs])
ax.set_yticks(range(0, 61, 10))
ax.set_yticklabels([f"{v}%" for v in range(0, 61, 10)])
ax.set_ylim(-1, 60)
ax.set_xlabel("owner's average share of revenue from the largest client", color=INK2, fontsize=10.5, labelpad=8)
ax.legend(loc="center left", bbox_to_anchor=(0.0, 0.62), frameon=False, fontsize=10.5, labelcolor=INK2)
fig.savefig(FIG / "06_client_test_cliff.png", dpi=200, facecolor=SURF)
plt.close(fig)

# =============================================================================================================================
# 7. timing
# =============================================================================================================================
pp = paths[(paths.profit_level == 100000) & (paths.concentration == 1.0) & (paths.hire_cost == 0)]
yrs = list(range(2027, 2040))
tl = [("ARCH:thr_dist_vvpr", "Qualifying pay, dividends every year", BLUE), ("ARCH:thr_lr_liq", "Qualifying pay, liquidation reserve", ORANGE), ("ARCH:min_lr_liq", "Minimum pay, liquidation reserve", AQUA)]
fig, nl = canvas("Same reform, opposite sign for the budget in the first years, depending on how owners pay out profit",
                 "Extra tax per owner and year (all three measures, one client, EUR 100,000 revenue, owner keeps the same planning). Owners who use the liquidation reserve stop paying its levy (10% of the credited amount); the 30% comes only when the company is wound up.", wrap=66)
ax = fig.add_axes([0.08, 0.20, 0.71, 0.36])
style(ax)
ends = {}
for key, lab, c in tl:
    b0 = pp[(pp.scenario == "baseline") & (pp.arrangement == key)].set_index("year").tax_total_mean
    d = (pp[(pp.scenario == COMB) & (pp.arrangement == key)].set_index("year").tax_total_mean - b0).loc[yrs]
    ax.plot(yrs, d.values / 1000, color=c, lw=2, label=lab, solid_capstyle="round")
    dot(ax, yrs[-1], d.values[-1] / 1000, c)
    ends[lab] = d.values[-1]
    ax.text(yrs[-1] + 0.35, d.values[-1] / 1000, f"{'+' if d.values[-1] > 0 else '-'}{k(abs(d.values[-1]))}", color=INK, fontsize=10.5, fontweight="semibold", va="center")
    for yy, v in d.items():
        record("07_timing", lab, int(yy), round(v, 1))
    last = (pp[(pp.scenario == COMB) & (pp.arrangement == key)].set_index("year").tax_total_mean - b0).loc[2040]
    record("07_timing", lab, 2040, round(last, 1), "liquidation year, horizon artefact; not plotted")
ax.axhline(0, color=INK2, lw=1)
ax.set_xlim(2026.8, 2039.2)
ax.set_xticks([2027, 2029, 2031, 2033, 2035, 2037, 2039])
ax.set_yticks([-4, -2, 0, 2, 4, 6])
ax.set_yticklabels(["-4k", "-2k", "0", "+2k", "+4k", "+6k"])
ax.set_ylabel("EUR per owner per year", color=INK2, fontsize=10.5)
ax.set_ylim(-5.5, 7)
ax.legend(loc="center right", frameon=False, fontsize=10, labelcolor=INK2, bbox_to_anchor=(1.0, 0.66))
ax.text(2027, -5.35, "2040, the liquidation year, is off the chart: +%s and +%s for the two reserve owners" % (k(list(ends.values())[1] * 0 + pp[(pp.scenario == COMB) & (pp.arrangement == 'ARCH:thr_lr_liq') & (pp.year == 2040)].tax_total_mean.iloc[0] - pp[(pp.scenario == 'baseline') & (pp.arrangement == 'ARCH:thr_lr_liq') & (pp.year == 2040)].tax_total_mean.iloc[0]),
        k(pp[(pp.scenario == COMB) & (pp.arrangement == 'ARCH:min_lr_liq') & (pp.year == 2040)].tax_total_mean.iloc[0] - pp[(pp.scenario == 'baseline') & (pp.arrangement == 'ARCH:min_lr_liq') & (pp.year == 2040)].tax_total_mean.iloc[0])), color=MUTED, fontsize=9, va="bottom")
fig.savefig(FIG / "07_timing.png", dpi=200, facecolor=SURF)
plt.close(fig)


# =============================================================================================================================
# population-level figures (comparison C): every input about the owner mix is an ASSUMPTION that is swept
# =============================================================================================================================
POP = ROOT / "outputs" / "population"
FOOT_POP = ("Model results under the project owner's tax rules (reported confirmed in the owner's own review, not checked here); proposals are scenario assumptions; the owner mix, the size of S0 (351,000 supplied, "
            "share unverified) and the response of owners are assumptions that are swept, not data. Not a forecast.")


def canvas_pop(title, subtitle, wrap=64):
    global FOOT
    old = FOOT
    FOOT = FOOT_POP
    try:
        return canvas(title, subtitle, wrap)
    finally:
        FOOT = old


mc = pd.read_csv(POP / "static_revenue_mc.csv")
dyn = pd.read_csv(POP / "dynamic_grid_central.csv")
strict = pd.read_csv(POP / "strict_bound.csv")
tor = pd.read_csv(POP / "tornado.csv")
import json as _json  # noqa: E402
psum = _json.load(open(POP / "population_summary.json"))

# ---- 08: budget range across owner mixes ---------------------------------------------------------------------------------------
sel = [("P1 alone, 2027", "P1 (2027)", "2027", 300), ("All three, 2028-29", "Combined central", "2028-29", 450), ("All three, 2030-39", "Combined central", "2030-39", None)]
fig, nl = canvas_pop("Whether the draft raises EUR 300-450m depends on who the owners are, which nobody knows",
                     "Extra tax and contributions per year with owners keeping their planning, over 4,000 random mixes of revenue, payout strategy, client concentration and size of S0 (200-450k). Dot = median, thick bar = middle half, thin bar = 5th-95th percentile.", wrap=66)
ax = fig.add_axes([0.25, 0.25, 0.68, 0.30])
style(ax, grid="x")
ax.spines["bottom"].set_visible(False)
ypos = np.arange(len(sel))[::-1]
for yy, (lab, scn_, per, ref) in zip(ypos, sel, strict=True):
    r = mc[(mc.scenario == scn_) & (mc.period == per) & (~mc.adapt)].iloc[0]
    ax.plot([r.p05, r.p95], [yy, yy], color=BLUE, lw=2, alpha=0.45, solid_capstyle="round")
    ax.plot([r.p25, r.p75], [yy, yy], color=BLUE, lw=8, solid_capstyle="round")
    dot(ax, r["median"], yy, INK, r=8)
    ax.text(r.p95 + 25, yy, f"median {r['median']:,.0f}", color=INK, fontsize=10, va="center", fontweight="semibold")
    for q in ("p05", "p25", "median", "p75", "p95"):
        record("08_budget_range_across_mixes", lab, q, round(float(r[q]), 1), "EUR million per year")
    record("08_budget_range_across_mixes", lab, "share of mixes >= projection", round(float(r.share_ge_300 if ref == 300 else (r.share_ge_450 if ref == 450 else np.nan)), 3) if ref else "n/a")
for xv, lab, ha in ((300, "EUR 300m (2027 projection)  ", "right"), (450, "  EUR 450m (2028-29 projection)", "left")):
    ax.axvline(xv, color=INK2, lw=1)
    ax.text(xv, len(sel) - 0.42, lab, color=INK2, fontsize=9, ha=ha, va="bottom")
ax.axvline(0, color=INK2, lw=1)
ax.set_yticks(ypos)
ax.set_yticklabels([x[0] for x in sel], fontsize=10.5, color=INK)
ax.set_xlim(-700, 1500)
ax.set_xticks([-500, 0, 500, 1000, 1500])
ax.set_xticklabels(["-500", "0", "500", "1,000", "EUR 1,500m"])
r1 = mc[(mc.scenario == "P1 (2027)") & (mc.period == "2027") & (~mc.adapt)].iloc[0]
r2 = mc[(mc.scenario == "Combined central") & (mc.period == "2028-29") & (~mc.adapt)].iloc[0]
fig.text(0.05, 0.18, "\n".join(textwrap.wrap(f"Share of mixes reaching the projection: {r1.share_ge_300:.0%} for P1 alone in 2027 (EUR 300m); {r2.share_ge_450:.0%} for all three in 2028-29 (EUR 450m). "
         f"{r2.share_negative:.0%} of mixes give negative revenue in 2028-29, because owners who keep profit in the liquidation reserve stop paying its levy (10% of the credited amount).", 140)), fontsize=10.5, color=INK2, va="top", linespacing=1.3)
fig.savefig(FIG / "08_budget_range_across_mixes.png", dpi=200, facecolor=SURF)
plt.close(fig)

# ---- 09: break-even ------------------------------------------------------------------------------------------------------------------
cc = dyn[(dyn.scenario == "Combined central") & dyn.adapt & (dyn.eps_employee_share == 0.5)]
fig, nl = canvas_pop("Leavers who become sole traders or employees add revenue; it takes over a third of leavers stopping work to cancel that",
                     f"Extra revenue 2028-29 at an illustrative central owner mix, by the share of leavers who stop all activity. s = fall in the number of company owners per percentage point of revenue advantage lost. All lines cross the no-response line at about {np.mean(list(psum['phi_cross_static_by_s'].values())):.0%}; revenue reaches zero at {min(psum['phi_zero_by_s'].values()):.0%}-{max(psum['phi_zero_by_s'].values()):.0%}.", wrap=66)
ax = fig.add_axes([0.07, 0.19, 0.74, 0.38])
style(ax)
for sv, c, lab in ((0.0, GRAY, "no response (s = 0)"), (0.02, BLUE, "s = 2% per point"), (0.05, ORANGE, "s = 5% per point"), (0.10, AQUA, "s = 10% per point")):
    d = cc[cc.s_per_pp == sv].sort_values("phi_stop")
    ax.plot(d.phi_stop * 100, d.revenue_2028_29_EURm, color=c if sv else MUTED, lw=2, label=lab, solid_capstyle="round")
    dot(ax, 100, d.revenue_2028_29_EURm.iloc[-1], c if sv else MUTED)
    ax.text(103, d.revenue_2028_29_EURm.iloc[-1], f"{d.revenue_2028_29_EURm.iloc[-1]:,.0f}", color=INK, fontsize=10, va="center", fontweight="semibold")
    for xx, yy in zip(d.phi_stop * 100, d.revenue_2028_29_EURm, strict=True):
        record("09_breakeven", lab, xx, round(yy, 1), "EUR million, 2028-29")
ax.axhline(0, color=INK2, lw=1)
ax.set_xlim(0, 100)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0%", "25%", "50%", "75%", "100% of leavers stop"])
ax.set_ylabel("EUR million per year, 2028-29", color=INK2, fontsize=10.5)
ax.set_yticks([-2000, -1000, 0, 1000, 2000])
ax.set_yticklabels(["-2,000", "-1,000", "0", "1,000", "2,000"])
ax.legend(loc="lower left", frameon=False, fontsize=10, labelcolor=INK2)
fig.savefig(FIG / "09_breakeven.png", dpi=200, facecolor=SURF)
plt.close(fig)

# ---- 10: entrepreneurs / owners --------------------------------------------------------------------------------------------------------
cc = dyn[(dyn.scenario == "Combined central") & dyn.adapt & (dyn.eps_employee_share == 0.5) & (dyn.phi_stop == 0.0)].set_index("s_per_pp")
st = strict[(strict.scenario == "Combined central") & (~strict.adapt)].iloc[0].iloc[2] * 100
cats = [("Perfect optimiser\n(only owners whose advantage turns negative)", -st, -st * 0.5)] + [(f"s = {int(round(sv * 100))}%\nper point", cc.loc[sv, "bv_owners_2040_pct"], cc.loc[sv, "self_employed_2040_pct"]) for sv in (0.01, 0.02, 0.05, 0.10)]
fig, nl = canvas_pop("Fewer company owners, but fewer entrepreneurs only if leavers become employees",
                     "Change by 2040 versus today, central owner mix, half of leavers become employees and half sole traders. Company owners (BV) and all self-employed including sole traders.", wrap=66)
ax = fig.add_axes([0.07, 0.19, 0.86, 0.38])
style(ax)
w = 0.34
xs = np.arange(len(cats))
for j, (lab, c) in enumerate((("Company owners (BV)", BLUE), ("All entrepreneurs (company owners + sole traders)", ORANGE))):
    vals = [x[1 + j] for x in cats]
    ax.bar(xs + (j - 0.5) * (w + 0.02), vals, width=w, color=c, label=lab, zorder=3)
    for xx, v in zip(xs + (j - 0.5) * (w + 0.02), vals, strict=True):
        ax.text(xx, v - 0.8, f"{v:.1f}%", ha="center", va="top", fontsize=10, fontweight="semibold", color=INK)
    for (cl, *_), v in zip(cats, vals, strict=True):
        record("10_entrepreneur_counts", f"{lab} | {cl.replace(chr(10), ' ')}", "2040 change %", round(float(v), 2))
ax.axhline(0, color=INK2, lw=1)
ax.set_xticks(xs)
ax.set_xticklabels([x[0] for x in cats], fontsize=10, color=INK2)
ax.set_ylim(-34, 3)
ax.set_yticks([-30, -20, -10, 0])
ax.set_yticklabels(["-30%", "-20%", "-10%", "0"])
ax.legend(loc="lower left", frameon=False, fontsize=10, labelcolor=INK2)
fig.savefig(FIG / "10_entrepreneur_counts.png", dpi=200, facecolor=SURF)
plt.close(fig)

# ---- 11: tornado -----------------------------------------------------------------------------------------------------------------------
t = tor[tor.factor != "central mix"].copy()
t["lo"], t["hi"] = t[["low", "high"]].min(axis=1), t[["low", "high"]].max(axis=1)
t = t.assign(width=t.hi - t.lo).sort_values("width")
centre = float(tor[tor.factor == "central mix"].low.iloc[0])
fig, nl = canvas_pop("The strategy mix of owners moves the budget more than any proposal parameter",
                     f"Extra revenue 2028-29, all three measures, owners keeping their planning, changing one assumption at a time from an illustrative central mix (EUR {centre:,.0f}m). Bars span the two values tried.", wrap=66)
ax = fig.add_axes([0.35, 0.17, 0.58, 0.42])
style(ax, grid="x")
ax.spines["bottom"].set_visible(False)
nice = {"median revenue": "median revenue (60k vs 130k)", "revenue spread (sigma)": "revenue spread (0.3 vs 0.9)", "share with one client (S1)": "share with one client (10% vs 80%)", "size of S0 (N0)": "size of S0 (250k vs 450k)",
        "strategy mix": "payout strategy (all ordinary vs all optimisers)", "household": "household (single vs one earner + 2 children)", "owners re-plan": "owners re-plan after the measures",
        "measure parameters": "measure parameters (mild vs harsh)"}
for yy, (_, r) in enumerate(t.iterrows()):
    ax.plot([r.lo, r.hi], [yy, yy], color=BLUE, lw=8, solid_capstyle="round")
    ax.text(r.hi + 30, yy, f"{r.lo:,.0f} to {r.hi:,.0f}", fontsize=9.5, color=INK, va="center")
    record("11_tornado", r.factor, "low / high EUR m", f"{r.low:.0f} / {r.high:.0f}")
ax.axvline(centre, color=INK2, lw=1)
ax.axvline(450, color=MUTED, lw=1)
ax.text(450, len(t) - 0.4, "EUR 450m", color=MUTED, fontsize=9, ha="center", va="bottom")
ax.set_yticks(range(len(t)))
ax.set_yticklabels([nice.get(f, f) for f in t.factor], fontsize=9.8, color=INK)
ax.set_xlim(-1250, 1650)
ax.set_xticks([-1000, -500, 0, 500, 1000, 1500])
ax.set_xticklabels(["-1,000", "-500", "0", "500", "1,000", "EUR 1,500m"])
fig.savefig(FIG / "11_tornado.png", dpi=200, facecolor=SURF)
plt.close(fig)

pd.DataFrame(data_rows).to_csv(FIG / "figure_data.csv", index=False, lineterminator="\n")
print("figures written:", sorted(p.name for p in FIG.glob("*.png")))
