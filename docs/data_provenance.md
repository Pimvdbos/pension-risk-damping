# DNB data acquisition and schema

The only supported research workbook is **CP2022 P scenarioset, 20K, 2026Q2,
unshocked**, released 14 April 2026. This project does not use Q-scenarios, a
shocked-rate variant, 100K files or a later quarter.

- [Official publication page](https://www.dnb.nl/voor-de-sector/open-boek-toezicht/sectoren/pensioenfondsen/dnb-publiceert-definitieve-scenariosets-bij-wet-toekomst-pensioenen/)
- [Exact workbook](https://www.dnb.nl/media/4xzlqaij/cp2022-p-scenarioset-20k-2026q2.xlsx)
- [DNB archive](https://www.dnb.nl/archief/) for older releases if the main page changes
- [Actual retrieval manifest](../data/provenance.json)

Retrieved 6 November 2026 with HTTP 200 and XLSX content type. File size:
**179,115,782 bytes** (170.8 MiB). SHA-256:
`275a336f4bc121fcd2948f3c40e3bc4fd154e5279fcdee472e491720565c658b`.
The response's Last-Modified date was 14 April 2026. This is a fresh public-source
download for packaging; it is not access to the author's lost original local copy.

## Acquisition

After installing the project, run `python scripts/download_data.py` or
`pension-risk download`. Both explicitly download to `data/raw/` and record a
manifest. They refuse to overwrite an existing file. The downloader uses system
`curl` if available, otherwise Python's standard-library HTTP client. In this
environment Python's HTTP request received 403, while curl returned 200 and
successfully acquired the exact file. No alternative URL was guessed.

For manual acquisition, follow the exact official link above, save the workbook
anywhere locally, and supply `--workbook /path/to/cp2022-p-scenarioset-20k-2026q2.xlsx`.
The local filename may differ; the **bytes must match** the recorded release hash.
If DNB changes the file, inspect the official page/archive and record a new verified
source manifest before deliberately updating the source constant; do not bypass the
check or silently substitute data.

## Inspected explanatory sheets

`Toelichting` contains three link cells and its substantive explanation as an embedded
image (`xl/media/image1.png`). `Veranderingen` contains its release notes as an image
(`image2.png`). Both were extracted and visually read. The numeric `0_Parameters`
and labeled `VoorbeeldRTS` sheets were also inspected. The explanations establish:

- Rows are scenarios; return/inflation columns are 100 projection-year intervals.
- State columns and phi columns include the initial time and total 101 points.
  The first curve is at the start of year one; the next curve is its year-end curve.
- Phi rows are maturities 1-100; Psi has three loadings on the same state variables.
- Nominal and Dutch real curves use different phi/Psi parameters but shared states.
- The rates are effective annual yields: `exp(-(phi + states @ Psi.T)/maturity)-1`.
- The P-set's phi smoothing introduced in 2024Q4 is **already incorporated** in
  the workbook and must not be applied again. No UFR is added to these curves.
- Returns are gross. DNB discusses a 20-basis-point cost correction for net-return
  applications. The printed research code uses the supplied gross equity series
  directly; this reconstruction preserves that choice without adding a cost adjustment.
- `VoorbeeldRTS` labels reference curves at T=0 and T=1, scenario 1. These sheets
  support layout/timing interpretation. The subsequent [full-data audit](replication_audit.md)
  also checked all 400 reference yields for the nominal and Dutch-real curves at these
  two times and reproduced all four report tables at published precision.

| Array | Sheet | Inspected shape |
| --- | --- | --- |
| equity | `4_Aandelenrendement` | 20000 × 100 |
| infl_nl | `6_Prijsinflatie_NL` | 20000 × 100 |
| s1/s2/s3 | `1_Toestandsvariabele_1`, `2_Toestandsvariabele_2`, `3_Toestandsvariabele_3` | each 20000 × 101 |
| phi_N | `7_Renteparameter_phi_N` | 100 × 101 |
| Psi_N | `8_Renteparameter_Psi_N` | 100 × 3 |
| phi_R_NL | `11_Renteparameter_phi_R_NL` | 100 × 101 |
| Psi_R | `10_Renteparameter_Psi_R` | 100 × 3 |

`pandas.ExcelFile(engine="calamine")` opens the workbook once and loads these nine
sheets as floats with no header. As in A.2, entirely empty rows/columns are removed.
Sheet names, finite numeric values and exact shapes are checked. The source SHA-256
also prevents a different scenario/time ordering from reusing the original cache.
No row-label columns or time-zero return columns are invented or removed.

NPZ filenames contain the complete source hash and loader schema version; embedded
metadata must match too. The loader rehashes the workbook even on cache hits. Engine
horizon checks require enough return years plus the corresponding state endpoints
for bond holding returns. Raw workbook, NPZ and large arrays remain Git-ignored.

## Attribution and reuse

Source: **De Nederlandsche Bank (DNB)**. Its [data disclaimer](https://www.dnb.nl/verantwoording/disclaimer/)
states that its databases/datasets are available under **Creative Commons Attribution
4.0 (CC BY 4.0)**, requiring source and license attribution and disclosure of changes.
See the [license](https://creativecommons.org/licenses/by/4.0/). DNB provides no
endorsement of this project. The download is stored unmodified; parsed arrays,
reconstructed curves and simulated outcomes are transformations by this project.
DNB data are third-party material and are excluded from the code license. The workbook
is linked for acquisition rather than redistributed in this repository.
