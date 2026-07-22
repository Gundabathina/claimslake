# processing/gold/

Gold layer: business-ready, dimensionally modeled data built primarily with dbt + SQL (see `dbt/`), with any supporting PySpark aggregation jobs kept here.

Produces the star schema consumed by analytics: `fact_claims`, `dim_member`, `dim_provider` (SCD Type 2), `dim_diagnosis`, `dim_date`. See `docs/data_dictionary` for full table/column definitions and grain.
