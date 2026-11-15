"""Hand-computed worked examples.  Expected values were derived by explicit arithmetic (written next to each case), NOT by
running the engine.  They check the engine against the SUPPLIED rules; they do not confirm the supplied rules themselves
(no published official worked example was available), hence the `unconfirmed` marker."""

import numpy as np
import pytest

from mgmt_tax.arrangements import Household, simulate_employee, simulate_sole_trader
from mgmt_tax.policy import PathChange, PolicyPath
from mgmt_tax.reserves import ReserveAccount
from mgmt_tax.strategies import BVStrategy, simulate_bv
from mgmt_tax.tax.contributions import employee_ssc, employer_cost, self_employed_contribution, wage_from_employer_cost
from mgmt_tax.tax.corporate import corporate_tax, qualifies_for_reduced_rate
from mgmt_tax.tax.distributions import lr_allocate, lr_dividend_withholding, lr_liquidation_tax, ordinary_liquidation_tax
from mgmt_tax.tax.pit import bracket_tax, income_tax, total_income_tax

pytestmark = pytest.mark.unconfirmed
A = lambda x: np.array([x], dtype=float)  # noqa: E731


# ---------------------------------------------------------------- personal income tax
@pytest.mark.parametrize("taxable,state,total", [
    # 10,000: 25% = 2,500 < reduction 2,887.50 -> floored at 0
    (10000, 0.0, 0.0),
    # 11,550: 25% x 11,550 = 2,887.50 - 2,887.50 = 0
    (11550, 0.0, 0.0),
    # 16,720: 0.25 x 16,720 = 4,180.00 ; - 2,887.50 = 1,292.50 ; x 1.072 = 1,385.56
    (16720, 1292.50, 1385.56),
    # 40,000: 4,180 + 0.40 x 12,790 (=5,116) + 0.45 x 10,490 (=4,720.50) = 14,016.50 ; - 2,887.50 = 11,129.00 ; x 1.072 = 11,930.288
    (40000, 11129.00, 11930.288),
    # 60,000: 4,180 + 5,116 + 0.45 x 21,560 (=9,702) + 0.50 x 8,930 (=4,465) = 23,463 ; - 2,887.50 = 20,575.50 ; x 1.072 = 22,056.936
    (60000, 20575.50, 22056.936),
])
def test_pit_examples(pol, taxable, state, total):
    s, m = income_tax(A(taxable), pol)
    assert s[0] == pytest.approx(state, abs=1e-6)
    assert (s + m)[0] == pytest.approx(total, abs=1e-6)


def test_allowance_is_a_reduction_not_a_deduction(pol):
    # belgium_abm deducts 11,550 from income first: taxable 28,450 -> 4,180 + 0.40 x 11,730 = 8,872.00.
    # Supplied rule: 11,129.00 on 40,000.  The two differ by 2,257.
    assert income_tax(A(40000), pol)[0][0] == pytest.approx(11129.0)
    assert 8872.0 != pytest.approx(11129.0)


# ---------------------------------------------------------------- contributions
def test_employee_examples(pol):
    # employer cost 60,000 -> gross wage 60,000 / 1.25 = 48,000 ; employee 13.07% = 6,273.60 ; employer contributions 12,000
    w = wage_from_employer_cost(A(60000), pol)
    assert w[0] == pytest.approx(48000.0)
    assert employee_ssc(w, pol)[0] == pytest.approx(6273.60)
    assert employer_cost(w, pol)[0] == pytest.approx(60000.0)


@pytest.mark.parametrize("net,contrib", [
    # tier 1: 20.5% x 50,000 = 10,250 ; gross income B = 60,250
    (50000.0, 10250.0),
    # tier 2: 0.205 x 75,024.54 (=15,380.0307) + 0.1416 x 10,000 (=1,416) = 16,796.0307 ; B = 85,024.54 + 16,796.0307 = 101,820.5707
    (85024.54, 16796.0307),
    # beyond 2nd ceiling: 15,380.0307 + 0.1416 x 35,537.88 (=5,032.1638) = 20,412.1945 ; nothing above (open default) ; B = 140,412.1945
    (120000.0, 20412.194508),
])
def test_self_employed_contribution_inverse(pol, net, contrib):
    gross = net + contrib
    assert self_employed_contribution(A(gross), pol)[0] == pytest.approx(contrib, abs=1e-3)


def test_self_employed_minimum(pol):
    # B = 10,000: 0.205/1.205 x 10,000 = 1,701.24 < minimum 4 x 890.42 = 3,561.68
    assert self_employed_contribution(A(10000), pol)[0] == pytest.approx(3561.68)


