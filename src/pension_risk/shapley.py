"""A.12: all 16 coalitions; shared summaries for both metrics and all tables."""

from itertools import combinations
from math import factorial

import pandas as pd

from .config import GRID, MECHS, Settings
from .engines import run_grid
from .metrics import describe


def coalitions(players=MECHS):
    return [frozenset(s) for r in range(len(players) + 1) for s in combinations(players, r)]


def shapley_values(values, players=MECHS):
    """Average marginal value over coalition orderings, with exact factorial weights."""
    players = tuple(players)
    if set(values) != set(coalitions(players)):
        raise ValueError("Supply every coalition exactly once")
    n = len(players)
    phi = dict.fromkeys(players, 0.0)
    for player in players:
        for subset in coalitions(tuple(p for p in players if p != player)):
            weight = factorial(len(subset)) * factorial(n - len(subset) - 1) / factorial(n)
            phi[player] += weight * (values[subset | {player}] - values[subset])
    return phi


class CoalitionStudy:
    """One simulation per (age, coalition); retain compact summaries, not paths."""

    def __init__(self, data, settings=Settings(), scenarios=None):
        self.data, self.settings, self.scenarios = data, settings, scenarios
        self.summaries = {}

    def get(self, age, active=frozenset()):
        active = frozenset(active)
        if not active <= set(MECHS):
            raise ValueError("Unknown mechanism")
        key = (age, active)
        if key not in self.summaries:
            flags = {m: m in active for m in MECHS}
            real = run_grid(self.data, age, **flags, settings=self.settings, scenarios=self.scenarios)[1]
            self.summaries[key] = describe(real)
        return self.summaries[key]

    def shapley_for_age(self, age, metric="CoV"):
        base = self.get(age)[metric]
        values = {s: base - self.get(age, s)[metric] for s in coalitions()}
        return shapley_values(values), values[frozenset(MECHS)]

    def shapley_table(self, metric="CoV", ages=GRID):
        rows = []
        for age in ages:
            phi, total = self.shapley_for_age(age, metric)
            row = {"Age": age, "Total reduction": total}
            row.update({f"{m}_value": phi[m] for m in MECHS})
            row.update({f"{m}_share": 100 * phi[m] / total if total else 0.0 for m in MECHS})
            rows.append(row)
        return pd.DataFrame(rows)
