# pyspark/

Standalone PySpark job scripts used by the Silver and Gold processing stages (invoked directly for local development, and by Airflow in the full pipeline).

Demonstrates real PySpark usage (Milestone 3): DataFrame joins, window functions for deduplication, aggregations, null handling, explicit schema/type management, partitioning strategy, and a deliberate, justified use of broadcast joins and caching where they actually help (not added just to pad a resume).