# ---------------------------------------------------------------- corporate tax
def test_corporate_two_rates(pol):
    assert corporate_tax(A(130000), np.array([True]), pol)[0] == pytest.approx(27500.0)   # 0.20 x 100,000 + 0.25 x 30,000
    assert corporate_tax(A(130000), np.array([False]), pol)[0] == pytest.approx(32500.0)  # 0.25 x 130,000
    assert corporate_tax(A(80000), np.array([True]), pol)[0] == pytest.approx(16000.0)    # 0.20 x 80,000


def test_pay_condition(pol):
    # fifth period: pay >= 51,000, or pay >= taxable income AFTER deducting the pay (= profit before pay - pay)
    assert qualifies_for_reduced_rate(A(51000), A(200000), 5, pol)[0]
    assert not qualifies_for_reduced_rate(A(50999.99), A(200000), 5, pol)[0]   # taxable 149,000 after pay: pay does not cover it
    # the checklist's example: 60,000 before pay and pay 30,000 leaves 30,000 taxable -> qualifies; 29,999 leaves 30,001 -> does not
    assert qualifies_for_reduced_rate(A(30000), A(60000), 5, pol)[0]
    assert not qualifies_for_reduced_rate(A(29999), A(60000), 5, pol)[0]
    # 100,000 before pay: pay 50,000 leaves 50,000 -> qualifies (cheapest qualifying pay = profit / 2 below 102,000)
    assert qualifies_for_reduced_rate(A(50000), A(100000), 5, pol)[0] and not qualifies_for_reduced_rate(A(49999), A(100000), 5, pol)[0]
    assert qualifies_for_reduced_rate(A(39999), A(40000), 5, pol)[0]       # taxable 1 after pay: covered
    assert qualifies_for_reduced_rate(A(0), A(200000), 4, pol)[0]          # first four periods exempt (confirmed)


# ---------------------------------------------------------------- distributions (on 100,000 of post-tax profit)
def test_distribution_routes(pol):
    x = A(100000)
    assert 0.30 * 100000 == 30000                                          # ordinary dividend
    assert 0.18 * 100000 == 18000                                          # VVPRbis dividend
    # liquidation reserve (confirmed): credit 100,000 / 1.10 = 90,909.09 ; levy 9,090.91 ; withholding 9.8% x 90,909.09 = 8,909.09 ; total 18,000 = 18.00%
    levy, pool = lr_allocate(x, pol)
    assert levy[0] == pytest.approx(9090.9091, abs=1e-3) and pool[0] == pytest.approx(90909.0909, abs=1e-3)
    assert lr_dividend_withholding(pool, pol)[0] == pytest.approx(8909.0909, abs=1e-3)
    assert levy[0] + lr_dividend_withholding(pool, pol)[0] == pytest.approx(18000.0, abs=1e-6)
    assert lr_liquidation_tax(pool, False, pol)[0] == 0.0                  # liquidation: levy only, 9.09%
    assert lr_liquidation_tax(pool, True, pol)[0] == pytest.approx(27272.7273, abs=1e-3)  # anti-abuse default 30% x 90,909.09
    assert ordinary_liquidation_tax(x, pol)[0] == pytest.approx(30000.0)   # 30% on surplus above paid-up capital


def test_vintaged_lock(pol):
    acct = ReserveAccount((1,))
    acct.add(2026, A(100.0))
    acct.add(2027, A(50.0))
    # confirmed: three full years from the end of the constitution year; a 2026 reserve is first payable in 2030 (lock 3 + 1 calendar year)
    assert acct.distributable(2029, pol)[0] == 0.0       # locked
    assert acct.distributable(2030, pol)[0] == 100.0     # 2026 vintage
    assert acct.distributable(2031, pol)[0] == 150.0
    assert acct.take_distributable(2030, pol)[0] == 100.0
    assert acct.total()[0] == 50.0                       # younger vintage untouched
    pol2 = pol.with_overrides({"lr.lock_extra_calendar_years": 0}, "lock+0")   # earlier reading, kept as a sensitivity
    acct = ReserveAccount((1,))
    acct.add(2026, A(100.0))
    assert acct.distributable(2029, pol2)[0] == 100.0 and acct.distributable(2028, pol2)[0] == 0.0


# ---------------------------------------------------------------- whole arrangements, one year, no shocks
SINGLE = Household("single", 1, 0, False)  # need 24,000


