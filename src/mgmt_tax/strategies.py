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


def simulate_bv(Y: np.ndarray, years: list[int], path: PolicyPath, hh: Household, strat: BVStrategy, shape: tuple[int, ...], first_period: int = 1) -> Outcome:
    out = Outcome(f"BV:{strat.name}", shape)
    pol0 = path.at(years[0])
    K = pol0.v("asm.bv_paid_up_capital")
    F = np.zeros(shape)
    lr = ReserveAccount(shape)
    wp = np.full(shape, -K)
    T = len(years)
    for t, yr in enumerate(years):
        pol = path.at(yr)
        regime = strat.div_regime if pol.v("asm.vvprbis_eligible") else "ordinary"
        div_r = dividend_rate(regime, pol)
        eq_open = K + F + lr.total()
        r = pol.v("asm.real_return")
        i_co = r * eq_open
        admin = pol.v("asm.admin_cost_bv")
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
        corp = corporate_tax(tp, qual, pol)
        a = tp - corp  # post-tax profit of the year
        ssc = self_employed_contribution(pay, pol)
        pit = total_income_tax(pay - ssc, pol)
        net_pay = pay - ssc - pit

        wht = np.zeros(shape)
        liqtax = np.zeros(shape)
        levy = np.zeros(shape)
        net_div = np.zeros(shape)
        cap_return = np.zeros(shape)

        # 1) liquidity gap financed by a dividend from the free pool
        deficit = np.clip(need - net_pay, 0.0, None)
        free_pool = F + a
        gross_draw = np.minimum(deficit / (1.0 - div_r), np.clip(free_pool, 0.0, None))
        wht += div_r * gross_draw
        net_div += (1.0 - div_r) * gross_draw
        F_ = free_pool - gross_draw
        out.liquidity_gap += np.clip(deficit - (1.0 - div_r) * gross_draw, 0.0, None)

        # 2) what happens to the rest of the free pool
        if strat.vehicle == "distribute":
            g = np.clip(F_, 0.0, None)
            wht += div_r * g
            net_div += (1.0 - div_r) * g
            F_ = F_ - g
        elif strat.vehicle == "liquidation_reserve":
            lv, credited = lr_allocate(F_, pol)
            levy += lv
            lr.add(yr, credited)
            F_ = F_ - np.clip(F_, 0.0, None)
        elif strat.vehicle != "free_reserve":
            raise ValueError(strat.vehicle)

        # 3) interim lump sum
        if strat.lump_year is not None and (t + 1) == strat.lump_year:
            g = np.clip(F_, 0.0, None)
            wht += div_r * g
            net_div += (1.0 - div_r) * g
            F_ = F_ - g
            pool = lr.take_distributable(yr, pol)
            w = lr_dividend_withholding(pool, pol)
            wht += w
            net_div += pool - w

        # 4) final exit (liquidation of the company at the end of the horizon)
        if t == T - 1:
            out.equity_pre_exit = K + F_ + lr.total()
            if strat.exit == "dividend":
                g = np.clip(F_, 0.0, None)
                wht += div_r * g
                net_div += (1.0 - div_r) * g
                F_ = F_ - g
                pool = lr.take_distributable(yr, pol)
                w = lr_dividend_withholding(pool, pol)
                wht += w
                net_div += pool - w
                rest = lr.take_all()
                lt = lr_liquidation_tax(rest, strat.anti_abuse, pol)
                liqtax += lt
                net_div += rest - lt
            elif strat.exit == "liquidation":
                g = np.clip(F_, 0.0, None)
                lt = ordinary_liquidation_tax(g, pol)
                liqtax += lt
                net_div += g - lt
                F_ = F_ - g
                rest = lr.take_all()
                lt2 = lr_liquidation_tax(rest, strat.anti_abuse, pol)
                liqtax += lt2
                net_div += rest - lt2
            else:
                raise ValueError(strat.exit)
            net_div += F_  # a negative free reserve (loss) is absorbed by the owner
            F_ = np.zeros(shape)
            cap_return = np.full(shape, K)
            K_close = 0.0
        else:
            K_close = K

        eq_close = K_close + F_ + lr.total()
        gi, mov = private_interest(wp, pol)
        cash_in = net_pay + net_div + cap_return
        wp_new = wp + gi - mov + cash_in - need

        taxes_t = {"pit": pit, "ssc_self": ssc, "corp_tax": corp, "company_contribution": np.full(shape, cc), "lr_levy": levy, "dividend_wht": wht,
                   "liquidation_tax": liqtax, "movable_income_tax": mov}
        for k, v in taxes_t.items():
            out.taxes[k] = out.taxes[k] + v
        rhs = admin + sum(taxes_t.values()) + need + (wp_new - wp) + (eq_close - eq_open)
        out.ledger_residual = max(out.ledger_residual, float(np.max(np.abs(Y[t] + i_co + gi - rhs))))
        out.admin += admin
        out.pension_base += pay - ssc
        out.owner_pay += pay
        out.reduced_rate_years += (qual & (tp > 0)).astype(float)
        wp = wp_new
        F = F_
        K = K_close
        out.private_path.append(wp.copy())
        out.equity_path.append(eq_close.copy() if t < T - 1 else out.equity_pre_exit.copy())
    out.wealth_end = wp
    return out
