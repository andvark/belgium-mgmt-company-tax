"""One-person BV: owner strategies with a vintaged reserve account, a liquidity constraint and an exit route.

A strategy = (pay rule, what happens to post-tax profit, dividend regime, optional interim lump-sum year, final exit).
  pay_rule   'threshold' pay min(51,000, profit before pay)  - keeps the reduced corporate rate after the exempt periods
             'liquidity' the smallest pay whose net-of-contributions-and-tax covers the household need (the 'minimum salary')
             'fixed'     a fixed amount per year (pay_amount), capped at profit before pay
             'full'      all profit paid as director remuneration (the BV as a shell)
  vehicle    'distribute' dividend all post-tax profit every year; 'free_reserve' retain it; 'liquidation_reserve' allocate it
             to the liquidation reserve (levy at creation, 3-year lock for dividends)
  div_regime 'ordinary' (30%) or 'vvprbis' (18%) for dividends out of the free reserve (vvprbis only if asm.vvprbis_eligible)
  lump_year  1-based year count at whose end the free reserve and the reserve vintages past the lock are paid out as dividends
  exit       at the last year: 'dividend' (free reserve as dividend, eligible vintages as dividend, the rest liquidated)
             or 'liquidation' (free reserve at the ordinary liquidation rate above paid-up capital, reserve at the liquidation rate)
Liquidity: if director pay does not cover the household need, the gap is financed by a dividend out of the free pool
(current post-tax profit + free reserve); any remaining gap reduces private wealth (recorded as liquidity_gap).

Draft proposals (all OFF unless the policy path switches them on; see configs/proposals.yaml):
  P1  the reduced corporate rate also requires a paid employee (hire_cost > 0 = a hire at that annual employer cost);
  P2  reduced-regime dividends and liquidation-reserve allocations are capped each year at payroll / m, the rest is taxed as ordinary;
  P3  when the owner's client share stays >= threshold throughout the lookback, the year's post-tax profit goes to an ORDINARY
      reserve (taxed 30% as dividend or liquidation) and cannot enter the liquidation reserve; earlier amounts keep their regime.
The free reserve is therefore two pools: ``F_red`` (amounts that keep the reduced regimes) and ``F_ord`` (amounts that do not).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from mgmt_tax.arrangements import Household, Outcome, private_interest
from mgmt_tax.policy import PolicyPath
from mgmt_tax.reserves import ReserveAccount
from mgmt_tax.tax.contributions import self_employed_contribution
from mgmt_tax.tax.corporate import corporate_tax, qualifies_for_reduced_rate
from mgmt_tax.tax.distributions import dividend_rate, lr_allocate, lr_dividend_withholding, lr_liquidation_tax, ordinary_liquidation_tax
from mgmt_tax.tax.pit import total_income_tax

BIG = 1e18


@dataclass(frozen=True)
class BVStrategy:
    name: str
    pay_rule: str
    vehicle: str
    div_regime: str = "vvprbis"
    lump_year: int | None = None
    exit: str = "liquidation"
    anti_abuse: bool = False
    pay_amount: float | None = None  # for pay_rule 'fixed': director pay in EUR per year (capped at profit before pay)


def net_of_pay(pay: np.ndarray, pol) -> np.ndarray:
    ssc = self_employed_contribution(pay, pol)
    return pay - ssc - total_income_tax(pay - ssc, pol)


def solve_pay_for_net(target: float, pay_max: np.ndarray, pol, iters: int = 50) -> np.ndarray:
    """Smallest pay in [0, pay_max] whose net (after contributions and income tax) reaches ``target`` (else pay_max). Net is increasing in pay."""
    hi = np.clip(pay_max, 0.0, None)
    lo = np.zeros_like(hi)
    reach = net_of_pay(hi, pol) >= target
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        ok = net_of_pay(mid, pol) >= target
        hi = np.where(ok, mid, hi)
        lo = np.where(ok, lo, mid)
    return np.where(reach, hi, np.clip(pay_max, 0.0, None))


def _pos(x):
    return np.clip(x, 0.0, None)


def _distribute(g, f_red, f_ord, cap, r_red, r_ord):
    """Pay a gross dividend g (capped at the positive pools), reduced-regime pool first.  The part of the reduced pool within ``cap`` bears r_red,
    everything else r_ord.  Returns (gross paid, withholding, f_red', f_ord', cap')."""
    pr, po = _pos(f_red), _pos(f_ord)
    g = np.minimum(g, pr + po)
    from_red = np.minimum(g, pr)
    from_ord = g - from_red
    red_part = np.minimum(from_red, cap)
    wht = r_red * red_part + r_ord * (g - red_part)
    return g, wht, f_red - from_red, f_ord - from_ord, cap - red_part


def _gross_for_net(d, f_red, f_ord, cap, r_red, r_ord):
    """Gross dividend needed to deliver a net amount d, reduced pool (within the cap) first."""
    pr, po = _pos(f_red), _pos(f_ord)
    ga = np.minimum(pr, cap)
    na = (1.0 - r_red) * ga
    g = np.where(d <= na, d / (1.0 - r_red), ga + (d - na) / (1.0 - r_ord))
    return np.minimum(g, pr + po)


def simulate_bv(Y: np.ndarray, years: list[int], path: PolicyPath, hh: Household, strat: BVStrategy, shape: tuple[int, ...], first_period: int = 1,
                hire_cost: float = 0.0, client_share: np.ndarray | None = None, burn: int = 0, hire_from: int = 0) -> Outcome:
    """``client_share``: array (burn + T, replicates) of the owner's largest-client share, used only if proposal 3 is on; its first ``burn`` rows are history.
    ``hire_cost``: annual employer cost of a hired employee, paid from calendar year ``hire_from`` on (0 = no employee)."""
    out = Outcome(f"BV:{strat.name}", shape)
    pol0 = path.at(years[0])
    K = pol0.v("asm.bv_paid_up_capital")
    F_red = np.zeros(shape)
    F_ord = np.zeros(shape)
    lr = ReserveAccount(shape)
    wp = np.full(shape, -K)
    T = len(years)
    for t, yr in enumerate(years):
        pol = path.at(yr)
        has_emp = hire_cost > 0 and yr >= hire_from
        regime = strat.div_regime if pol.v("asm.vvprbis_eligible") else "ordinary"
        r_red = dividend_rate(regime, pol)
        r_ord = dividend_rate("ordinary", pol)
        eq_open = K + F_red + F_ord + lr.total()
        r = pol.v("asm.real_return")
        i_co = r * eq_open
        admin = pol.v("asm.admin_cost_bv") + (hire_cost if has_emp else 0.0)  # a hire at annual employer cost c is treated as a cost leaving the system
        hire_wage = hire_cost / (1.0 + pol.v("ssc.employer_rate")) if has_emp else 0.0
        cc = pol.v("corp.annual_company_contribution")
        pp = Y[t] + i_co - admin - cc  # taxable profit before the director's pay
        pp_pos = np.clip(pp, 0.0, None)
        need = hh.owner_need(pol)
        if strat.pay_rule == "threshold":
            pay = np.minimum(pol.v("corp.director_min_pay"), pp_pos)
        elif strat.pay_rule == "full":
            pay = pp_pos
        elif strat.pay_rule == "fixed":
            pay = np.minimum(float(strat.pay_amount), pp_pos)
        elif strat.pay_rule == "liquidity":
            pay = solve_pay_for_net(need, pp_pos, pol)
        else:
            raise ValueError(strat.pay_rule)
        tp = pp - pay
        qual = qualifies_for_reduced_rate(pay, pp, first_period + t, pol)
        if pol.v("p1.reduced_rate_requires_employee") and not has_emp:
            qual = np.zeros_like(qual, dtype=bool)
        corp = corporate_tax(tp, qual, pol)
        a = tp - corp  # post-tax profit of the year
        ssc = self_employed_contribution(pay, pol)
        pit = total_income_tax(pay - ssc, pol)
        net_pay = pay - ssc - pit

        # proposal 2: yearly capacity of the reduced regimes; proposal 3: does this year's profit lose them?
        m = pol.v("p2.payroll_multiple")
        cap = (pay + hire_wage) / float(m) if m else np.full(shape, BIG)
        if regime == "ordinary":
            cap = np.full(shape, BIG)  # no reduced rate to ration
        if pol.v("p3.active"):
            L = int(pol.v("p3.lookback_years"))
            thr = pol.v("p3.client_threshold")
            hi = burn + t + 1
            window = client_share[hi - L:hi]
            red_ok = ~(window.min(axis=0) >= thr - 1e-12)
        else:
            red_ok = np.ones(shape[-1], dtype=bool)
        to_red = np.where(red_ok | (a < 0), a, 0.0)
        F_red = F_red + to_red
        F_ord = F_ord + (a - to_red)

        wht = np.zeros(shape)
        liqtax = np.zeros(shape)
        levy = np.zeros(shape)
        net_div = np.zeros(shape)

        # 1) liquidity gap financed by a dividend from the free pools
        deficit = np.clip(need - net_pay, 0.0, None)
        g = _gross_for_net(deficit, F_red, F_ord, cap, r_red, r_ord)
        g, w, F_red, F_ord, cap = _distribute(g, F_red, F_ord, cap, r_red, r_ord)
        wht += w
        net_div += g - w
        out.liquidity_gap += np.clip(deficit - (g - w), 0.0, None)

        # 2) what happens to the rest of the free pools
        if strat.vehicle == "distribute":
            g, w, F_red, F_ord, cap = _distribute(_pos(F_red) + _pos(F_ord), F_red, F_ord, cap, r_red, r_ord)
            wht += w
            net_div += g - w
        elif strat.vehicle == "liquidation_reserve":
            x = np.minimum(_pos(F_red), cap)  # only amounts that keep the reduced regimes, within the yearly capacity
            lv, credited = lr_allocate(x, pol)
            levy += lv
            lr.add(yr, credited)
            F_red = F_red - x
            cap = cap - x
        elif strat.vehicle != "free_reserve":
            raise ValueError(strat.vehicle)

        # 3) interim lump sum
        if strat.lump_year is not None and (t + 1) == strat.lump_year:
            g, w, F_red, F_ord, cap = _distribute(_pos(F_red) + _pos(F_ord), F_red, F_ord, cap, r_red, r_ord)
            wht += w
            net_div += g - w
            pool = lr.take_up_to(yr, pol, cap)
            cap = cap - pool
            w = lr_dividend_withholding(pool, pol)
            wht += w
            net_div += pool - w

        # 4) final exit (liquidation of the company at the end of the horizon)
        cap_return = np.zeros(shape)
        if t == T - 1:
            out.equity_pre_exit = K + F_red + F_ord + lr.total()
            if strat.exit == "dividend":
                g, w, F_red, F_ord, cap = _distribute(_pos(F_red) + _pos(F_ord), F_red, F_ord, cap, r_red, r_ord)
                wht += w
                net_div += g - w
                pool = lr.take_up_to(yr, pol, cap)
                w = lr_dividend_withholding(pool, pol)
                wht += w
                net_div += pool - w
            elif strat.exit == "liquidation":
                gp = _pos(F_red) + _pos(F_ord)
                lt = ordinary_liquidation_tax(gp, pol)
                liqtax += lt
                net_div += gp - lt
                F_red = F_red - _pos(F_red)
                F_ord = F_ord - _pos(F_ord)
            else:
                raise ValueError(strat.exit)
            rest = lr.take_all()
            lt2 = lr_liquidation_tax(rest, strat.anti_abuse, pol)
            liqtax += lt2
            net_div += rest - lt2
            net_div += F_red + F_ord  # negative balances (losses) are absorbed by the owner
            F_red = np.zeros(shape)
            F_ord = np.zeros(shape)
            cap_return = np.full(shape, K)
            K_close = 0.0
        else:
            K_close = K

        eq_close = K_close + F_red + F_ord + lr.total()
        gi, mov = private_interest(wp, pol)
        cash_in = net_pay + net_div + cap_return
        wp_new = wp + gi - mov + cash_in - need

        taxes_t = {"pit": pit, "ssc_self": ssc, "corp_tax": corp, "company_contribution": np.full(shape, cc), "lr_levy": levy, "dividend_wht": wht,
                   "liquidation_tax": liqtax, "movable_income_tax": mov}
        for k, v in taxes_t.items():
            out.taxes[k] = out.taxes[k] + v
        rhs = admin + sum(taxes_t.values()) + need + (wp_new - wp) + (eq_close - eq_open)
        out.ledger_residual = max(out.ledger_residual, float(np.max(np.abs(Y[t] + i_co + gi - rhs))))
        out.tax_year_total.append(sum(taxes_t.values()))
        out.tax_year_ssc.append(ssc)
        out.admin += admin
        out.pension_base += pay - ssc
        out.owner_pay += pay
        out.reduced_rate_years += (qual & (tp > 0)).astype(float)
        wp = wp_new
        K = K_close
        out.private_path.append(wp.copy())
        out.equity_path.append(eq_close.copy() if t < T - 1 else out.equity_pre_exit.copy())
    out.wealth_end = wp
    return out
