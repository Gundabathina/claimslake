# Airflow orchestration — ClaimsLake

A single DAG, `claimslake_pipeline`, orchestrates the existing pipeline as five
Airflow tasks. It **reuses the production entry points** from
`scripts/run_pipeline.py` (Bronze ingestion, Silver PySpark, Gold dbt build) —
no business logic is duplicated in the DAG.

## Task graph

```
check_prerequisites
    → bronze_ingestion
    → silver_processing
    → gold_dbt_build
    → validate_outputs
```

`validate_outputs` fails the run unless every expected artifact exists: Bronze
Parquet, Silver `members/providers/diagnoses/claims` Parquet, quarantine output,
metrics JSON, and `gold/claimslake.duckdb`.

## Configuration (environment variables)

| Variable | Purpose | Default |
| --- | --- | --- |
| `CLAIMSLAKE_REPO_ROOT` | Repo root (must be importable) | inferred from DAG file |
| `CLAIMSLAKE_BRONZE` | Bronze output dir | `<root>/bronze` |
| `CLAIMSLAKE_SILVER` | Silver output dir | `<root>/silver` |
| `CLAIMSLAKE_QUARANTINE` | Quarantine dir | `<silver>/quarantine` |
| `CLAIMSLAKE_METRICS` | Metrics JSON dir | `<root>/data_quality/metrics` |
| `CLAIMSLAKE_DUCKDB_PATH` | Gold DuckDB file | `<root>/gold/claimslake.duckdb` |
| `DBT_PROFILES_DIR` | dbt profiles dir | `<root>/dbt` |

## Install (isolated environment)

Airflow is intentionally kept out of `requirements.txt`. Install it separately:

```bash
python -m venv .venv-airflow && source .venv-airflow/bin/activate
pip install "apache-airflow==2.9.3" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.11.txt"
# plus the pipeline's own runtime deps so the tasks can execute:
pip install -r requirements.txt -r dbt/requirements-dbt.txt
pip install pyspark==4.0.0
```

## Run locally

```bash
# 1. Point Airflow at this repo and its dags folder.
export AIRFLOW_HOME="$(pwd)/.airflow"
export CLAIMSLAKE_REPO_ROOT="$(pwd)"
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/airflow/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False

# 2. Initialise the metadata DB (first run only).
airflow db migrate

# 3a. Easiest: single-process standalone (scheduler + webserver + triggerer).
airflow standalone
#    UI at http://localhost:8080 (login shown in the console output).

# 3b. Or run components separately:
#     airflow scheduler
#     airflow webserver --port 8080

# 4. Verify the DAG imports and is registered.
airflow dags list                       # should list claimslake_pipeline
airflow dags list-import-errors         # should print "No data found" / be empty
python airflow/dags/claimslake_pipeline.py   # parses the file directly; no output = OK

# 5. Trigger a run and check status.
airflow dags trigger claimslake_pipeline
airflow dags list-runs -d claimslake_pipeline
```

## Tests

DAG-structure tests live in `tests/airflow/`. They skip automatically when
Airflow is not installed, so the core test suite and CI stay green:

```bash
pip install "apache-airflow==2.9.3" --constraint \
  "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.11.txt"
python -m pytest tests/airflow -v
```
