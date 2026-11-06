"""Plot supplied report Tables 2 and 4, without the DNB workbook or simulations."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NAVY, TEAL, TEXT, GRID = "#253d58", "#16827c", "#243344", "#e4e9ee"


def style(ax):
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0, pad=8, colors=TEXT)


def save(fig, name, source):
    fig.text(0.10, 0.025, source + " · Reported values; not a new simulation run.",
             fontsize=9, color="#5b6775")
    out = ROOT / "assets/figures"
    out.mkdir(parents=True, exist_ok=True)
    for extension in ("svg", "png"):
        path = out / f"{name}.{extension}"
        fig.savefig(path, dpi=180, facecolor="white", metadata={"Date": None} if extension == "svg" else None)
        if extension == "svg":
            path.write_text("\n".join(line.rstrip() for line in path.read_text(encoding="utf-8").splitlines())
                            + "\n", encoding="utf-8")
    plt.close(fig)


def main():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "text.color": TEXT, "axes.labelcolor": TEXT,
                         "svg.fonttype": "none", "svg.hashsalt": "pension-risk-damping"})
    cohort = pd.read_csv(ROOT / "results/reported/table4_baseline_full.csv")
    fig, ax = plt.subplots(figsize=(10, 5.3))
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.19, top=0.80)
    fig.text(0.10, 0.93, "Lower level uncertainty across all five cohorts", fontsize=17, weight="bold")
    fig.text(0.10, 0.875, "Baseline versus all four damping mechanisms · Real-benefit coefficient of variation", fontsize=11)
    x, width = np.arange(len(cohort)), 0.32
    for shift, column, label, color in [(-width/2, "baseline_level_cov", "Baseline", NAVY),
                                         (width/2, "full_level_cov", "Full model", TEAL)]:
        bars = ax.bar(x + shift, cohort[column], width, label=label, color=color)
        ax.bar_label(bars, fmt="%.3f", padding=5, fontsize=10, color=TEXT)
    ax.set_xticks(x, cohort.current_age.astype(str))
    ax.set_xlabel("Current cohort age")
    ax.set_ylabel("Level CoV (dimensionless)")
    ax.set_ylim(0, 1.40)
    style(ax)
    ax.legend(frameon=False, loc="upper right", ncols=2)
    save(fig, "reported_cohort_cov", "Source: original report, Table 4")

    shares = pd.read_csv(ROOT / "results/reported/table2_shapley_shares.csv")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    fig.subplots_adjust(left=0.22, right=0.96, bottom=0.22, top=0.76)
    fig.text(0.10, 0.93, "The leading mechanism depends on the risk metric", fontsize=17, weight="bold")
    fig.text(0.10, 0.875, "Age 45 · Shapley shares of the combined reduction (%)", fontsize=11)
    y, height = np.arange(len(shares)), 0.32
    for shift, column, label, color in [(-height/2, "level_age45_percent", "Level dispersion", NAVY),
                                         (height/2, "yoy_age45_percent", "YoY payout volatility", TEAL)]:
        bars = ax.barh(y + shift, shares[column], height, label=label, color=color)
        ax.bar_label(bars, fmt="%.1f%%", padding=6, fontsize=10, color=TEXT)
    ax.set_yticks(y, shares.mechanism)
    ax.invert_yaxis()
    ax.set_xlim(0, 66)
    ax.set_xlabel("Share of combined risk reduction (%)")
    style(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(-0.02, 1.015), ncols=2)
    save(fig, "reported_shapley_age45", "Source: original report, Table 2 (rounding retained)")


if __name__ == "__main__":
    main()
