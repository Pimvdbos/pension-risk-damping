# Generated calculations

The analysis CLI writes demonstration or full-run tables here, in separate folders,
with `provenance.json` (source SHA-256, selection, parameters and implementation hash)
and `coalition_summaries.json`. These outputs are ignored by Git. Summary reuse requires
the same provenance; the same cohort/coalition is not simulated separately for each table
or metric.

The published report values remain under [`../reported/`](../reported/README.md).
Subset outputs are software demonstrations and are not published estimates. A full
20,000-scenario workflow and numerical audit have subsequently completed. Its compact,
reviewed [replication snapshot](../replication/2026q2/README.md) is explicitly committed
outside this ignored working-output directory. The workbook and large arrays remain
excluded from Git.
