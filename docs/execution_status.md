# Execution status

Updated **6 November 2026** following the full-data replication and engineering audit.
Full numerical runs used Windows x64 and Python **3.12.14**. The reported CSVs and
research content remain unchanged. The public report is a 34-page portfolio edition
with original printed pagination. No model parameters were recalibrated.

## Completed numerical work

- **All 20,000 scenarios**, five cohorts and all 16 coalitions completed, generating
  both risk metrics and all seven appendix tables. Projection examples at 2.5%, 3%,
  4% and the separate illustrative-longevity example completed too.
- **93/93 numerical outcome cells** in Section 6 Tables 1-4 match the published
  rounding: 24 in Table 1, 24 in Table 2, 25 in Table 3 and 20 in Table 4.
- **All 13 recovered notebook code cells** executed on the full 20,000-scenario
  input. The committed notebook remains output-free. Its local execution log is
  ignored under `results/generated/`.
- **480 cohort/coalition metric comparisons** between notebook and package agree
  exactly in this execution. Eighteen nominal/real standalone and extension array
  comparisons pass; maximum absolute array difference is 1.82e-12, within the
  documented relative/absolute tolerance. Notebook and package Shapley values agree
  exactly.
- **400 DNB reference yields** were checked: nominal and Dutch-real curves, 100
  maturities, T=0/T=1, scenario 1. Maximum absolute difference is **2.22e-16**.
- Shapley efficiency residuals are at most **1.11e-16**. An independent enumeration
  of all 24 coalition-addition orderings agrees to **1.67e-16**.
- All nominal/real paths across the 80 cohort/coalition cases were finite and positive.
  All 320 conditional marginal risk reductions were tabulated, including the three
  small negative level-dispersion increments rather than hiding them.
- Nested first-N diagnostics at 1k/2k/5k/10k/20k scenarios were calculated without
  treating the dependent prefixes as independent samples or confidence intervals.
- Three additional figures were generated from the full-data summaries and visually
  reviewed, alongside the two original report-data figures.

The [audit report](replication_audit.md), [compact snapshot](../results/replication/2026q2/README.md),
[machine-readable verdict](../results/replication/2026q2/audit_summary.json) and
[audit provenance](../results/replication/2026q2/audit_provenance.json) provide the exact
scope, errors, source/output hashes and recorded run times. The original model has
not been silently extended or revised.

## Software and acquisition checks

- **23 tests pass**, including the six structural/comparison tests and two snapshot
  integrity checks added for this audit. Tests use artificial fixtures or compact
  recorded summaries, not a full-data CI run.
- Read the full source report, including A.1-A.13; extracted text and visually
  inspected damaged listings and the four main-report tables. The portfolio edition
  preserves the research pages and original printed pagination. Its SHA-256 is
  recorded in the audit provenance.
- Downloaded the exact unshocked DNB P 20K 2026Q2 workbook (HTTP 200,
  179,115,782 bytes) and recorded its actual checksum. Read its explanatory images,
  inspected sheet names/layout/time indexing and exercised source-bound NPZ caching.
- A fresh environment installed the pinned lock and then the local editable package
  with `python -m pip install --no-deps -e .`. Initial software checks passed in both
  development and fresh environments. Earlier 32/256-scenario demonstrations were
  subsequently superseded by the full-data evidence above.
- Tests cover annuity/contribution timing, bond returns, integer rounding, shock
  slices, reserve conservation/cap, independent baseline recurrence, profiles/metrics,
  known Shapley interactions, notebook/package agreement, source/layout rejection,
  notebook validity, local links, report precision, payout homogeneity under a full
  hedge, and committed snapshot/source hashes.
- Source compilation and CLI/audit help checks pass. CI regenerates all five figures
  using the committed small CSVs, without downloading DNB input or executing full
  scenario runs. The [Actions page](https://github.com/Pimvdbos/pension-risk-damping/actions)
  records hosted checks separately from the local full-data audit.

## Tested environment

[`requirements-lock.txt`](../requirements-lock.txt) pins dependencies with platform
markers. Core versions: NumPy **2.5.4**, pandas **3.1.1**, python-calamine **0.9.1**.
Plotting/testing: matplotlib **3.11.2**, nbformat **5.11.1**, pytest **9.2.0**,
IPython **9.18.1**, ipykernel **7.4.0**. Software CI runs on Ubuntu/Python 3.12;
the full 20,000-scenario numerical audit was executed locally on Windows.

## Limits on the conclusion

Numerical reproduction is demonstrated for this reconstructed model and exact input
release, at the report's displayed precision. It is not an independent external
replication from the lost original source, a validation of DNB's scenario generator,
or verification of a real fund's actuarial policy. No statistical confidence intervals,
cross-vintage robustness study, fee recalibration or new shared intergenerational
reserve model is claimed. Economic-model limits are reviewed explicitly in the audit.
