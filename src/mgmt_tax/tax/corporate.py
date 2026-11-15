"""Corporate tax with two rates and the director-remuneration condition for the reduced rate."""

from __future__ import annotations

import numpy as np

from mgmt_tax.policy import Policy


def qualifies_for_reduced_rate(pay: np.ndarray, profit_before_pay: np.ndarray, period_index: int, pol: Policy) -> np.ndarray:
    """Pay condition: pay >= min(51,000, taxable profit before the director's pay); periods 1-4 are exempt (interpretation)."""
    if pol.v("corp.dividend_capital_condition"):
        raise NotImplementedError("the dividend-vs-paid-up-capital condition on the reduced rate is not modelled")
    if period_index <= pol.v("corp.pay_test_first_exempt_periods"):
        return np.ones_like(np.asarray(pay, dtype=float), dtype=bool)
    need = np.asarray(pol.v("corp.director_min_pay"), dtype=float)
    if pol.v("corp.pay_test_covers_profit"):
        need = np.minimum(need, np.clip(profit_before_pay, 0.0, None))
    return np.asarray(pay, dtype=float) >= need - 1e-9


def corporate_tax(taxable_profit: np.ndarray, qualifies: np.ndarray, pol: Policy) -> np.ndarray:
    tp = np.clip(np.asarray(taxable_profit, dtype=float), 0.0, None)
    std, red, band = pol.v("corp.standard_rate"), pol.v("corp.reduced_rate"), pol.v("corp.reduced_band")
    low = np.minimum(tp, band)
    return np.where(qualifies, red * low + std * (tp - low), std * tp)
