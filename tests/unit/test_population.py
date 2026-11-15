"""Population layer: hand-computed toy case, conservation, limiting cases.  The layer is assumption-driven; these tests check the arithmetic, not the assumptions."""
from pathlib import Path

import numpy as np
import pytest

from mgmt_tax import population as pop

HFCS = Path(__file__).resolve().parents[2] / "data" / "hfcs_wealth_targets_BE_2023.csv"
K, C, P, T = len(pop.CATS), len(pop.CONCS), len(pop.PROF), pop.T


def toy():
    """One owner type (category 0, one client, revenue 100,000): taxes 10,000 a year today, 12,000 from 2028 under the scenario; 15-year wealth
    500,000 today, 440,000 under the scenario, 300,000 as a sole trader."""
    wk, wc, wp = np.zeros(K), np.zeros(len(pop.CONCS)), np.zeros(P)
    wk[0], wc[0], wp[5] = 1, 1, 1
    mix = pop.Mix(1000.0, wk, wc, wp)
    X = {k: np.zeros((K, C, P, T)) for k in ("base_tax", "scn_tax")}
    X["base_tax"][0, 0, 5, :] = 10000.0
    X["scn_tax"][0, 0, 5, :] = np.where(pop.YEARS >= 2028, 12000.0, 10000.0)
    X["base_w"], X["scn_w"] = np.zeros((K, C, P)), np.zeros((K, C, P))
    X["base_w"][0, 0, 5], X["scn_w"][0, 0, 5] = 500000.0, 440000.0
    X["sole_w"], X["emp_w"] = np.full(P, 300000.0), np.full(P, 250000.0)
    X["sole_tax"], X["emp_tax"] = np.full((P, T), 15000.0), np.full((P, T), 20000.0)
    return mix, X


def test_profit_grid_index():
    assert pop.PROF[5] == 100000.0


def test_static_revenue_toy():
    mix, X = toy()
    v = pop.static_revenue(mix, X)
    assert v[0] == 0 and v[1] == 0                                   # 2026, 2027: no change
    assert v[2] == pytest.approx(1000 * 2000.0)                      # 2028 on: 1,000 owners x 2,000


def test_dynamic_toy_hand_computed():
    mix, X = toy()
    # loss = 60,000 over 15 years at revenue 100,000 -> 60,000 / (15 x 100,000) x 100 = 4.0 pp ; s = 0.1 -> target share exp(-0.4) = 0.670320
    f = np.exp(-0.4)
    d = pop.dynamic(mix, X, "P2x2_2028", s=0.1, phi=0.0, eps=0.0, tau=1.0)
    assert d["loss_pp"][0, 0, 5] == pytest.approx(4.0)
    assert d["bv_owners"][2] == pytest.approx(1000 * f)              # tau = 1: immediate adjustment in 2028
    assert d["bv_owners"][1] == pytest.approx(1000.0)                # before the start year
    # 2028: stayers 670.32 x (12,000 - 10,000) + leavers 329.68 x (sole trader 15,000 - baseline 10,000)
    expected = 1000 * f * 2000.0 + 1000 * (1 - f) * 5000.0
    assert d["revenue"][2] == pytest.approx(expected)
    assert d["bv_owners"] + d["leavers"] == pytest.approx(1000.0)    # conservation every year
    # everybody who stops: tax of the leavers is lost -> -10,000 each
    d2 = pop.dynamic(mix, X, "P2x2_2028", s=0.1, phi=1.0, eps=0.0, tau=1.0)
    assert d2["revenue"][2] == pytest.approx(1000 * f * 2000.0 - 1000 * (1 - f) * 10000.0)
    assert d2["entrepreneurs_lost"][2] == pytest.approx(1000 * (1 - f))
    assert d["entrepreneurs_lost"][2] == pytest.approx(0.0)          # sole traders stay entrepreneurs
    assert d["self_employed_total"][2] == pytest.approx(1000.0)


def test_zero_sensitivity_means_dynamic_equals_static():
    mix, X = toy()
    d = pop.dynamic(mix, X, "P2x2_2028", s=0.0, phi=0.5, eps=0.3)
    assert np.allclose(d["revenue"], pop.static_revenue(mix, X)) and d["leavers"].max() == 0


def test_partial_adjustment_converges():
    mix, X = toy()
    d = pop.dynamic(mix, X, "P2x2_2028", s=0.1, phi=0.0, eps=0.0, tau=3.0)
    gap = np.abs(d["bv_owners"] - 1000 * np.exp(-0.4))
    assert gap[-1] < gap[2] and (np.diff(d["bv_owners"][2:]) <= 1e-9).all()


def test_strict_bound_ignores_owners_already_worse_off_today():
    mix, X = toy()
    X["base_w"][0, 0, 5] = 200000.0      # worse than the sole trader (300,000) already today
    X["scn_w"][0, 0, 5] = 150000.0
    assert pop.dynamic(mix, X, "P2x2_2028", 0, 0, 0, tau=1.0, strict=True)["leavers"].max() == 0   # not a policy-induced leaver


def test_strict_bound_only_owners_with_negative_advantage_leave():
    mix, X = toy()
    assert pop.dynamic(mix, X, "P2x2_2028", 0, 0, 0, strict=True)["leavers"].max() == 0       # 440,000 > 300,000 sole trader: nobody leaves
    X["scn_w"][0, 0, 5] = 250000.0
    d = pop.dynamic(mix, X, "P2x2_2028", 0, 0, 0, tau=1.0, strict=True)
    assert d["bv_owners"][-1] == pytest.approx(0.0, abs=1e-9)


def test_lognormal_weights():
    w = pop.lognormal_weights(90000, 0.6)
    assert w.sum() == pytest.approx(1.0) and (w >= 0).all()
    assert pop.lognormal_weights(150000, 0.6)[-3:].sum() > w[-3:].sum()


@pytest.mark.skipif(not HFCS.exists(), reason="belgium_abm data not available")
def test_national_wealth_matches_observed_aggregates():
    n = pop.NationalWealth(HFCS)
    w = n.sample(200000)
    assert w.mean() == pytest.approx(n.targets["mean"], rel=0.01)
    assert np.median(w) == pytest.approx(n.targets["median"], rel=0.01)
    assert abs(pop.gini(w) - n.targets["gini"]) < 0.02
    assert abs(pop.top_share(w, 0.9) - n.targets["top10"]) < 0.02


def test_gini_of_equal_and_unequal():
    assert pop.gini(np.full(100, 5.0)) == pytest.approx(0.0, abs=1e-9)
    assert pop.gini(np.r_[np.zeros(99), 1.0]) == pytest.approx(0.99, abs=1e-6)


@pytest.mark.skipif(not HFCS.exists(), reason="belgium_abm data not available")
def test_zero_loss_leaves_wealth_gini_unchanged():
    mix, X = toy()
    X["scn_w"][:] = X["base_w"]
    r = pop.wealth_effect(pop.NationalWealth(HFCS), mix, X, 5.2e6, "middle (30-80th percentile)", 0.0, "static")
    assert r["gini_after"] == pytest.approx(r["gini_before"])
