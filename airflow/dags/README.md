# airflow/dags/

Airflow DAG definitions that orchestrate the full ClaimsLake pipeline: ingestion -> validation -> Bronze -> Silver -> Gold -> warehouse load -> data quality checks -> notification.

Built in Milestone 6. Demonstrates task dependencies, retries with backoff, failure handling/alerting, idempotent tasks (safe to re-run), and task groups used only where they genuinely simplify the DAG rather than for show.
