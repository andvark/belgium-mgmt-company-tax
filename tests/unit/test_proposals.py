"""Hand-computed checks of the three draft-proposal mechanics (scenario assumptions, not the drafts themselves).
Setup of every case: one year (or two), fifth taxable period, client pays 155,409.30, admin 4,000, company contribution 409.30,
director pay 51,000 -> taxable profit 100,000 -> corporate tax 20,000 -> post-tax profit 80,000 (baseline)."""

import numpy as np
import pytest

from mgmt_tax.arrangements import Household
from mgmt_tax.policy import PathChange, PolicyPath
from mgmt_tax.strategies import BVStrategy, simulate_bv

pytestmark = pytest.mark.unconfirmed
SINGLE = Household("single", 1, 0, False)
Y = 155409.30


def run(pol, strat, changes=(), years=(2026,), hire=0.0, share=None, burn=0):
    path = PolicyPath(pol, tuple(changes))
    yv = np.array([[Y]] * len(years))
    return simulate_bv(yv, list(years), path, SINGLE, strat, (1,), first_period=5, hire_cost=hire, client_share=share, burn=burn)


T = lambda o, k: o.taxes[k].ravel()[0]  # noqa: E731
THR_DIST = BVStrategy("d", "threshold", "distribute", "vvprbis", None, "liquidation")
THR_LR = BVStrategy("l", "threshold", "liquidation_reserve", "vvprbis", None, "liquidation")
THR_RET = BVStrategy("r", "threshold", "free_reserve", "vvprbis", None, "dividend")


# ------------------------------------------------------------------ P1
def test_p1_withdraws_reduced_rate_without_employee(pol):
    p1 = (PathChange(2026, {"p1.reduced_rate_requires_employee": True}, "P1"),)
    assert T(run(pol, THR_DIST), "corp_tax") == pytest.approx(20000.0)                 # 0.20 x 100,000
    assert T(run(pol, THR_DIST, p1), "corp_tax") == pytest.approx(25000.0)             # 0.25 x 100,000


def test_p1_hire_keeps_reduced_rate_at_a_cost(pol):
    # hire at employer cost 10,000: profit before pay 155,409.30 - 14,000 - 409.30 = 141,000 ; pay 51,000 ; taxable 90,000 ; 0.20 x 90,000 = 18,000
    p1 = (PathChange(2026, {"p1.reduced_rate_requires_employee": True}, "P1"),)
    o = run(pol, THR_DIST, p1, hire=10000.0)
    assert T(o, "corp_tax") == pytest.approx(18000.0)
    assert o.admin.ravel()[0] == pytest.approx(14000.0)
    assert o.ledger_residual < 1e-6


def test_p1_start_year(pol):
    # P1 from 2027: 2026 keeps 20% (20,000), 2027 pays 25,000
    p1 = (PathChange(2027, {"p1.reduced_rate_requires_employee": True}, "P1"),)
    assert T(run(pol, THR_DIST, p1, years=(2026, 2027)), "corp_tax") == pytest.approx(45000.0)


# ------------------------------------------------------------------ P2
@pytest.mark.parametrize("m,wht", [
    # payroll 51,000 / 2 = 25,500 at 18% (4,590) + 54,500 at 30% (16,350) = 20,940 ; baseline 0.18 x 80,000 = 14,400
    (2, 20940.0),
    # 51,000 / 3 = 17,000 at 18% (3,060) + 63,000 at 30% (18,900) = 21,960
    (3, 21960.0),
])
def test_p2_caps_reduced_dividends(pol, m, wht):
    p2 = (PathChange(2026, {"p2.payroll_multiple": m}, f"P2x{m}"),)
    assert T(run(pol, THR_DIST), "dividend_wht") == pytest.approx(14400.0)
    assert T(run(pol, THR_DIST, p2), "dividend_wht") == pytest.approx(wht)


def test_p2_caps_liquidation_reserve_allocation(pol):
    # m = 2: only 25,500 can be used for the reserve (levy 25,500 - 25,500 / 1.10 = 2,318.18); 54,500 stays in the free reserve and is liquidated at 30% = 16,350
    p2 = (PathChange(2026, {"p2.payroll_multiple": 2}, "P2x2"),)
    o = run(pol, THR_LR, p2)
    assert T(o, "lr_levy") == pytest.approx(2318.1818, abs=1e-3)
    assert T(o, "liquidation_tax") == pytest.approx(16350.0)


def test_p2_higher_pay_raises_the_cap(pol):
    # pay 80,000 -> cap 40,000 (m = 2).  Profit before pay 151,000 ; taxable 71,000 ; reduced rate kept (pay >= 51,000) ; corporate tax 14,200 ; post-tax 56,800
    # dividends: 40,000 at 18% = 7,200 + 16,800 at 30% = 5,040 -> 12,240
    p2 = (PathChange(2026, {"p2.payroll_multiple": 2}, "P2x2"),)
    s = BVStrategy("f", "fixed", "distribute", "vvprbis", None, "liquidation", pay_amount=80000.0)
    o = run(pol, s, p2)
    assert T(o, "corp_tax") == pytest.approx(14200.0)
    assert T(o, "dividend_wht") == pytest.approx(12240.0)


