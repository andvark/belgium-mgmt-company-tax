"""Invariants of the proposal mechanics (all are scenario assumptions)."""

import numpy as np
import pytest

from mgmt_tax.arrangements import Household
from mgmt_tax.compare_b import p1, p2, p3, run_one, strategies_ext
from mgmt_tax.compare_a import HOUSEHOLDS
from mgmt_tax.policy import PolicyPath

pytestmark = pytest.mark.unconfirmed
PROF = (50e3, 100e3, 200e3)


def wealth(pol, changes, hh=HOUSEHOLDS[0], conc=0.85, hire=0.0, n=60, first=5):
    outs, _ = run_one(PolicyPath(pol, tuple(changes)), hh, first, n, 5, PROF, strategies_ext(), hire, conc)
    return outs


def test_ledger_reconciles_under_every_proposal_and_combination(pol):
    for changes, hire in (((p1(2027),), 10000.0), ((p2(2),), 0.0), ((p3(0.8, 3),), 0.0), ((p1(2027), p2(3), p3(0.7, 5)), 5000.0)):
        for hh in (HOUSEHOLDS[0], HOUSEHOLDS[3]):
            outs = wealth(pol, changes, hh=hh, hire=hire, n=30)
            for k, o in outs.items():
                assert o.ledger_residual < 1e-6, (k, changes, o.ledger_residual)


# Two baseline-DOMINATED strategies can gain when a proposal blocks part of what they do, so they are excluded from the monotonicity checks:
#  * *_lr_div_k5 forces an interim liquidation-reserve dividend (18.82%) although liquidation (10%) is cheaper; a tighter cap blocks part of it;
#  * *_lr_liq_antiabuse pays levy 10% + 30% on the payout (37%) and is better off when blocked from the reserve (ordinary 30%).
DOMINATED = ("lr_div_k5", "antiabuse")


def _keys(d):
    return [k for k in d if not any(x in k for x in DOMINATED)]


def test_each_proposal_can_only_hurt_a_fixed_strategy_pathwise(pol):
    base = wealth(pol, ())
    for changes in ((p1(2027),), (p2(2),), (p2(3),), (p3(0.9, 3),), (p3(0.7, 3),), (p1(2027), p2(2), p3(0.9, 3))):
        scn = wealth(pol, changes)
        for k in _keys(base):
            assert (scn[k].wealth_end <= base[k].wealth_end + 1e-6).all(), (k, changes)


def test_employee_and_sole_trader_are_untouched_by_the_proposals(pol):
    base = wealth(pol, ())
    scn = wealth(pol, (p1(2027), p2(2), p3(0.7, 3)))
    for k in ("EMPLOYEE", "SOLE_TRADER"):
        assert np.array_equal(base[k].wealth_end, scn[k].wealth_end)


def test_tighter_proposal_parameters_hurt_more(pol):
    m2, m3 = wealth(pol, (p2(2),)), wealth(pol, (p2(3),))
    t70, t90, t100 = wealth(pol, (p3(0.7, 3),)), wealth(pol, (p3(0.9, 3),)), wealth(pol, (p3(1.0, 3),))
    l3, l5 = wealth(pol, (p3(0.9, 3),)), wealth(pol, (p3(0.9, 5),))
    s2027, s2028 = wealth(pol, (p2(2, 2027),)), wealth(pol, (p2(2, 2028),))
    for k in _keys(m2):
        assert (m3[k].wealth_end <= m2[k].wealth_end + 1e-6).all()          # 3x is tighter than 2x
        assert (t70[k].wealth_end <= t90[k].wealth_end + 1e-6).all()        # lower threshold binds more often
        assert (t90[k].wealth_end <= t100[k].wealth_end + 1e-6).all()
        assert (l3[k].wealth_end <= l5[k].wealth_end + 1e-6).all()          # a longer lookback binds less often
        assert (s2027[k].wealth_end <= s2028[k].wealth_end + 1e-6).all()    # earlier start


def test_p3_never_binds_for_an_owner_with_low_concentration(pol):
    base = wealth(pol, (), conc=0.5)
    scn = wealth(pol, (p3(0.9, 3),), conc=0.5)
    for k in base:
        assert np.array_equal(base[k].wealth_end, scn[k].wealth_end)


def test_p1_hire_is_worthless_when_the_reduced_rate_is_already_lost(pol):
    """A strategy that pays below EUR 51,000 never had the reduced rate (after the exempt periods), so P1 leaves it unchanged."""
    base = wealth(pol, (), first=5)
    scn = wealth(pol, (p1(2026),), first=5)
    for k in base:
        if k.startswith("BV:min_") or k == "BV:shell_full_pay":
            assert np.allclose(base[k].wealth_end, scn[k].wealth_end), k


def test_pay_cap_vanishes_when_payroll_is_large(pol):
    """With m = 2 and director pay of 100,000 the cap (50,000) exceeds every dividend of the revenue levels tested at 50,000: no effect."""
    base = wealth(pol, ())
    scn = wealth(pol, (p2(2),))
    k = "BV:fx100_dist_vvpr"
    # at revenue 50,000 profit is below the pay anyway (pay capped at profit, no dividends): identical
    assert np.allclose(base[k].wealth_end[0], scn[k].wealth_end[0])
