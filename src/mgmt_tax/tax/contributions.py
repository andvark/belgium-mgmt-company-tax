"""Social contributions: employee 13.07% / employer 25%, and self-employed (main occupation).

Self-employed base (modelling choice, rule ``se.base_net_of_contribution``): the contribution is a percentage of income
NET of the contribution itself.  With net income N and tiers (r1 up to C1, r2 from C1 to C2, r3 above) the contribution is
f(N) = r1*min(N,C1) + r2*clip(N-C1,0,C2-C1) + r3*max(N-C2,0); the gross income is B = N + f(N).  The inverse is piecewise
linear and is solved in closed form.  The minimum annual contribution (4 x quarterly minimum) always applies (no cap at B):
an active self-employed person owes it even on very low income.
"""

from __future__ import annotations

import numpy as np

from mgmt_tax.policy import Policy


def employee_ssc(gross_wage: np.ndarray, pol: Policy) -> np.ndarray:
    return np.asarray(gross_wage, dtype=float) * pol.v("ssc.employee_rate")


def employer_ssc(gross_wage: np.ndarray, pol: Policy) -> np.ndarray:
    return np.asarray(gross_wage, dtype=float) * pol.v("ssc.employer_rate")


def employer_cost(gross_wage: np.ndarray, pol: Policy) -> np.ndarray:
    """Total employer cost = gross wage + employer contributions - reductions/work bonus (open input, default 0)."""
    w = np.asarray(gross_wage, dtype=float)
    return w + employer_ssc(w, pol) - pol.v("emp.employer_reductions_and_work_bonus")


def wage_from_employer_cost(cost: np.ndarray, pol: Policy) -> np.ndarray:
    """Gross wage whose total employer cost equals ``cost`` (the same revenue the contractor would bill)."""
    return (np.asarray(cost, dtype=float) + pol.v("emp.employer_reductions_and_work_bonus")) / (1.0 + pol.v("ssc.employer_rate"))


def self_employed_contribution(gross_income: np.ndarray, pol: Policy) -> np.ndarray:
    """Annual contribution on gross professional income B (before the contribution)."""
    r1, c1, r2, c2, r3 = (pol.v(k) for k in ("se.rate_1", "se.ceiling_1", "se.rate_2", "se.ceiling_2", "se.rate_above_ceiling_2"))
    fee = pol.v("se.admin_fee_rate")
    b = np.clip(np.asarray(gross_income, dtype=float), 0.0, None)
    if pol.v("se.base_net_of_contribution"):
        b1 = c1 * (1 + r1)
        b2 = b1 + (c2 - c1) * (1 + r2)
        net = np.where(b <= b1, b / (1 + r1), np.where(b <= b2, c1 + (b - b1) / (1 + r2), c2 + (b - b2) / (1 + r3)))
        contrib = b - net
    else:
        contrib = r1 * np.minimum(b, c1) + r2 * np.clip(b - c1, 0.0, c2 - c1) + r3 * np.maximum(b - c2, 0.0)
    contrib = contrib * (1.0 + fee)
    return np.maximum(contrib, 4.0 * pol.v("se.min_quarterly"))
