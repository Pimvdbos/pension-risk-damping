"""Figures from committed, full-data replication summaries; no workbook needed."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

from plot_reported_results import NAVY, TEAL, TEXT, GRID, style

ROOT = Path(__file__).resolve().parents[1]
COLORS = {"Baseline": NAVY, "Protection": "#70609b", "Lifecycle": "#a5682a",
          "Spreading": "#3886ad", "Reserve": "#a55c76", "Full model": TEAL}
CONFIGS = {"Baseline": "baseline", "Protection": "hedge", "Lifecycle": "lifecycle",
           "Spreading": "spreading", "Reserve": "reserve", "Full model": "hedge+lifecycle+reserve+spreading"}


def save(fig, path, note):
    fig.text(0.09, 0.045, "Source: full 20,000-scenario replication, unshocked DNB P-set 2026Q2.", fontsize=9, color="#5b6775")
    fig.text(0.09, 0.018, note, fontsize=9, color="#5b6775")
    for extension in ("png", "svg"):
        target = path.with_suffix(f".{extension}")
        fig.savefig(target, dpi=180, facecolor="white", metadata={"Date": None} if extension == "svg" else None)
        if extension == "svg":
            target.write_text("\n".join(x.rstrip() for x in target.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "results/replication/2026q2")
    parser.add_argument("--output", type=Path, default=ROOT / "assets/figures")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "text.color": TEXT,
                         "axes.labelcolor": TEXT, "svg.fonttype": "path", "svg.hashsalt": "pension-replication"})
    metrics = pd.read_csv(args.input / "coalition_metrics.csv")
    cohort = metrics[metrics.age == 45].set_index("coalition")
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 6.2), sharey=True)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.80, bottom=0.30, wspace=0.15)
    fig.text(0.09, 0.93, "Age 45: risk and expected benefits", fontsize=18, weight="bold")
    fig.text(0.09, 0.875, "All 16 configurations; six highlighted policies. Lower risk is further left.", fontsize=11)
    for ax, metric, label in zip(axes, ("CoV", "YoY"), ("Level CoV (dimensionless)", "YoY volatility (dimensionless)")):
        ax.scatter(cohort[metric], cohort.Mean, s=45, color="#a6afb8", alpha=0.7, zorder=2)
        for name, coalition in CONFIGS.items():
            row = cohort.loc[coalition]
            ax.scatter(row[metric], row.Mean, s=90, color=COLORS[name], edgecolor="white", linewidth=0.8, zorder=3)
        ax.set_xlabel(label)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        style(ax)
    axes[0].set_ylabel("Mean real benefit (annual contribution units)")
    handles = [Line2D([], [], color=c, marker="o", linestyle="None", label=n, markersize=8) for n, c in COLORS.items()]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.11), ncols=3, frameon=False)
    save(fig, args.output / "replicated_risk_benefit_age45", "Mean averages the real-benefit array; these are policy comparisons, not an optimized frontier.")

    quantiles = pd.read_csv(args.input / "benefit_quantiles_age45.csv")
    fig, ax = plt.subplots(figsize=(10, 5.8))
    fig.subplots_adjust(left=0.09, right=0.98, top=0.79, bottom=0.19)
    fig.text(0.09, 0.93, "Age 45: distribution of real retirement payments", fontsize=17, weight="bold")
    fig.text(0.09, 0.875, "Baseline and full model across 20,000 economic scenarios", fontsize=11)
    handles = []
    for name, color in (("Baseline", NAVY), ("Full model", TEAL)):
        q = quantiles[quantiles.configuration == name]
        ax.fill_between(q.payment_number, q.p5, q.p95, color=color, alpha=0.16)
        line, = ax.plot(q.payment_number, q["median"], color=color, linewidth=2, label=f"{name} median")
        handles.append(line)
    handles.append(Patch(facecolor="#b6c0ca", alpha=0.35, label="Shaded: pointwise P5-P95"))
    ax.legend(handles=handles, frameon=False, loc="upper right", fontsize=10)
    ax.set_xlabel("Retirement payment number")
    ax.set_ylabel("Real benefit (annual contribution units)")
    ax.set_xticks([1, 5, 10, 15, 20, 27])
    ax.set_xlim(1, 27)
    ax.set_ylim(bottom=0)
    style(ax)
    save(fig, args.output / "replicated_benefit_distribution_age45", "Pointwise scenario quantiles show outcome dispersion; they are not confidence intervals.")

    stability = pd.read_csv(args.input / "scenario_prefix_stability.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.5))
    fig.subplots_adjust(left=0.09, right=0.98, top=0.78, bottom=0.22, wspace=0.27)
    fig.text(0.09, 0.93, "Age 45: sensitivity to the number of scenarios", fontsize=17, weight="bold")
    fig.text(0.09, 0.875, "Nested first-N subsets from the same DNB release", fontsize=11)
    for ax, metric, ylabel in zip(axes, ("CoV", "YoY"), ("Level CoV", "YoY volatility")):
        rows = stability[stability.metric == metric]
        for column, label, color in (("baseline_risk", "Baseline", NAVY), ("full_risk", "Full model", TEAL)):
            ax.plot(rows.scenarios, rows[column], color=color, marker="o", label=label)
        ax.set_xscale("log")
        ax.set_xticks(rows.scenarios, [f"{n/1000:g}k" for n in rows.scenarios])
        ax.set_xlabel("Number of scenarios")
        ax.set_ylabel(ylabel + " (dimensionless)")
        ax.set_ylim(bottom=0)
        ax.legend(frameon=False, fontsize=10)
        style(ax)
    save(fig, args.output / "replicated_prefix_stability", "Nested subsets are dependent; this diagnostic does not estimate a Monte Carlo confidence interval.")


if __name__ == "__main__":
    main()
