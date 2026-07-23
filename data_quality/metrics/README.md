# data_quality/metrics/

Generated data-quality metrics from the Silver pipeline. Every Silver run
writes one JSON file per dataset here, populated ONLY from real pipeline
execution (see `pyspark/src/writers.py` and `transformations.py`) -
no metric is ever hard-coded or estimated.

Two files are written per dataset:

- `<dataset>_latest.json` - overwritten each run, for quick inspection.
- `<dataset>_YYYYMMDDTHHMMSSZ.json` - a timestamped historical record.

Metrics captured include (dataset-dependent):

- `input_count` / `output_count`
- `exact_duplicate_rows_removed` and `business_key_duplicates_removed`
- `quarantined_count` and a per-reason `quarantine_reason_breakdown`
- `referential_integrity_failures` (claims: bad member/provider/diagnosis refs)
- `late_arriving_count` (claims)
- `providers_with_historical_versions_preserved` (providers, for future SCD2)
- null-count and flag summaries

## Generated, not source-controlled

The JSON metric files are build artifacts and are git-ignored (see
`.gitignore`); only this README is tracked. Regenerate them locally:

```
python -m pyspark.src.silver_pipeline --all
```

All data is synthetic.
