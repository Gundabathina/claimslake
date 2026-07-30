# docs/architecture/

Architecture documentation for ClaimsLake. All data is synthetic.

This folder complements the top-level [`README.md`](../../README.md), which contains the primary architecture overview and rendered Mermaid diagrams (high-level architecture, Bronze → Silver → Gold data flow, Airflow orchestration, and the AWS Terraform reference architecture).

Related documentation:

- Silver design rationale: [`spark_jobs/README.md`](../../spark_jobs/README.md) and [`docs/interview_guide/03_pyspark_silver.md`](../interview_guide/03_pyspark_silver.md)
- Schemas: [`docs/data_dictionary/silver_schemas.md`](../data_dictionary/silver_schemas.md)
- Column lineage: [`docs/data_lineage/`](../data_lineage/)
- Analytical SQL: [`docs/analytics_catalog.md`](../analytics_catalog.md)
- AWS reference architecture: [`terraform/README.md`](../../terraform/README.md)

## Medallion pipeline (implemented)

```
SOURCE -> PYTHON INGESTION -> BRONZE -> PYSPARK SILVER -> GOLD (dbt + DuckDB)
                                             |
                                             +--> QUARANTINE
```

The Silver stage is implemented in the `spark_jobs/` package (single
source of truth; see `spark_jobs/README.md`) and reads Bronze Parquet,
producing:

- `silver/<dataset>/` - cleaned, typed, deduplicated, validated data.
- `silver/quarantine/<dataset>/` - records that failed validation,
  retained with `rejection_reason` and `validation_timestamp`
  instead of being dropped.
- `data_quality/metrics/` - per-run JSON metrics computed from real
  execution.

The Gold stage is implemented with dbt using the dbt-duckdb adapter.
DuckDB reads the Silver Parquet outputs directly (no separate load step)
and builds a star schema: `fact_claims`, `dim_member`, and `dim_provider`
(SCD Type 2 provider history), all covered by dbt tests.

Design highlights: explicit schemas (Bronze is all-string), two-stage
deterministic deduplication, preservation of provider historical versions
for SCD Type 2, broadcast-join referential-integrity checks,
late-arriving claim flagging, claims batch-1/batch-2 schema normalization,
and date-based partitioning of the claims fact.
