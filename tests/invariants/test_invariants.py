"""Invariants that must hold whatever the rule values are."""

import numpy as np
import pytest

from mgmt_tax.arrangements import Household, simulate_employee, simulate_sole_trader
from mgmt_tax.compare_a import HOUSEHOLDS, run_cell, strategies
from mgmt_tax.policy import PathChange, PolicyPath
from mgmt_tax.shocks import paired_shocks
from mgmt_tax.strategies import BVStrategy, net_of_pay, simulate_bv, solve_pay_for_net
from mgmt_tax.tax.contributions import employer_cost, self_employed_contribution, wage_from_employer_cost
from mgmt_tax.tax.pit import bracket_tax, income_tax, total_income_tax

pytestmark = pytest.mark.unconfirmed
YEARS = list(range(2026, 2041))


def _rev(n_rep=40, seed=7, profits=(40e3, 100e3, 250e3), pol=None):
    me, mb = paired_shocks(seed, n_rep, YEARS, pol)
    yb = np.asarray(profits)[None, :, None]
    return yb * me[:, None, :], yb * mb[:, None, :], (len(profits), n_rep)


@pytest.mark.parametrize("real_return", [0.0, 0.03])
@pytest.mark.parametrize("hh", HOUSEHOLDS, ids=lambda h: h.name)
def test_ledger_reconciles_everywhere(pol, hh, real_return):
    """Revenue + interest = admin + all taxes + spending + change in private wealth + change in company equity, every year,
    for the employee, the sole trader and every BV strategy (so nothing is created, lost or counted twice)."""
    path = PolicyPath(pol, (PathChange(2026, {"asm.real_return": real_return}, "r"),))
    for first_period in (1, 5):
        outs, _ = run_cell(path, hh, first_period, 40, 11, profits=(40e3, 100e3, 250e3))
        for name, o in outs.items():
            assert o.ledger_residual < 1e-6, (name, o.ledger_residual)


def test_resources_are_conserved_over_the_horizon(pol):
    """With zero return: total revenue = admin costs + all taxes and contributions + total spending + final wealth."""
    ye, ys, shape = _rev(pol=pol)
    path = PolicyPath(pol)
    hh = Household("single", 1, 0, False)
    need = hh.owner_need(pol) * len(YEARS)
    for o, y in ((simulate_employee(ye, YEARS, path, hh, shape), ye), (simulate_sole_trader(ys, YEARS, path, hh, shape), ys),
                 (simulate_bv(ys, YEARS, path, hh, BVStrategy("x", "liquidity", "liquidation_reserve", exit="liquidation"), shape, 5), ys)):
        lhs = y.sum(axis=0)
        rhs = o.admin + o.total_tax() + need + o.wealth_end
        assert np.allclose(lhs, rhs, atol=1e-6)


def test_pit_allowance_reduction_equals_zero_first_bracket(pol):
    """For income above the allowance, 'brackets then minus 25% x 11,550' = a 0% bracket on the first 11,550 (and 25% up to 16,720)."""
    x = np.linspace(11550, 400000, 500)
    alt = bracket_tax(x, [[11550, 0.0], [16720, 0.25], [29510, 0.40], [51070, 0.45], [None, 0.50]])
    assert np.allclose(income_tax(x, pol)[0], alt)


def test_pit_monotone_and_continuous(pol):
    x = np.linspace(0, 300000, 30001)
    t = total_income_tax(x, pol)
    d = np.diff(t)
    assert (d >= -1e-9).all() and d.max() <= 0.5 * 1.072 * (x[1] - x[0]) + 1e-9


def test_contributions_monotone_continuous_and_employer_cost_roundtrip(pol):
    b = np.linspace(0, 300000, 30001)
    c = self_employed_contribution(b, pol)
    assert (np.diff(c) >= -1e-9).all()
    assert np.diff(c).max() <= 0.205 * (b[1] - b[0]) + 1e-9  # no jump
    w = wage_from_employer_cost(np.array([30000.0, 123456.78]), pol)
    assert np.allclose(employer_cost(w, pol), [30000.0, 123456.78])


def test_bv_with_full_pay_equals_sole_trader_with_same_costs(pol):
    """A BV that pays out all profit as director pay has no corporate tax and no dividends: it must equal a sole trader whose
    administrative cost equals the BV's (admin + company contribution)."""
    ye, ys, shape = _rev(pol=pol)
    hh = Household("single", 1, 0, False)
    bv = simulate_bv(ys, YEARS, PolicyPath(pol), hh, BVStrategy("shell", "full", "distribute", "ordinary", None, "liquidation"), shape, 5)
    cost = pol.v("asm.admin_cost_bv") + pol.v("corp.annual_company_contribution")
    sole = simulate_sole_trader(ys, YEARS, PolicyPath(pol.with_overrides({"asm.admin_cost_sole_trader": cost}, "same cost")), hh, shape)
    assert np.allclose(bv.wealth_end, sole.wealth_end, atol=1e-6)


def test_a_path_that_changes_nothing_equals_baseline(pol):
    """A dated change that sets rules to their current values must reproduce the baseline exactly."""
    same = PathChange(2028, {"corp.reduced_rate": 0.20, "div.vvprbis_rate": 0.18}, "no-op")
    a, _ = run_cell(PolicyPath(pol), HOUSEHOLDS[0], 5, 30, 3, profits=(60e3, 150e3))
    b, _ = run_cell(PolicyPath(pol, (same,)), HOUSEHOLDS[0], 5, 30, 3, profits=(60e3, 150e3))
    for k in a:
        assert np.array_equal(a[k].wealth_end, b[k].wealth_end), k


