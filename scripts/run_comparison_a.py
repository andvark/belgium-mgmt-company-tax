"""Run comparison A under current law (baseline) and the sensitivity cases.  Usage: python scripts/run_comparison_a.py [out_dir]"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mgmt_tax.compare_a import HOUSEHOLDS, run_grid  # noqa: E402
from mgmt_tax.policy import PathChange, PolicyPath, load_policy  # noqa: E402

out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "outputs" / "comparison_A"
pol = load_policy(ROOT / "configs" / "policy_be_2026_supplied.yaml", ROOT / "configs" / "assumptions.yaml")

# label -> rule overrides applied from 2026.  Sensitivities change ONE input at a time; they are not alternative laws.
CASES = {
    "baseline": {},
    "return_2pct": {"asm.real_return": 0.02},
    "return_3pct": {"asm.real_return": 0.03},
    "lr_dividend_total_18pct": {"lr.dividend_withholding": 0.08889},        # 10% + 0.9 x 8.889% = 18% (owner's stated total)
    "lock_plus_one_year": {"lr.lock_extra_calendar_years": 1},
    "no_exempt_first_periods": {"corp.pay_test_first_exempt_periods": 0},   # alternative reading of 'test starts in the fifth period'
    "se_14pct_above_ceiling": {"se.rate_above_ceiling_2": 0.1416},
    "employee_deduction_3000": {"emp.professional_expense_rate": 1.0, "emp.professional_expense_cap": 3000.0},  # HYPOTHETICAL fixed deduction, not a rule
    "no_pay_covers_profit_rule": {"corp.pay_test_covers_profit": False},
    "anti_abuse_rate_0": {"lr.anti_abuse_rate": 0.0},
}
for label, ov in CASES.items():
    t = time.time()
    path = PolicyPath(pol, (PathChange(2026, ov, label),) if ov else ())
    run_grid(path, out, label, n_rep=300)  # same replicates and seed in every case, so differences are policy, not sampling
    print(f"{label}: {time.time() - t:.0f}s", flush=True)
