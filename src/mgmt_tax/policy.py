"""Versioned rules with provenance, and the policy path by calendar year.

Every value is a :class:`Rule` with a status and a source.  ``Policy.v(id)`` records which rules a
calculation actually used, so every output table can list the rules it depends on and their status.
There is no default value in code: an unknown id raises KeyError.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

STATUSES = ("checked", "supplied", "interpretation", "open", "assumed", "scenario")
UNCONFIRMED = ("supplied", "interpretation", "open", "assumed", "scenario")  # everything except "checked"


@dataclass(frozen=True)
class Rule:
    id: str
    value: Any
    status: str
    source: str
    hand_check: bool = False
    note: str = ""


@dataclass
class Policy:
    name: str
    year: int
    banner: str
    rules: dict[str, Rule]
    used: set[str] = field(default_factory=set)

    def v(self, rule_id: str) -> Any:
        r = self.rules[rule_id]
        self.used.add(rule_id)
        return r.value

    def with_overrides(self, overrides: dict[str, Any], label: str) -> Policy:
        """Return a copy with some values replaced; replaced rules get status 'scenario'."""
        rules = dict(self.rules)
        for rid, val in overrides.items():
            if rid not in rules:
                raise KeyError(f"override of unknown rule '{rid}'")
            rules[rid] = replace(rules[rid], value=copy.deepcopy(val), status="scenario", source=f"scenario override '{label}' of: {rules[rid].source}")
        return Policy(label, self.year, self.banner + f" | SCENARIO: {label}", rules)

    def table(self, only_used: bool = True) -> pd.DataFrame:
        ids = sorted(self.used) if only_used else sorted(self.rules)
        return pd.DataFrame([{"rule_id": i, "value": str(self.rules[i].value), "status": self.rules[i].status, "hand_check": self.rules[i].hand_check,
                              "source": self.rules[i].source} for i in ids])


def _load_one(path: Path) -> tuple[str, int, str, dict[str, Rule]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    rules = {}
    for rid, body in raw["rules"].items():
        st = body["status"]
        if st not in STATUSES:
            raise ValueError(f"{rid}: unknown status '{st}'")
        if not body.get("source"):
            raise ValueError(f"{rid}: every rule needs a source")
        rules[rid] = Rule(rid, body["value"], st, body["source"], bool(body.get("hand_check", False)), body.get("note", ""))
    return raw["name"], int(raw["policy_year"]), raw.get("banner", ""), rules


def load_policy(*paths: str | Path) -> Policy:
    """Load one or more YAML files (statutory rules and assumptions) into a single Policy."""
    names, banners, rules, year = [], [], {}, None
    for p in paths:
        n, y, b, r = _load_one(Path(p))
        dup = set(r) & set(rules)
        if dup:
            raise ValueError(f"duplicate rule ids across files: {sorted(dup)}")
        rules.update(r)
        names.append(n)
        banners.append(b)
        year = y if year is None else year
    return Policy("+".join(names), int(year), " | ".join(b for b in banners if b), rules)


@dataclass(frozen=True)
class PathChange:
    """From calendar year ``start_year`` (inclusive) the listed rule values replace the baseline."""

    start_year: int
    overrides: dict[str, Any]
    label: str


class PolicyPath:
    """Rules in force by calendar year: baseline plus dated changes (applied cumulatively in start-year order)."""

    def __init__(self, baseline: Policy, changes: tuple[PathChange, ...] = ()):
        self.baseline = baseline
        self.changes = tuple(sorted(changes, key=lambda c: c.start_year))
        self._cache: dict[int, Policy] = {}

    def at(self, year: int) -> Policy:
        if year not in self._cache:
            pol = self.baseline
            for c in self.changes:
                if c.start_year <= year:
                    pol = pol.with_overrides(c.overrides, c.label)
            self._cache[year] = pol
        return self._cache[year]

    def used_table(self) -> pd.DataFrame:
        used: set[str] = set(self.baseline.used)
        for p in self._cache.values():
            used |= p.used
        status = {}
        for p in [self.baseline, *self._cache.values()]:
            for rid in used:
                status[rid] = p.rules[rid]  # later (overridden) policies win
        return pd.DataFrame([{"rule_id": i, "value": str(status[i].value), "status": status[i].status, "hand_check": status[i].hand_check,
                              "source": status[i].source} for i in sorted(used)])

    @property
    def banner(self) -> str:
        labels = [c.label for c in self.changes]
        return self.baseline.banner + (" | PATH CHANGES: " + "; ".join(f"{c.label} from {c.start_year}" for c in self.changes) if labels else "")
