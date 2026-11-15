"""Vintaged liquidation-reserve account with a lock.

Each allocation is stored under the calendar year of creation (its vintage).  A vintage may be paid out as a DIVIDEND
only when year - vintage >= lock_years + lock_extra_calendar_years.  Liquidation payouts ignore the lock (supplied rule:
a qualifying reserve paid out on actual liquidation carries no additional withholding).  Vintages matter for proposal 3
("new amounts from 2028") and for the lock.
"""

from __future__ import annotations

import numpy as np

from mgmt_tax.policy import Policy


class ReserveAccount:
    def __init__(self, shape: tuple[int, ...]):
        self.shape = shape
        self.vintages: dict[int, np.ndarray] = {}

    def add(self, year: int, amount: np.ndarray) -> None:
        amount = np.broadcast_to(np.asarray(amount, dtype=float), self.shape)
        self.vintages[year] = self.vintages.get(year, np.zeros(self.shape)) + amount

    def total(self) -> np.ndarray:
        out = np.zeros(self.shape)
        for a in self.vintages.values():
            out = out + a
        return out

    def eligible_years(self, year: int, pol: Policy) -> list[int]:
        wait = pol.v("lr.lock_years") + pol.v("lr.lock_extra_calendar_years")
        return [v for v in sorted(self.vintages) if year - v >= wait]

    def distributable(self, year: int, pol: Policy) -> np.ndarray:
        out = np.zeros(self.shape)
        for v in self.eligible_years(year, pol):
            out = out + self.vintages[v]
        return out

    def take_distributable(self, year: int, pol: Policy) -> np.ndarray:
        """Remove and return everything past the lock."""
        out = np.zeros(self.shape)
        for v in self.eligible_years(year, pol):
            out = out + self.vintages.pop(v)
        return out

    def take_all(self) -> np.ndarray:
        out = self.total()
        self.vintages.clear()
        return out

    def take_up_to(self, year: int, pol: Policy, limit: np.ndarray) -> np.ndarray:
        """Remove and return up to ``limit`` of the amounts past the lock, oldest vintage first."""
        left = np.broadcast_to(np.asarray(limit, dtype=float), self.shape).copy()
        out = np.zeros(self.shape)
        for v in self.eligible_years(year, pol):
            take = np.minimum(self.vintages[v], np.clip(left, 0.0, None))
            self.vintages[v] = self.vintages[v] - take
            out = out + take
            left = left - take
        return out