def test_employee_one_year(path):
    # W 48,000 ; employee 6,273.60 ; lump sum min(30% x 41,726.40 = 12,517.92 ; cap 6,070) = 6,070 ; taxable 35,656.40 ;
    # tax 4,180 + 5,116 + 0.45 x 6,146.40 (=2,765.88) = 12,061.88 ; -2,887.50 = 9,174.38 ; x 1.072 = 9,834.93536 ;
    # net 48,000 - 6,273.60 - 9,834.93536 = 31,891.46464 ; saves 7,891.46464
    o = simulate_employee(np.array([[60000.0]]), [2026], path, SINGLE, (1,))
    assert o.taxes["pit"].ravel()[0] == pytest.approx(9834.93536, abs=1e-4)
    assert o.wealth_end.ravel()[0] == pytest.approx(7891.46464, abs=1e-4)
    assert o.total_tax().ravel()[0] == pytest.approx(28108.53536, abs=1e-4)   # 12,000 + 6,273.60 + 9,834.93536


def test_sole_trader_one_year(path):
    # profit 80,000 - 1,000 = 79,000 ; N = 79,000/1.205 = 65,560.166 ; contribution 13,439.834 ;
    # tax: 4,180 + 5,116 + 9,702 + 0.50 x 14,490.166 (=7,245.083) = 26,243.083 ; -2,887.50 = 23,355.583 ; x 1.072 = 25,037.185
    # net 79,000 - 13,439.834 - 25,037.185 = 40,522.981 ; saves 16,522.981
    o = simulate_sole_trader(np.array([[80000.0]]), [2026], path, SINGLE, (1,))
    assert o.taxes["ssc_self"].ravel()[0] == pytest.approx(13439.834, abs=1e-3)
    assert o.taxes["pit"].ravel()[0] == pytest.approx(25037.185, abs=1e-3)
    assert o.wealth_end.ravel()[0] == pytest.approx(16522.981, abs=1e-3)


# BV, fifth period, one year: client pays 155,409.30 ; admin 4,000 ; company contribution 409.30 -> profit before pay 151,000
# pay 51,000 -> taxable 100,000 -> corporate tax 20,000 -> post-tax profit 80,000
# director: N = 51,000/1.205 = 42,323.651 ; contribution 8,676.349 ; PIT (4,180 + 5,116 + 0.45 x 12,813.651 = 5,766.143 -> 15,062.143
#   -2,887.50 = 12,174.643 ; x 1.072) = 13,051.217 ; net pay 29,272.434 ; need 24,000 -> no deficit
Y_BV = 155409.30


def _bv(path, strat):
    return simulate_bv(np.array([[Y_BV]]), [2026], path, SINGLE, strat, (1,), first_period=5)


def test_bv_retain_then_vvprbis_dividend(path):
    # dividend 80,000 x 18% = 14,400 ; wealth = -12,000 + 29,272.434 + 65,600 + 12,000 (capital back) - 24,000 = 70,872.434
    o = _bv(path, BVStrategy("t", "threshold", "free_reserve", "vvprbis", None, "dividend"))
    assert o.taxes["corp_tax"].ravel()[0] == pytest.approx(20000.0)
    assert o.taxes["dividend_wht"].ravel()[0] == pytest.approx(14400.0)
    assert o.wealth_end.ravel()[0] == pytest.approx(70872.434, abs=1e-3)
    assert o.total_tax().ravel()[0] == pytest.approx(56536.866, abs=1e-3)  # 20,000 + 409.30 + 8,676.349 + 13,051.217 + 14,400


def test_bv_liquidation_reserve_then_liquidation(path):
    # credit 80,000 / 1.10 = 72,727.27 ; levy 7,272.73 ; liquidation: no extra tax ; wealth = 29,272.434 + 72,727.273 - 24,000 = 77,999.707
    o = _bv(path, BVStrategy("t", "threshold", "liquidation_reserve", "vvprbis", None, "liquidation"))
    assert o.taxes["lr_levy"].ravel()[0] == pytest.approx(7272.7273, abs=1e-3)
    assert o.wealth_end.ravel()[0] == pytest.approx(77999.707, abs=1e-3)
    assert o.total_tax().ravel()[0] == pytest.approx(49409.593, abs=1e-3)  # 20,000 + 409.30 + 8,676.349 + 13,051.217 + 7,272.727


def test_bv_ordinary_liquidation(path):
    # 30% x 80,000 = 24,000 ; wealth = 29,272.434 + 56,000 - 24,000 = 61,272.434
    o = _bv(path, BVStrategy("t", "threshold", "free_reserve", "ordinary", None, "liquidation"))
    assert o.wealth_end.ravel()[0] == pytest.approx(61272.434, abs=1e-3)


