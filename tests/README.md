# tests/

pytest suite covering real functionality, not padding.

- Unit tests for ingestion helpers (config parsing, retry logic, metadata tracking)
- Unit tests for PySpark transformation logic (deduplication, null handling, validation rules) using local Spark sessions and small fixture DataFrames
- Data quality tests validating Bronze/Silver/Gold outputs (row counts, uniqueness, referential integrity)
- dbt tests (`not_null`, `unique`, `relationships`, `accepted_values`) live in `dbt/tests` and are run via `dbt test`, not duplicated here
