# docs/data_lineage/

Data lineage documentation: traces each column back through the medallion
layers to its original source field. All data is synthetic.

## End-to-end flow

```
SOURCE CSV
  -> PYTHON INGESTION (ingestion/)         raw strings preserved, technical metadata added
  -> BRONZE (bronze/, Parquet)             ingestion_date partitions; all columns string
  -> PYSPARK SILVER (spark_jobs/, Parquet)    typed, cleaned, deduped, validated
       |-> silver/<dataset>                records that passed validation
       |-> silver/quarantine/<dataset>     records that failed (with rejection_reason)
       +-> data_quality/metrics/           per-run JSON metrics
  -> GOLD (dbt + DuckDB)                   star schema; fact_claims, dim_member, dim_provider (SCD Type 2)
```

## Bronze -> Silver column lineage (examples)

- `silver.claims.paid_amount` (decimal) <- `bronze.claims.paid_amount`
  (string) <- source `claims_batch_*.csv`. Cast in
  `cleaners.clean_claims`; negative values quarantined.
- `silver.claims.adjustment_amount` <- `bronze.claims.adjustment_amount`
  present only in `claims_batch_2`; null for batch_1 rows (schema
  normalization via `mergeSchema` + `ensure_columns`).
- `silver.claims.is_late_arriving` / `days_late` are DERIVED in Silver
  from `service_date` and `submission_date` (not source columns).
- `silver.members.state` <- `bronze.members.state`, trimmed/upper-cased;
  invalid codes quarantined.
- `silver.providers` rows preserve each `(provider_id, effective_date)`
  version <- `bronze.providers`; this feeds the
  `gold.dim_provider` SCD Type 2 columns (for example `is_current`).
- Lineage/audit columns `ingestion_timestamp`, `source_file`,
  `file_hash` are carried unchanged from Bronze into Silver so any Silver
  row can be traced back to the exact Bronze file it came from.

## Silver -> Gold lineage (examples)

- `gold.fact_claims` <- `silver.claims` (grain preserved: one row per claim),
  with member and provider foreign keys resolved against the dimensions.
- `gold.dim_member` <- `silver.members` (one row per member).
- `gold.dim_provider` <- `silver.providers` versioned rows, exposed as SCD
  Type 2 with current/historical flags. Models are defined in
  `dbt/models/marts/` and built by dbt-duckdb directly from the Silver Parquet.
