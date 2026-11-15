"""Corporate tax with two rates and the director-remuneration condition for the reduced rate (confirmed in the owner's checklist review):
periods 1-4 are exempt; afterwards director pay must be at least EUR 51,000, or - below that - at least the company's taxable income AFTER deducting that pay."""

from __future__ import annotations

import numpy as np

from mgmt_tax.policy import Policy


def qualifies_for_reduced_rate(pay: np.ndarray, profit_before_pay: np.ndarray, period_index: int, pol: Policy) -> np.ndarray:
    """Pay condition: pay >= 51,000, or pay >= taxable profit after deducting the pay (= profit before pay - pay); periods 1-4 are exempt."""
    if pol.v("corp.dividend_capital_condition"):
        raise NotImplementedError("the dividend-vs-paid-up-capital condition on the reduced rate is not modelled")
    if period_index <= pol.v("corp.pay_test_first_exempt_periods"):
        return np.ones_like(np.asarray(pay, dtype=float), dtype=bool)
    pay = np.asarray(pay, dtype=float)
    ok = pay >= pol.v("corp.director_min_pay") - 1e-9
    if pol.v("corp.pay_test_covers_profit"):
        ok = ok | (pay >= (np.asarray(profit_before_pay, dtype=float) - pay) - 1e-6)
    return ok


def corporate_tax(taxable_profit: np.ndarray, qualifies: np.ndarray, pol: Policy) -> np.ndarray:
    tp = np.clip(np.asarray(taxable_profit, dtype=float), 0.0, None)
    std, red, band = pol.v("corp.standard_rate"), pol.v("corp.reduced_rate"), pol.v("corp.reduced_band")
    low = np.minimum(tp, band)
    return np.where(qualifies, red * low + std * (tp - low), std * tp)
