# Full-data replication snapshot: DNB P-set 2026Q2

Generated on 6 November 2026 from all 20,000 scenarios, five cohorts and all 16
coalitions, with the unchanged appendix parameters. **93/93 published numerical
outcome cells match their printed rounding.** See the [audit report](../../../docs/replication_audit.md)
and [machine-readable verdict](audit_summary.json).

This compact snapshot contains derived summaries, not DNB workbooks, parsed scenario
arrays or individual paths. New experimental runs default to ignored `results/generated/`.
The immutable-by-convention [reported tables](../../reported/README.md) remain separate.

| File | Meaning and units |
| --- | --- |
| [reported_comparison.csv](reported_comparison.csv) | Every numerical outcome cell in report Tables 1-4; original precision, reproduced value, signed error, half rounding unit and agreement |
| [coalition_metrics.csv](coalition_metrics.csv) | All 80 age/coalition summaries; Mean/Std/P5/P95 in annual-contribution units, CoV/YoY dimensionless |
| [cohort_baseline_full.csv](cohort_baseline_full.csv) | Both risk metrics and mean benefits for baseline/full across the five cohorts; reductions in percent |
| [marginal_contributions.csv](marginal_contributions.csv) | All 320 risk-metric/coalition additions; signed reductions in dimensionless risk units |
| [pair_interactions_age45.csv](pair_interactions_age45.csv) | Pair-only reduction minus sum of standalone reductions; baseline context, dimensionless risk units |
| [shapley_checks.csv](shapley_checks.csv) | Efficiency residual and independent 24-permutation calculation errors, dimensionless risk units |
| [curve_reference_checks.csv](curve_reference_checks.csv) | DNB nominal/Dutch-real reference yield errors at T=0/T=1, scenario 1, maturities 1-100; decimal annual yields |
| [notebook_package_comparison.csv](notebook_package_comparison.csv) | 480 full-data summary comparisons, original metric units |
| [standalone_array_checks.csv](standalone_array_checks.csv) | 18 nominal/real standalone and extension array comparisons; maximum error in contribution units |
| [notebook_shapley_comparison.csv](notebook_shapley_comparison.csv) | Both metrics/five cohorts/four players; absolute Shapley error |
| [path_checks.csv](path_checks.csv) | Finiteness, positivity and extrema for each age/coalition; benefit extrema in contribution units |
| [scenario_prefix_stability.csv](scenario_prefix_stability.csv) | Nested first-N scenario metrics and Shapley shares; risk dimensionless, reductions/shares in percent |
| [benefit_quantiles_age45.csv](benefit_quantiles_age45.csv) | Pointwise P5/median/P95/mean for each of 27 retirement payments; contribution units, not confidence intervals |
| `appendix_table1_*.csv` through `appendix_table7_*.csv` | All seven A.13 result tables with the appendix's own numbering/rounding |
| [illustrative_extensions.csv](illustrative_extensions.csv) | A.8/A.9 projection/longevity examples for the age-25 entry cohort; excluded from decomposition |
| [run_provenance.json](run_provenance.json) | Data hash, parameters, selection, software versions, source identity and run timing |
| [audit_provenance.json](audit_provenance.json) | Report/input/code/output hashes, environment and audit timing |

The raw scenario matrix SHA-256 is recorded in the data/run provenance, not embedded
in each row. DNB's [separate attribution and reuse terms](../../../docs/data_provenance.md)
apply to its input data. These are project-generated transformations, not official
DNB results. Means and percentiles aggregate the full real-benefit array unless a
file explicitly indexes payment numbers. The table-numbering map is in the
[reported-results guide](../../reported/README.md).

Source-file hashes normalize text line endings to LF, as declared in the audit
manifest. Data/report/output hashes use raw bytes. This distinguishes a portable
source identity from the exact preserved PDF and numerical artifacts.

To regenerate after explicitly acquiring the data and installing development dependencies:

```bash
pension-risk analyze --full --extensions
python scripts/audit_replication.py --output results/replication/2026q2
python scripts/plot_replicated_results.py
```

The default audit output is ignored. Updating this committed snapshot is an explicit
action that refreshes hashes and evidence together; do not hand-edit generated cells.
