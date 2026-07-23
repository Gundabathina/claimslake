# processing/silver/

Conceptual placeholder for the Silver processing stage. This directory
was scaffolded in Milestone 0 to describe the medallion stages; the
ACTUAL Silver implementation lives in the `pyspark/` package.

- Silver code (source of truth): `pyspark/src/` (see `pyspark/README.md`)
- Silver output (generated): `silver/`
- Rejected records: `silver/quarantine/`
- Data-quality metrics: `data_quality/metrics/`
- Tests: `tests/pyspark/`
- Interview Q&A: `docs/interview_guide/03_pyspark_silver.md`

Run the Silver layer with:

```
python -m pyspark.src.silver_pipeline --all
```

Responsibilities implemented (Milestone 3): data cleaning and type
standardization, deterministic deduplication, business-rule validation,
referential-integrity checks, quarantining of invalid records (with
reasons, not silent drops), late-arriving claim identification, claims
batch-1/batch-2 schema normalization, preservation of provider history
for future SCD Type 2, and real data-quality metrics.

This README is kept as a pointer only, to avoid two competing
descriptions of the Silver layer. All data is synthetic.
