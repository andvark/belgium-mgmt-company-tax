"""One-year and multi-year simulation for the employee and the sole trader, plus shared containers.

Same economic activity: ``Y`` is the revenue the client pays (for an employee, the total employer cost).
Every arrangement starts with private wealth 0 (the BV owner starts at -paid-up capital, which sits in the company),
spends the household's fixed need each year, and saves the rest privately.  The ledger identity checked every year is

    Y + company interest + private interest = administrative costs + all taxes and contributions
                                              + owner spending need + change in private wealth + change in company equity

which proves nothing is created, lost or counted twice.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from mgmt_tax.policy import PolicyPath
from mgmt_tax.tax.contributions import employee_ssc, employer_cost, self_employed_contribution, wage_from_employer_cost
from mgmt_tax.tax.pit import total_income_tax

TAX_KEYS = ("pit", "ssc_employee", "ssc_employer", "ssc_self", "corp_tax", "company_contribution", "lr_levy", "dividend_wht", "liquidation_tax", "movable_income_tax")


@dataclass(frozen=True)
class Household:
    name: str
    adults: int  # 1 or 2
    children: int
    partner_employed: bool

    def need(self, pol) -> float:
        return pol.v("asm.need_first_adult") + (pol.v("asm.need_second_adult") if self.adults == 2 else 0.0) + self.children * pol.v("asm.need_per_child")

    def owner_need(self, pol) -> float:
        """Spending the owner's own income must finance: household need minus the partner's fixed net income."""
        partner = pol.v("asm.partner_net_income_employed") if (self.adults == 2 and self.partner_employed) else 0.0
        return max(0.0, self.need(pol) - partner)


@dataclass
class Outcome:
    label: str
    shape: tuple[int, ...]
    taxes: dict[str, np.ndarray] = field(default_factory=dict)
    admin: np.ndarray | None = None
    pension_base: np.ndarray | None = None
    owner_pay: np.ndarray | None = None
    wealth_end: np.ndarray | None = None
    equity_pre_exit: np.ndarray | None = None
    liquidity_gap: np.ndarray | None = None  # years' spending need not met by current-year income (before private savings)
    reduced_rate_years: np.ndarray | None = None
    tax_year_total: list[np.ndarray] = field(default_factory=list)   # per calendar year, all taxes and contributions
    tax_year_ssc: list[np.ndarray] = field(default_factory=list)     # of which social contributions
    private_path: list[np.ndarray] = field(default_factory=list)
    equity_path: list[np.ndarray] = field(default_factory=list)
    ledger_residual: float = 0.0

    def __post_init__(self):
        self.taxes = {k: np.zeros(self.shape) for k in TAX_KEYS}
        self.admin = np.zeros(self.shape)
        self.pension_base = np.zeros(self.shape)
        self.owner_pay = np.zeros(self.shape)
        self.liquidity_gap = np.zeros(self.shape)
        self.reduced_rate_years = np.zeros(self.shape)

    def total_tax(self) -> np.ndarray:
        return sum(self.taxes.values())

    def total_tax_excl_ssc(self) -> np.ndarray:
        return sum(v for k, v in self.taxes.items() if not k.startswith("ssc"))

    def total_ssc(self) -> np.ndarray:
        return sum(v for k, v in self.taxes.items() if k.startswith("ssc"))


def private_interest(wp: np.ndarray, pol) -> tuple[np.ndarray, np.ndarray]:
    """(gross interest, tax on it).  Positive wealth earns r taxed at the movable-income placeholder; debt costs r untaxed."""
    r = pol.v("asm.real_return")
    gross = r * wp
    tax = np.where(wp > 0, pol.v("asm.private_return_tax") * gross, 0.0)
    return gross, tax


def simulate_employee(Y: np.ndarray, years: list[int], path: PolicyPath, hh: Household, shape: tuple[int, ...]) -> Outcome:
    """Y has shape (T, ...) = total employer cost paid by the client each year."""
    out = Outcome("EMPLOYEE", shape)
    wp = np.zeros(shape)
    for t, yr in enumerate(years):
        pol = path.at(yr)
        cost = Y[t]
        wage = wage_from_employer_cost(cost, pol)
        ee = employee_ssc(wage, pol)
        prof = np.minimum(pol.v("emp.professional_expense_rate") * wage, pol.v("emp.professional_expense_cap"))
        pit = total_income_tax(wage - ee - prof, pol)
        net = wage - ee - pit
        er = cost - wage
        need = hh.owner_need(pol)
        gi, mov = private_interest(wp, pol)
        wp_new = wp + gi - mov + net - need
        taxes_t = {"pit": pit, "ssc_employee": ee, "ssc_employer": er, "movable_income_tax": mov}
        for k, v in taxes_t.items():
            out.taxes[k] = out.taxes[k] + v
        rhs = sum(taxes_t.values()) + need + (wp_new - wp)
        out.ledger_residual = max(out.ledger_residual, float(np.max(np.abs(cost + gi - rhs))))
        out.tax_year_total.append(sum(taxes_t.values()))
        out.tax_year_ssc.append(ee + er)
        out.pension_base += wage
        out.owner_pay += wage
        out.liquidity_gap += np.clip(need - net, 0.0, None)
        wp = wp_new
        out.private_path.append(wp.copy())
        out.equity_path.append(np.zeros(shape))
    out.wealth_end = wp
    out.equity_pre_exit = np.zeros(shape)
    return out


def simulate_sole_trader(Y: np.ndarray, years: list[int], path: PolicyPath, hh: Household, shape: tuple[int, ...]) -> Outcome:
    out = Outcome("SOLE_TRADER", shape)
    wp = np.zeros(shape)
    for t, yr in enumerate(years):
        pol = path.at(yr)
        admin = pol.v("asm.admin_cost_sole_trader")
        profit = Y[t] - admin
        ssc = self_employed_contribution(profit, pol)
        pit = total_income_tax(profit - ssc, pol)
        net = profit - ssc - pit
        need = hh.owner_need(pol)
        gi, mov = private_interest(wp, pol)
        wp_new = wp + gi - mov + net - need
        taxes_t = {"pit": pit, "ssc_self": ssc, "movable_income_tax": mov}
        for k, v in taxes_t.items():
            out.taxes[k] = out.taxes[k] + v
        rhs = admin + sum(taxes_t.values()) + need + (wp_new - wp)
        out.ledger_residual = max(out.ledger_residual, float(np.max(np.abs(Y[t] + gi - rhs))))
        out.tax_year_total.append(sum(taxes_t.values()))
        out.tax_year_ssc.append(ssc)
        out.admin += admin
        out.pension_base += profit - ssc
        out.owner_pay += profit
        out.liquidity_gap += np.clip(need - net, 0.0, None)
        wp = wp_new
        out.private_path.append(wp.copy())
        out.equity_path.append(np.zeros(shape))
    out.wealth_end = wp
    out.equity_pre_exit = np.zeros(shape)
    return out