def test_policy_change_after_horizon_or_unused_rule_changes_nothing(pol):
    far = PathChange(2041, {"corp.reduced_rate": 0.25}, "after horizon")
    a, _ = run_cell(PolicyPath(pol), HOUSEHOLDS[0], 5, 20, 3, profits=(60e3,))
    b, _ = run_cell(PolicyPath(pol, (far,)), HOUSEHOLDS[0], 5, 20, 3, profits=(60e3,))
    for k in a:
        assert np.array_equal(a[k].wealth_end, b[k].wealth_end)


def test_shocks_are_paired_mean_one_and_independent_of_the_number_of_replicates(pol):
    me, mb = paired_shocks(5, 100, YEARS, pol)
    assert np.allclose(me.mean(axis=1), 1.0) and np.allclose(mb.mean(axis=1), 1.0)
    # same seed, different replicate count: the first replicates keep their raw draws up to the (replicate-mean) rescaling
    me2, _ = paired_shocks(5, 60, YEARS, pol)
    r = (me[:, :60] * me.mean(axis=1, keepdims=True)) / (me2 * me2.mean(axis=1, keepdims=True))  # undo rescaling is not possible; compare ratios across years
    ratios = me[:, :60] / me2
    assert np.allclose(ratios, ratios[:, [0]], rtol=1e-9)  # constant across replicates within a year => identical underlying draws
    # strategies/arrangements see identical shocks: the employee path is the common factor of the business path
    assert np.corrcoef(np.log(me[:, 0]), np.log(mb[:, 0]))[0, 1] > 0.3


def test_wealth_is_increasing_in_profit_level_for_every_arrangement(pol):
    outs, _ = run_cell(PolicyPath(pol), HOUSEHOLDS[0], 5, 40, 9, profits=(40e3, 60e3, 80e3, 100e3, 130e3, 160e3, 200e3, 250e3))
    for k, o in outs.items():
        m = o.wealth_end.mean(axis=1)
        assert (np.diff(m) > 0).all(), k


def test_exit_cost_ordering_and_lock_mechanics(pol):
    """Effective tax on retained post-tax profit: LR liquidation 10% < VVPRbis 18% < ordinary liquidation 30%.
    The LR dividend route costs 18.82% only on vintages past the 3-year lock: with a lump in the last year (2040) the vintages
    2026-2037 (12 of 15) are paid as dividends and 2038-2040 stay locked and are liquidated at no extra withholding."""
    ys = np.full((len(YEARS), 1, 1), 150000.0)
    hh = Household("single", 1, 0, False)
    out = {}
    for name, s in {"lr_liq": BVStrategy("a", "threshold", "liquidation_reserve", "vvprbis", None, "liquidation"),
                    "vvpr": BVStrategy("b", "threshold", "free_reserve", "vvprbis", None, "dividend"),
                    "lr_div": BVStrategy("c", "threshold", "liquidation_reserve", "vvprbis", 15, "liquidation"),
                    "ord": BVStrategy("d", "threshold", "free_reserve", "ordinary", None, "liquidation")}.items():
        out[name] = simulate_bv(ys, YEARS, PolicyPath(pol), hh, s, (1, 1), 5)
    w = {k: o.wealth_end.item() for k, o in out.items()}
    assert w["lr_liq"] > w["lr_div"] and w["lr_liq"] > w["vvpr"] > w["ord"]
    # hand arithmetic: profit before pay 150,000 - 4,000 - 409.30 = 145,590.70 ; pay 51,000 ; taxable 94,590.70 ; corporate tax 20% = 18,918.14 ;
    # post-tax 75,672.56 per year ; reserve credited 0.9 x 75,672.56 = 68,105.304 per vintage ; withholding 9.8% on 12 vintages
    a = 145590.70 - 51000.0
    post = a - 0.20 * a
    assert out["lr_div"].taxes["dividend_wht"].item() == pytest.approx(0.098 * 12 * 0.9 * post, rel=1e-9)
    assert out["lr_liq"].taxes["lr_levy"].item() == pytest.approx(0.10 * 15 * post, rel=1e-9)
    assert out["vvpr"].taxes["dividend_wht"].item() == pytest.approx(0.18 * 15 * post, rel=1e-9)


def test_liquidity_pay_solver(pol):
    pmax = np.array([200000.0, 30000.0, 5000.0])
    for need in (0.0, 12000.0, 24000.0):
        pay = solve_pay_for_net(need, pmax, pol)
        net = net_of_pay(pay, pol)
        reach = net_of_pay(pmax, pol) >= need
        assert np.all(net[reach] >= need - 1e-4) and np.all(net[reach] <= need + 1e-3)  # minimal pay that reaches the need
        assert np.allclose(pay[~reach], pmax[~reach])                                   # cannot reach it: pays everything
    assert net_of_pay(np.array([0.0]), pol)[0] == pytest.approx(-3561.68)             # minimum contribution is owed even on zero pay


def test_no_unsourced_rule_and_statuses_are_declared(pol):
    from mgmt_tax.policy import STATUSES
    assert all(r.source and r.status in STATUSES for r in pol.rules.values())
    assert not any(r.status == "checked" for r in pol.rules.values())  # nothing has been confirmed against a primary source yet


def test_unmodelled_condition_raises(pol):
    from mgmt_tax.tax.corporate import qualifies_for_reduced_rate
    p = pol.with_overrides({"corp.dividend_capital_condition": True}, "x")
    with pytest.raises(NotImplementedError):
        qualifies_for_reduced_rate(np.array([1.0]), np.array([1.0]), 5, p)


def test_strategy_names_unique():
    names = [s.name for s in strategies()]
    assert len(names) == len(set(names))
