# Code provenance and reconstruction

The research source is the supplied report, published here as a
[34-page portfolio edition](../reports/Management_Control_Assignment.pdf).
Original printed pagination is retained, including Appendix A.1-A.13 on pp.16-32.
The complete source document was read. Text was extracted page by page;
visual inspection checked damaged listings and all four published result tables.
The original notebook/source files were unavailable.

[`appendix_reconstructed.ipynb`](../notebooks/appendix_reconstructed.ipynb) is a
**reconstruction from the PDF**, not the original notebook or a byte-identical file.
It retains all standalone mechanisms, the two combined/cohort engines, extensions,
decomposition and table generation in A.1-A.13 order. The package is a practical
refactoring of those mechanics. No parameters were fitted to match report tables.

| Appendix | Notebook section | Maintained package / entry point |
| --- | --- | --- |
| A.1 | Environment setup | `pyproject.toml`, `requirements-lock.txt` |
| A.2 | Checked loading, arrays, nominal/Dutch real curves | `data.py`: `read_sheet`, `validate_arrays`, `load_workbook`; `curves.py`: `curve`, `nominal_curve`, `real_curve_nl`; `acquisition.py`: `download` |
| A.3 | Independent baseline recurrence and quick checks | `engines.py`: `run_baseline`, `annuity_factor` |
| A.4 | Independent spreading implementation and comparison | `engines.py`: `run_with_spreading`, `spread_update` |
| A.5 | Independent reserve implementation and comparison | `engines.py`: `run_with_reserve`, `reserve_update` |
| A.6 | Hedge ratio, duration, discounts, bond return, standalone hedge | `curves.py`: `hedge_ratio`, `liability_duration`, `discount`, `protection_return`; `engines.py`: `run_with_hedge` |
| A.7 | Lifecycle profile, one-year rate, standalone lifecycle | `curves.py`: `exposure`, `risk_free_1y`; `engines.py`: `run_with_lifecycle` |
| A.8 | Projection examples 0.025, 0.03, 0.04 | `engines.py`: `run_with_projection`; CLI `--extensions` |
| A.9 | Mortality function, survival annuity and mortality credits | `engines.py`: `mortality_rate`, `run_with_longevity`; CLI `--extensions` |
| A.10 | Zero-capital engine with four switches | `engines.py`: `run`, shared `_simulate` |
| A.11 | Seeded cohort engine, age grid, both risk metrics | `engines.py`: `accumulated_to`, `run_grid`; `config.py`: `GRID`; `metrics.py`: `level_cov`, `yoy_vol` |
| A.12 | Factorial Shapley for both metrics, efficiency check | `shapley.py`: `coalitions`, `shapley_values`, `CoalitionStudy` |
| A.13 | All seven appendix tables, including sequential addition | `tables.py`: `result_tables`; `cli.py`: `analyze`; `scripts/run_analysis.py` |

All package paths in this table are relative to [`src/pension_risk/`](../src/pension_risk/).
The [result transcription guide](../results/reported/README.md) distinguishes main
report Tables 1-4 from the appendix's different Tables 1-7.

## Transcription repairs

- Restored quotation marks for sheet names, dictionary keys, strings and f-strings.
  Restored prose headers/function descriptions as comments or triple-quoted docstrings.
  Some explanatory wording/spacing and temporary-variable layout are made readable;
  this is executable source recovery, not a facsimile of listing typography.
- Removed printed line numbers, continuation arrows, page headers/footers and joined
  wrapped statements within parentheses. Restored spaces, indentation and control-flow
  blocks that were lost in text extraction.
- Restored `~` in the NaN masks, `**` for powers, ordinary minus signs and valid
  `if ... else`, membership tests, comprehensions, dictionary expansion and factorial
  weights. Mathematical `^` in prose remains explanation, not Python exponentiation.
- Reconstructed print labels from context. They are diagnostic text, not analytical
  assumptions. Split semicolon statements into separate lines for readability.
- Kept the implementation's ring-buffer timing despite the “next N years” prose;
  current slices are included. Kept age-95 lifecycle endpoint, population standard
  deviations, payout/deflator indices, and integer bond-maturity rounding.
- The clipped Colab workbook path is replaced by the verified public filename and
  configurable local paths. No claim is made to recover the original local path/file.

## Engineering adaptations

- A.1's bare notebook `pip install` becomes installation instructions for an isolated
  local environment; unused SciPy is omitted. Notebook A.2 retains its numeric reader,
  NPZ block, original array names and explicit curve functions, with added source-hash
  and shape-validation helpers from the package. Google Drive mounting is removed.
- The original A.2 cache was keyed only by its local filename. New caches use the
  workbook SHA-256, loader schema and embedded metadata. Calamine reads the nine
  sheets once; sheet names, exact layout, horizon and numeric finiteness are checked.
- Notebook defaults select the first 256 scenarios as a labeled demonstration.
  `PENSION_SCENARIOS=all` selects all input scenarios. The practical full workflow
  is the CLI `--full` command. No notebook outputs are prefilled or fabricated.
- Notebook standalone implementations remain independent. The maintained package
  shares accumulation, conversion, payout and deflation loops; standalone API functions
  set their respective switches. A.10 and A.11 retain distinct initial-capital rules.
  The package's raw-shock update is algebraically equivalent to baseline pass-through;
  small floating-point rounding differences are possible after refactoring.
- Projection and longevity API functions share bookkeeping but remain separate
  illustrations, excluded from `MECHS`. A.9's survival-weighted conversion and
  per-survivor credit are both preserved, without extending its economic interpretation.
- `Settings` centralizes constants. Historical cohort capital uses its fixed 3%
  setting; the main workflow uses the printed parameter values. New research outputs
  include parameters, source hash and implementation hash and cannot overwrite the
  reported tables through the CLI.
- `CoalitionStudy` caches compact descriptives for each age/coalition. All table
  columns and both metrics reuse them. Persisted summaries are reused only with
  identical input/parameters/selection/implementation. No large paths are committed.

## Preserved boundaries and unresolved scope

There is no unresolved substantive ambiguity for the requested cohort grid. The
printed `run_grid` formula would use deflator index -1 at a start age of 68; that
edge lies outside the study's 25/35/45/55/67 grid. The code retains that indexing
instead of inventing a revised retirement-year convention. The package rejects
start ages beyond retirement rather than imply support for already-retired cohorts.

The report sometimes describes cohort YoY volatility as identical. Its functions
calculate each cohort separately, and its results mention minor variations. This
project describes them as broadly similar, without modifying values or forcing equality.
The reserve remains an own-buffer proxy and provides no transfer accounting.

Initial packaging checks concerned installation and software mechanics. Subsequently,
the full 20,000-scenario workflow and recovered notebook were executed and audited
against all four supplied tables. The simulator, research parameters and reported
values were preserved. Added analysis is in `replication.py`, `scripts/audit_replication.py`
and `scripts/plot_replicated_results.py`; compact generated evidence is separate from
the report transcriptions. Source hashing now normalizes text newlines for portability,
and run provenance includes the environment and completion timing. See the
[audit](replication_audit.md) and [execution status](execution_status.md).
