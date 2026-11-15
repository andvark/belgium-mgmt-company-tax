"""Personal income tax (individual taxation).

Order of operations (supplied rule, correcting belgium_abm which deducts the allowance from income first):
  1. progressive brackets applied to taxable income;
  2. the tax-free allowance enters as a tax reduction: reduction_rate x allowance (= 25% x 11,550 = 2,887.50),
     subtracted from the tax and floored at zero;
  3. municipal surcharge (7.2%) on the resulting state tax.
"""

from __future__ import annotations

import numpy as np

from mgmt_tax.policy import Policy


def bracket_tax(taxable: np.ndarray, brackets: list[list]) -> np.ndarray:
    x = np.clip(np.asarray(taxable, dtype=float), 0.0, None)
    tax = np.zeros_like(x)
    lower = 0.0
    for upper, rate in brackets:
        hi = np.inf if upper is None else float(upper)
        tax = tax + np.clip(np.minimum(x, hi) - lower, 0.0, None) * float(rate)
        lower = hi
        if not np.isfinite(hi):
            break
    return tax


def income_tax(taxable: np.ndarray, pol: Policy) -> tuple[np.ndarray, np.ndarray]:
    """Return (state tax after the allowance reduction, municipal surcharge)."""
    gross = bracket_tax(taxable, pol.v("pit.brackets"))
    reduction = pol.v("pit.reduction_rate") * pol.v("pit.basic_allowance")
    state = np.maximum(gross - reduction, 0.0)
    return state, state * pol.v("pit.municipal_surcharge")


def total_income_tax(taxable: np.ndarray, pol: Policy) -> np.ndarray:
    s, m = income_tax(taxable, pol)
    return s + m
