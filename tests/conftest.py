"""Artificial fixtures for software tests only; never research evidence."""
import numpy as np
import pytest
from pension_risk.data import ScenarioData


@pytest.fixture
def artificial_data():
    rng = np.random.default_rng(2026)
    n, years, maturities = 6, 75, 100
    arrays = {"equity": rng.uniform(-0.15, 0.25, (n, years)),
              "infl_nl": rng.uniform(0.0, 0.04, (n, years)),
              **{k: np.zeros((n, years + 1)) for k in ("s1", "s2", "s3")}}
    # Flat annual effective nominal/real rate of 2%; all state loadings are zero.
    phi = -np.arange(1, maturities + 1)[:, None] * np.log(1.02)
    arrays.update(phi_N=np.repeat(phi, years + 1, axis=1),
                  phi_R_NL=np.repeat(phi, years + 1, axis=1),
                  Psi_N=np.zeros((maturities, 3)), Psi_R=np.zeros((maturities, 3)))
    return ScenarioData(arrays, {"fixture": "artificial, not DNB"})
