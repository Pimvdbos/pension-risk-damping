# Optional large input data

No DNB workbook or scenario array is distributed here. The report-data figures work
without it. To run simulations:

```bash
python scripts/download_data.py
pension-risk analyze --scenarios 256 --extensions
```

The download is 179,115,782 bytes. `data/raw/` holds the workbook and `data/cache/`
holds source-bound parsed NPZ arrays; both are ignored. A manual local workbook is
accepted with `--workbook`. See [acquisition, schema and DNB reuse terms](../docs/data_provenance.md)
and [actual provenance manifest](provenance.json).
