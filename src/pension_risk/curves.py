"""A.2, A.6, A.7: reconstructed annual effective yields and bond returns."""

import numpy as np

from .config import Settings


def curve(data, phi, psi, t, maturities, scenarios):
    maturities = np.atleast_1d(maturities)
    if np.any(maturities < 1) or np.any(maturities != maturities.astype(int)):
        raise ValueError("Curve maturities must be positive integer years")
    idx = maturities.astype(int) - 1
    if np.max(idx) >= phi.shape[0] or not 0 <= t < phi.shape[1]:
        raise ValueError("Curve time/maturity is outside workbook coverage")
    states = np.stack([data.arrays[k][scenarios, t] for k in ("s1", "s2", "s3")], axis=1)
    return np.exp((-1.0 / maturities)[None, :] *
                  (phi[idx, t][None, :] + states @ psi[idx, :].T)) - 1.0


def nominal_curve(data, t, maturities, scenarios):
    return curve(data, data.arrays["phi_N"], data.arrays["Psi_N"], t, maturities, scenarios)


def real_curve_nl(data, t, maturities, scenarios):
    return curve(data, data.arrays["phi_R_NL"], data.arrays["Psi_R"], t, maturities, scenarios)


def hedge_ratio(age, settings=Settings()):
    return float(np.clip((age - 45) / (settings.retirement_age - 45), 0.0, 1.0))


def liability_duration(age, settings=Settings()):
    return max(max(settings.end_age - age, 1) / 2.0, 1.0)


def exposure(age, settings=Settings()):
    return float(np.clip(1.0 - 0.8 * (age - 35) / (settings.end_age - 35), 0.2, 1.0))


def discount(data, t, maturity, scenarios):
    if maturity <= 0:
        return np.ones(len(np.atleast_1d(scenarios)))
    return (1.0 + nominal_curve(data, t, [maturity], scenarios)[:, 0]) ** (-maturity)


def protection_return(data, t, scenarios, duration):
    # Python's int(round(...)) is intentional, including ties-to-even rounding.
    d = int(round(duration))
    return discount(data, t + 1, d - 1, scenarios) / discount(data, t, d, scenarios) - 1.0


def risk_free_1y(data, t, scenarios):
    return nominal_curve(data, t, [1], scenarios)[:, 0]
