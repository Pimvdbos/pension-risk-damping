"""A.11: two distinct aggregations, both with NumPy population std (ddof=0)."""
import numpy as np


def yoy_vol(real):
    return float(np.median(np.std(np.diff(real, axis=1) / real[:, :-1], axis=1, ddof=0)))


def level_cov(real):
    return float(np.median(np.std(real, axis=0, ddof=0) / np.mean(real, axis=0)))


def describe(real):
    return {"Mean": float(np.mean(real)), "Std": float(np.std(real, ddof=0)),
            "CoV": level_cov(real), "YoY": yoy_vol(real),
            "P5": float(np.percentile(real, 5)), "P95": float(np.percentile(real, 95))}
