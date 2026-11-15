"""Dividend regimes, liquidation-reserve levy/withholding and liquidation routes.

Liquidation reserve (interpretation, see rules ``lr.*``): of an amount x allocated from post-tax profit, the company pays a
levy lr.levy_rate * x and the reserve account holds x - levy.  Paid out as a dividend after the lock the withholding
(lr.dividend_withholding) applies to the amount distributed from the account: total = 10% + 0.9 * 9.8% = 18.82%.
Paid out on actual liquidation: no additional withholding (total 10%), unless the anti-abuse flag applies.
"""

from __future__ import annotations

import numpy as np

from mgmt_tax.policy import Policy


def dividend_rate(regime: str, pol: Policy) -> float:
    if regime == "ordinary":
        return pol.v("div.ordinary_rate")
    if regime == "vvprbis":
        return pol.v("div.vvprbis_rate")
    raise ValueError(regime)


def lr_allocate(amount: np.ndarray, pol: Policy) -> tuple[np.ndarray, np.ndarray]:
    """Allocate ``amount`` to the liquidation reserve; return (levy paid by the company, amount credited to the reserve account)."""
    x = np.clip(np.asarray(amount, dtype=float), 0.0, None)
    levy = pol.v("lr.levy_rate") * x
    return levy, x - levy


def lr_dividend_withholding(pool_amount: np.ndarray, pol: Policy) -> np.ndarray:
    return pol.v("lr.dividend_withholding") * np.asarray(pool_amount, dtype=float)


def lr_liquidation_tax(pool_amount: np.ndarray, anti_abuse: bool, pol: Policy) -> np.ndarray:
    rate = pol.v("lr.anti_abuse_rate") if anti_abuse else pol.v("lr.liquidation_extra_withholding")
    return rate * np.asarray(pool_amount, dtype=float)


def ordinary_liquidation_tax(free_surplus: np.ndarray, pol: Policy) -> np.ndarray:
    """30% on the liquidation surplus above fiscal paid-up capital; ``free_surplus`` is already net of paid-up capital."""
    return pol.v("liq.ordinary_rate") * np.clip(np.asarray(free_surplus, dtype=float), 0.0, None)
