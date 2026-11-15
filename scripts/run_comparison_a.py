"""Run comparison A under current law (baseline) and the sensitivity cases.  Usage: python scripts/run_comparison_a.py [out_dir]"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mgmt_tax.compare_a import HOUSEHOLDS, run_grid  # noqa: E402
from mgmt_tax.policy import PathChange, PolicyPath, load_policy  # noqa: E402

out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "outputs" / "comparison_A"
pol = load_policy(ROOT / "configs" / "policy_be_2026_supplied.yaml", ROOT / "configs" / "assumptions.yaml", ROOT / "configs" / "proposals.yaml")

# label -> rule overrides applied from 2026.  Sensitivities change ONE input at a time; they are not alternative laws.
CASES = {
    "baseline": {},
    "return_2pct": {"asm.real_return": 0.02},
    "return_3pct": {"asm.real_return": 0.03},
    "lock_without_extra_year": {"lr.lock_extra_calendar_years": 0},                 # earlier reading of the lock (a date-based model could differ)
    "vvprbis_no_wait": {"vvprbis.wait_years_after_contribution_year": 0},           # VVPRbis from the first year (affects new companies only)
    "employee_no_lump_sum": {"emp.professional_expense_rate": 0.0, "emp.professional_expense_cap": 0.0},   # earlier default: no professional-expense lump sum
    "no_lower_pay_exception": {"corp.pay_test_covers_profit": False},               # pay must reach EUR 51,000 to keep the 20% rate
    "anti_abuse_rate_0": {"lr.anti_abuse_rate": 0.0},
}
for label, ov in CASES.items():
    t = time.time()
    path = PolicyPath(pol, (PathChange(2026, ov, label),) if ov else ())
    run_grid(path, out, label, n_rep=300)  # same replicates and seed in every case, so differences are policy, not sampling
    print(f"{label}: {time.time() - t:.0f}s", flush=True)