def test_bv_first_four_periods_exempt_from_pay_condition(path):
    # fixed pay 40,000 (< 51,000): taxable profit 151,000 - 40,000 = 111,000.
    # period 5: reduced rate lost -> 0.25 x 111,000 = 27,750 ; period 4 (exempt, interpretation) -> 0.20 x 100,000 + 0.25 x 11,000 = 22,750
    s = BVStrategy("t", "fixed", "free_reserve", "vvprbis", None, "dividend", pay_amount=40000.0)
    p5 = simulate_bv(np.array([[Y_BV]]), [2026], path, SINGLE, s, (1,), first_period=5)
    p4 = simulate_bv(np.array([[Y_BV]]), [2026], path, SINGLE, s, (1,), first_period=4)
    assert p5.taxes["corp_tax"].ravel()[0] == pytest.approx(27750.0)
    assert p4.taxes["corp_tax"].ravel()[0] == pytest.approx(22750.0)
    assert p5.reduced_rate_years.ravel()[0] == 0.0 and p4.reduced_rate_years.ravel()[0] == 1.0


# ---------------------------------------------------------------- policy path by calendar year
def test_policy_path_by_calendar_year(pol):
    path = PolicyPath(pol, (PathChange(2027, {"corp.reduced_rate": 0.25}, "P1-like"),))
    assert path.at(2026).v("corp.reduced_rate") == 0.20
    assert path.at(2027).v("corp.reduced_rate") == 0.25
    assert path.at(2040).v("corp.reduced_rate") == 0.25
    assert path.at(2027).rules["corp.reduced_rate"].status == "scenario"
    assert pol.rules["corp.reduced_rate"].value == 0.20  # baseline untouched
    t = path.used_table()
    assert "corp.reduced_rate" in set(t.rule_id)


# ---------------------------------------------------------------- findings of the owner's checklist review (15 Nov 2026)
def test_cheapest_qualifying_pay_is_half_of_profit_below_102k(path):
    # client pays 104,409.30 ; admin 4,000 + company contribution 409.30 -> profit before pay 100,000.  'threshold' pays min(51,000, 100,000 / 2) = 50,000:
    # taxable 50,000 <= pay -> qualifies for 20% (fifth period): corporate tax 10,000 ; post-tax profit 40,000
    s = BVStrategy("t", "threshold", "free_reserve", "vvprbis", None, "dividend")
    o = simulate_bv(np.array([[104409.30]]), [2026], path, SINGLE, s, (1,), first_period=5)
    assert o.owner_pay.ravel()[0] == pytest.approx(50000.0)
    assert o.taxes["corp_tax"].ravel()[0] == pytest.approx(10000.0)
    assert o.reduced_rate_years.ravel()[0] == 1.0


def test_vvprbis_starts_with_the_third_year_after_the_contribution_year(path):
    # new company (first period 2026), client pays 155,409.30 each year -> post-tax profit 80,000 a year, all distributed each year (VVPRbis dividends).
    # profit of 2026, 2027, 2028 bears 30% (3 x 24,000 = 72,000); profit of 2029 bears 18% (14,400): total 86,400.  A mature company pays 18% throughout.
    s = BVStrategy("t", "threshold", "distribute", "vvprbis", None, "liquidation")
    yv = np.array([[155409.30]] * 4)
    new = simulate_bv(yv, [2026, 2027, 2028, 2029], path, SINGLE, s, (1,), first_period=1)
    old = simulate_bv(yv, [2026, 2027, 2028, 2029], path, SINGLE, s, (1,), first_period=5)
    assert new.taxes["dividend_wht"].ravel()[0] == pytest.approx(86400.0)
    assert old.taxes["dividend_wht"].ravel()[0] == pytest.approx(4 * 14400.0)
    assert new.ledger_residual < 1e-6


def test_liquidation_reserve_is_available_before_vvprbis_starts(path):
    # the reserve is not tied to VVPRbis eligibility: a new company's first-year profit (80,000) can be credited at once: levy 7,272.73
    s = BVStrategy("t", "threshold", "liquidation_reserve", "vvprbis", None, "liquidation")
    o = simulate_bv(np.array([[155409.30]]), [2026], path, SINGLE, s, (1,), first_period=1)
    assert o.taxes["lr_levy"].ravel()[0] == pytest.approx(7272.7273, abs=1e-3)
    assert o.taxes["liquidation_tax"].ravel()[0] == 0.0