def test_p2_hire_adds_to_payroll(pol):
    # hire cost 10,000 -> wage 8,000 ; payroll 59,000 ; cap (m = 2) 29,500.  Post-tax profit 72,000 (see P1 hire case, taxable 90,000 x 0.8)
    # dividends: 29,500 x 0.18 (5,310) + 42,500 x 0.30 (12,750) = 18,060
    p2 = (PathChange(2026, {"p2.payroll_multiple": 2}, "P2x2"),)
    o = run(pol, THR_DIST, p2, hire=10000.0)
    assert T(o, "dividend_wht") == pytest.approx(18060.0)


# ------------------------------------------------------------------ P3
P3 = (PathChange(2026, {"p3.active": True, "p3.client_threshold": 0.9, "p3.lookback_years": 3}, "P3"),)


def test_p3_binding_year_loses_reduced_regimes(pol):
    one = np.ones((3 + 1, 1))
    assert T(run(pol, THR_DIST, P3, share=one, burn=3), "dividend_wht") == pytest.approx(24000.0)   # 30% x 80,000 instead of 18%
    assert T(run(pol, THR_LR, P3, share=one, burn=3), "lr_levy") == 0.0                              # cannot enter the liquidation reserve
    assert T(run(pol, THR_LR, P3, share=one, burn=3), "liquidation_tax") == pytest.approx(24000.0)   # liquidated at 30% instead of 10% levy


def test_p3_lookback_window(pol):
    # window = the last 3 years including the current one
    dip = np.array([[1.0], [1.0], [0.8], [1.0]])           # 0.8 inside the window -> not binding
    assert T(run(pol, THR_DIST, P3, share=dip, burn=3), "dividend_wht") == pytest.approx(14400.0)
    old = np.array([[0.8], [1.0], [1.0], [1.0]])           # 0.8 just outside the 3-year window -> binding
    assert T(run(pol, THR_DIST, P3, share=old, burn=3), "dividend_wht") == pytest.approx(24000.0)
    p5 = (PathChange(2026, {"p3.active": True, "p3.client_threshold": 0.9, "p3.lookback_years": 5}, "P3-5y"),)
    long_old = np.array([[0.8], [1.0], [1.0], [1.0], [1.0], [1.0]])
    assert T(run(pol, THR_DIST, p5, share=long_old[:6], burn=5), "dividend_wht") == pytest.approx(24000.0)  # window = last 5 rows


def test_p3_threshold(pol):
    s85 = np.full((4, 1), 0.85)
    assert T(run(pol, THR_DIST, P3, share=s85, burn=3), "dividend_wht") == pytest.approx(14400.0)   # 85% < 90%: not touched
    p80 = (PathChange(2026, {"p3.active": True, "p3.client_threshold": 0.8, "p3.lookback_years": 3}, "P3-80"),)
    assert T(run(pol, THR_DIST, p80, share=s85, burn=3), "dividend_wht") == pytest.approx(24000.0)  # 85% >= 80%: touched


def test_p3_only_new_amounts_are_affected(pol):
    # P3 from 2027, two years, post-tax profit 80,000 each, retain and take a VVPRbis dividend at the end:
    # the 2026 amount keeps 18% (14,400), the 2027 amount is ordinary 30% (24,000)
    p3 = (PathChange(2027, {"p3.active": True, "p3.client_threshold": 0.9, "p3.lookback_years": 3}, "P3"),)
    one = np.ones((3 + 2, 1))
    o = run(pol, THR_RET, p3, years=(2026, 2027), share=one, burn=3)
    assert T(o, "dividend_wht") == pytest.approx(38400.0)
    # liquidation reserve: 2026 allocation 80,000 (levy 80,000 - 80,000 / 1.10 = 7,272.73) ; 2027 amount stays ordinary -> liquidated at 30% = 24,000
    o2 = run(pol, THR_LR, p3, years=(2026, 2027), share=one, burn=3)
    assert T(o2, "lr_levy") == pytest.approx(7272.7273, abs=1e-3)
    assert T(o2, "liquidation_tax") == pytest.approx(24000.0)
    assert o2.ledger_residual < 1e-6


def test_hire_starts_only_when_the_policy_starts(pol):
    # P1 from 2027, hire at 10,000: no cost in 2026, 10,000 in 2027 (admin 4,000 + 4,000 + 10,000 = 18,000 over two years)
    p1 = (PathChange(2027, {"p1.reduced_rate_requires_employee": True}, "P1"),)
    path = PolicyPath(pol, p1)
    o = simulate_bv(np.array([[Y], [Y]]), [2026, 2027], path, SINGLE, THR_DIST, (1,), first_period=5, hire_cost=10000.0, hire_from=2027)
    assert o.admin.ravel()[0] == pytest.approx(18000.0)
    # 2026 corporate tax 20,000 (no hire, rule not yet in force); 2027 with hire: taxable 90,000 -> 18,000
    assert T(o, "corp_tax") == pytest.approx(38000.0)
