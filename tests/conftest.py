import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mgmt_tax.policy import PolicyPath, load_policy  # noqa: E402


@pytest.fixture()
def pol():
    return load_policy(ROOT / "configs" / "policy_be_2026_supplied.yaml", ROOT / "configs" / "assumptions.yaml")


@pytest.fixture()
def path(pol):
    return PolicyPath(pol)
