# dbt/

dbt project that builds the Gold-layer star schema on top of the local warehouse (DuckDB/Postgres).

Why dbt on top of PySpark: PySpark handles the heavier, less structured Bronze-to-Silver cleaning where full DataFrame/RDD control is valuable, while dbt owns the Silver-to-Gold SQL modeling layer, where its built-in testing, documentation, dependency graph (`dbt docs generate`), and version-controlled SQL transformations are a better fit than hand-written Spark jobs.

Will include (Milestone 4): sources, staging models, intermediate models, marts (facts/dimensions), an SCD Type 2 provider dimension, and `not_null`/`unique`/`relationships`/`accepted_values` tests.
