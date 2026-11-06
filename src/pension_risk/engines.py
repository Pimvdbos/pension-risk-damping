"""A.3-A.11: recovered mechanics, with shared loops in the maintained package.

The reconstruction notebook retains the independent stepwise implementations.
Both A.10's unseeded entry-age engine and A.11's seeded current-age engine are
available. The two illustrative extensions remain outside the four switches.
"""

from dataclasses import replace
import numpy as np

from .config import Settings
from .curves import exposure, hedge_ratio, liability_duration, protection_return, risk_free_1y


def annuity_factor(projection, years):
    return np.sum((1.0 + projection) ** (-np.arange(1, years + 1)))


def accumulated_to(age, settings=Settings()):
    capital = 0.0
    for _ in range(age - settings.entry_age):
        capital = (capital + settings.contribution) * (1.0 + settings.projection)
    return capital


def spread_update(pending, k, raw_shock):
    """Current slice participates immediately; overwritten after M updates."""
    pending[:, k % pending.shape[1]] = raw_shock / pending.shape[1]
    return pending.sum(axis=1)


def reserve_update(raw, previous, reserve, fill_rate=0.25, cap=2.0):
    """A.5/A.10 cash flows; reserve is mutated in place and earns no interest."""
    topup = np.minimum(np.maximum(previous - raw, 0.0), reserve)
    b = raw + topup
    reserve -= topup
    room = np.maximum(cap * previous - reserve, 0.0)
    contribution = np.minimum(fill_rate * np.maximum(b - previous, 0.0), room)
    b -= contribution
    reserve += contribution
    return b


def _simulate(data, start_age, initial_capital, *, hedge=False, lifecycle=False,
              spreading=False, reserve=False, settings=Settings(), scenarios=None,
              longevity=False):
    s = np.arange(data.n_scen) if scenarios is None else np.atleast_1d(scenarios).astype(int)
    if len(s) == 0 or np.any(s < 0) or np.any(s >= data.n_scen):
        raise ValueError("Select at least one existing scenario")
    if not settings.entry_age <= start_age <= settings.retirement_age:
        raise ValueError("Current/entry age must be between entry and retirement ages")
    acc = max(settings.retirement_age - start_age, 0)
    data.require_horizon(acc + settings.pay_years - 1)
    equity, infl_nl = data.arrays["equity"], data.arrays["infl_nl"]

    def allocate(t, age):
        eq = equity[s, t]
        w = exposure(age, settings) if lifecycle else 1.0
        h = hedge_ratio(age, settings) if hedge else 0.0
        risky = w * eq + (1.0 - w) * (risk_free_1y(data, t, s) if w < 1.0 else 0.0)
        if h > 0.0:
            return h * protection_return(data, t, s, liability_duration(age, settings)) + (1.0 - h) * risky
        return risky

    capital = np.full(len(s), initial_capital, dtype=float)
    for t in range(acc):
        capital = (capital + settings.contribution) * (1.0 + allocate(t, start_age + t))
    factor = annuity_factor(settings.projection, settings.pay_years)
    if longevity:
        surv, survival = 1.0, []
        for k in range(settings.pay_years):
            survival.append(surv)
            surv *= 1.0 - mortality_rate(settings.retirement_age + k)
        factor = np.sum(np.array(survival) * (1.0 + settings.projection) **
                        (-np.arange(1, settings.pay_years + 1)))
    benefit = np.empty((len(s), settings.pay_years))
    benefit[:, 0] = capital / factor
    pending = np.zeros((len(s), max(int(settings.spread_years), 1)))
    res = np.zeros(len(s))
    for k in range(1, settings.pay_years):
        t = acc + k - 1
        allocated = allocate(t, settings.retirement_age + k - 1)
        if longevity:
            q = mortality_rate(settings.retirement_age + k - 1)
            allocated = (1.0 + allocated) / (1.0 - q) - 1.0
        raw_shock = (1.0 + allocated) / (1.0 + settings.projection) - 1.0
        applied = spread_update(pending, k, raw_shock) if spreading else raw_shock
        b = benefit[:, k - 1] * (1.0 + applied)
        if reserve:
            b = reserve_update(b, benefit[:, k - 1], res, settings.fill_rate, settings.reserve_cap)
        benefit[:, k] = b
    price_level = np.cumprod(1.0 + infl_nl[s], axis=1)
    pay_data_years = acc + np.arange(settings.pay_years)
    # Retain A.10/A.11's year-end index, including -1 when acc == 0.
    return benefit, benefit / price_level[:, pay_data_years - 1]


def run(data, hedge=False, lifecycle=False, spreading=False, reserve=False, *,
        entry_age=25, settings=Settings(), scenarios=None):
    """A.10: start with zero capital at entry_age (no deterministic history)."""
    return _simulate(data, entry_age, 0.0, hedge=hedge, lifecycle=lifecycle,
                     spreading=spreading, reserve=reserve, settings=settings, scenarios=scenarios)


def run_grid(data, start_age, hedge=False, lifecycle=False, spreading=False, reserve=False, *,
             settings=Settings(), scenarios=None):
    """A.11: current cohort seeded at the fixed historical projection return."""
    return _simulate(data, start_age, accumulated_to(start_age, settings), hedge=hedge,
                     lifecycle=lifecycle, spreading=spreading, reserve=reserve,
                     settings=settings, scenarios=scenarios)


def run_baseline(data, *, settings=Settings(), scenarios=None):
    """A.3 baseline entry cohort; all damping switches off."""
    return run(data, entry_age=settings.entry_age, settings=settings, scenarios=scenarios)


def run_with_spreading(data, spread_years=5, *, settings=Settings(), scenarios=None):
    return run(data, spreading=True, entry_age=settings.entry_age,
               settings=replace(settings, spread_years=spread_years), scenarios=scenarios)


def run_with_reserve(data, fill_rate=0.25, cap=2.0, *, settings=Settings(), scenarios=None):
    return run(data, reserve=True, entry_age=settings.entry_age,
               settings=replace(settings, fill_rate=fill_rate, reserve_cap=cap), scenarios=scenarios)


def run_with_hedge(data, *, settings=Settings(), scenarios=None):
    return run(data, hedge=True, entry_age=settings.entry_age, settings=settings, scenarios=scenarios)


def run_with_lifecycle(data, *, settings=Settings(), scenarios=None):
    return run(data, lifecycle=True, entry_age=settings.entry_age, settings=settings, scenarios=scenarios)


def run_with_projection(data, projection, *, settings=Settings(), scenarios=None):
    """A.8: projection changes conversion AND payout updates; no damping flags."""
    return run_baseline(data, settings=replace(settings, projection=projection), scenarios=scenarios)


def mortality_rate(age):
    """A.9's illustrative mortality, not a calibrated actuarial life table."""
    return float(np.clip(0.005 * 2 ** ((age - 65) / 9.0), 0.0, 1.0))


def run_with_longevity(data, *, settings=Settings(), scenarios=None):
    return _simulate(data, settings.entry_age, 0.0, settings=settings, scenarios=scenarios, longevity=True)
