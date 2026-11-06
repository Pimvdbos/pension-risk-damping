# Supplied report results

These four CSVs transcribe **Section 6, Tables 1-4**, of the
[research report, portfolio edition](../../reports/Management_Control_Assignment.pdf). They are supplied
research findings. Separately generated [full-data replication results](../replication/2026q2/README.md)
now reproduce all 93 numerical outcome cells at the printed precision. Printed pages
10-12 correspond to PDF pages 11-13. Published decimal places and rounded totals are
preserved. Blank baseline Delta CoV represents the published dash, not zero.

| File | Reference | Units |
| --- | --- | --- |
| [table1_standalone_age45.csv](table1_standalone_age45.csv) | §6.1, Table 1, printed p.10 | Mean/Std: multiples of annual nominal contribution; CoV, Delta CoV, YoY: dimensionless |
| [table2_shapley_shares.csv](table2_shapley_shares.csv) | §6.2, Table 2, printed p.11 | Percent of the combined risk reduction, not standalone percent reduction |
| [table3_standalone_cohorts.csv](table3_standalone_cohorts.csv) | §6.3, Table 3, printed p.12 | Level CoV, dimensionless |
| [table4_baseline_full.csv](table4_baseline_full.csv) | §6.3, Table 4, printed p.12 | CoV/absolute reduction: dimensionless; reduction_percent: percent |

No values are recomputed from rounded cells. For example Table 4's published age-55
absolute reduction is 0.697; retain it even though subtracting its displayed CoVs gives
0.698. Shapley shares can sum to 99.9% or 100.1%; they are not normalized. The mean
and standard deviation aggregate the entire benefit array, so their ratio need not be
the median of year-specific CoVs.

## Main-report and appendix table mapping

Appendix A.13 has its **own** numbering:

| Main report | Related appendix output | Difference |
| --- | --- | --- |
| Table 1, standalone at age 45 | Appendix Table 1 baseline + Table 2 standalone | Main table also includes Std and YoY; appendix standalone includes Tail P95 |
| Table 2, Shapley shares | Appendix Tables 5 (values), 6 (level shares), 7 (YoY shares) | Main table shows YoY shares only at age 45 |
| Table 3, standalone CoV across cohorts | Cohort engine and individual configurations | No direct A.13 numbered equivalent |
| Table 4, baseline versus full | Appendix Table 4 | Same comparison, different displayed rounding |
| No main-report equivalent | Appendix Table 3 | Sequential additions at age 45, dependent on the chosen addition order |

The figure script reads only these CSVs. New calculations belong under
[`results/generated/`](../generated/README.md) and cannot replace these files through
the analysis CLI.
