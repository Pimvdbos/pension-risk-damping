from dataclasses import replace
from itertools import product

import numpy as np
import pytest

from pension_risk.config import Settings
from pension_risk.curves import exposure, hedge_ratio, protection_return
from pension_risk.engines import (annuity_factor, reserve_update, run, run_baseline,
                                  run_grid, spread_update)
from pension_risk.metrics import level_cov, yoy_vol
from pension_risk.shapley import coalitions, shapley_values


def test_one_year_capital_contribution_before_return(artificial_data):
    cfg = replace(Settings(), entry_age=67, retirement_age=68, end_age=69)
    nominal, real = run_baseline(artificial_data, settings=cfg)
    capital = 1.0 * (1.0 + artificial_data.arrays["equity"][:, 0])
    np.testing.assert_allclose(nominal[:, 0], capital * 1.03)
    np.testing.assert_allclose(real[:, 0], nominal[:, 0] / (1 + artificial_data.arrays["infl_nl"][:, 0]))
    assert annuity_factor(0.03, 1) == pytest.approx(1 / 1.03)


def test_flat_zero_coupon_holding_return_and_rounding(artificial_data):
    np.testing.assert_allclose(protection_return(artificial_data, 0, [0, 1], 12.5), 0.02)
    # Python round(12.5) -> 12, round(13.5) -> 14. A sloped curve exposes maturity choice.
    artificial_data.arrays["phi_N"][:] = 0
    artificial_data.arrays["phi_N"][11, 0] = -0.5
    expected = np.exp(0.5) - 1  # P(1,11)=1, P(0,12)=exp(-0.5)
    assert protection_return(artificial_data, 0, [0], 12.5)[0] == pytest.approx(expected)


def test_shock_slice_current_timing_and_expiry():
    pending = np.zeros((1, 5))
    assert spread_update(pending, 1, np.array([0.5]))[0] == pytest.approx(0.1)
    for k in range(2, 6):
        assert spread_update(pending, k, np.zeros(1))[0] == pytest.approx(0.1)
    assert spread_update(pending, 6, np.zeros(1))[0] == 0


def test_reserve_cash_flow_bounds_and_previous_benefit_cap():
    res = np.array([0.0, 3.0, 1.0])
    raw, previous = np.array([14.0, 8.0, 5.0]), np.array([10.0, 10.0, 10.0])
    old = res.copy()
    paid = reserve_update(raw, previous, res)
    np.testing.assert_allclose(paid, [13, 10, 6])
    np.testing.assert_allclose(res, [1, 1, 0])
    np.testing.assert_allclose(paid + res, raw + old)
    capped = np.array([19.8])
    assert reserve_update(np.array([14.0]), np.array([10.0]), capped)[0] == pytest.approx(13.8)
    assert capped[0] == pytest.approx(20.0)


def test_all_off_against_independent_baseline_recurrence(artificial_data):
    eq, infl = artificial_data.arrays["equity"], artificial_data.arrays["infl_nl"]
    capital = np.zeros(eq.shape[0])
    for t in range(43):
        capital = (capital + 1) * (1 + eq[:, t])
    expected = np.empty((eq.shape[0], 27))
    expected[:, 0] = capital / np.sum(1.03 ** -np.arange(1, 28))
    for k in range(1, 27):
        expected[:, k] = expected[:, k - 1] * (1 + eq[:, 43 + k - 1]) / 1.03
    nominal, real = run(artificial_data)
    np.testing.assert_allclose(nominal, expected)
    np.testing.assert_allclose(real, expected / np.cumprod(1 + infl, axis=1)[:, np.arange(42, 69)])
    np.testing.assert_allclose(run_grid(artificial_data, 25)[0], nominal)


def test_profiles_match_appendix_endpoints():
    assert [hedge_ratio(a) for a in (25, 45, 68, 95)] == [0, 0, 1, 1]
    assert exposure(35) == 1
    assert exposure(68) == pytest.approx(0.56)
    assert exposure(95) == pytest.approx(0.2)


def test_metric_aggregation_population_std():
    values = np.array([[1., 2., 6.], [3., 3., 3.]])
    assert level_cov(values) == pytest.approx(np.median([0.5, 0.2, 1/3]))
    # Relative changes: [1,2] and [0,0]; population stds .5 and 0; median .25.
    assert yoy_vol(values) == pytest.approx(0.25)


def test_shapley_known_interaction_and_efficiency():
    players = ("a", "b", "c", "d")
    def value(s):
        return sum({"a": 2, "b": 3, "c": 5, "d": 7}[x] for x in s) + (4 if {"a", "b"} <= s else 0)
    values = {s: value(s) for s in coalitions(players)}
    phi = shapley_values(values, players)
    assert phi == pytest.approx({"a": 4, "b": 5, "c": 5, "d": 7})
    assert sum(phi.values()) == pytest.approx(values[frozenset(players)])


def test_engine_coalitions_are_finite_on_artificial_fixture(artificial_data):
    for flags in product((False, True), repeat=4):
        nominal, real = run_grid(artificial_data, 45, *flags)
        assert nominal.shape == real.shape == (6, 27)
        assert np.isfinite(real).all()


def test_insufficient_curve_time_coverage_fails(artificial_data):
    artificial_data.arrays["s1"] = artificial_data.arrays["s1"][:, :3]
    with pytest.raises(ValueError, match="s1 needs"):
        run(artificial_data)
