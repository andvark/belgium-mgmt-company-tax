"""Paired shock paths (common random numbers).

Every arrangement, profit level and strategy sees the SAME shock path for the same replicate and calendar year: draws are keyed
by (seed, stream, year, replicate id) through belgium_abm's counter-based generator, so adding or removing a strategy never
changes anyone's shocks.  Employee: revenue x exp(wage residual); business forms: x exp(wage residual + business shock); both
are mean-preserving (exp(x - var/2)) and then rescaled to replicate-mean exactly 1 in each year, so every arrangement has the same
average revenue at a given profit level.
"""

from __future__ import annotations

import numpy as np
from belgium_abm.engines import crn

from mgmt_tax.policy import Policy


def paired_shocks(seed: int, n_rep: int, years: list[int], pol: Policy) -> tuple[np.ndarray, np.ndarray]:
    """Return (m_employee, m_business), each of shape (T, n_rep), with mean 1."""
    ids = np.arange(n_rep)
    sw, rw = pol.v("asm.wage_shock_sigma"), pol.v("asm.wage_shock_rho")
    sb, rb = pol.v("asm.business_shock_sigma"), pol.v("asm.business_shock_rho")
    var_w = sw**2 / (1 - rw**2)
    var_b = sb**2 / (1 - rb**2)
    w = np.sqrt(var_w) * crn.normal(seed, "init_wage", 0, ids)
    b = np.sqrt(var_b) * crn.normal(seed, "init_biz", 0, ids)
    m_emp, m_bus = [], []
    for yr in years:
        w = rw * w + sw * crn.normal(seed, "wage", yr, ids)
        b = rb * b + sb * crn.normal(seed, "biz", yr, ids)
        me = np.exp(w - 0.5 * var_w)
        m_emp.append(me)
        m_bus.append(me * np.exp(b - 0.5 * var_b))
    m_emp, m_bus = np.array(m_emp), np.array(m_bus)
    # variance reduction: rescale so the replicate mean is exactly 1 in every year, so that sampling noise in expected revenue
    # cannot masquerade as an advantage of one arrangement (differences across replicates are untouched)
    return m_emp / m_emp.mean(axis=1, keepdims=True), m_bus / m_bus.mean(axis=1, keepdims=True)
