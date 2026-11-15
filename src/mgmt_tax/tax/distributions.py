"""Dividend regimes, liquidation-reserve levy/withholding and liquidation routes.

Liquidation reserve (rules ``lr.*``, confirmed in the owner's checklist review): the levy is 10% of the amount CREDITED to the reserve.  From an
amount ``a`` available after ordinary corporate tax the company credits ``a / 1.10`` and pays the levy ``a - a / 1.10``.  Paid out as a qualifying dividend
the 9.8% withholding applies to the credited amount: total (0.10 + 0.098) / 1.10 = 18.00% of ``a``.  Paid out on actual liquidation: exempt at payout,
so the total is 0.10 / 1.10 = 9.09% of ``a``, unless the anti-abuse flag applies.
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
    """Use ``amount`` (available after corporate tax) for the liquidation reserve; return (levy paid by the company, amount credited to the reserve account)."""
    a = np.clip(np.asarray(amount, dtype=float), 0.0, None)
    credited = a / (1.0 + pol.v("lr.levy_rate"))
    return a - credited, credited


def lr_dividend_withholding(pool_amount: np.ndarray, pol: Policy) -> np.ndarray:
    return pol.v("lr.dividend_withholding") * np.asarray(pool_amount, dtype=float)


def lr_liquidation_tax(pool_amount: np.ndarray, anti_abuse: bool, pol: Policy) -> np.ndarray:
    rate = pol.v("lr.anti_abuse_rate") if anti_abuse else pol.v("lr.liquidation_extra_withholding")
    return rate * np.asarray(pool_amount, dtype=float)


def ordinary_liquidation_tax(free_surplus: np.ndarray, pol: Policy) -> np.ndarray:
    """30% on the liquidation surplus above fiscal paid-up capital; ``free_surplus`` is already net of paid-up capital."""
    return pol.v("liq.ordinary_rate") * np.clip(np.asarray(free_surplus, dtype=float), 0.0, None)
