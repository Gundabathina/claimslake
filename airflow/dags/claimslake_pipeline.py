"""ClaimsLake end-to-end pipeline DAG.

Orchestrates the existing ClaimsLake stages as separate Airflow tasks:

    check_prerequisites
        -> bronze_ingestion
        -> silver_processing
        -> gold_dbt_build
        -> validate_outputs

The DAG does NOT reimplement any business logic. Each task calls the
production functions already used by scripts/run_pipeline.py
(check_prerequisites, run_bronze, run_silver, run_gold), so ingestion,
PySpark and dbt logic live in exactly one place.

All filesystem locations are configurable via environment variables so the
same DAG works locally, in Docker, or on a mounted volume:

    CLAIMSLAKE_REPO_ROOT   repository root (must be importable)
    CLAIMSLAKE_BRONZE      Bronze output dir           (default: bronze)
    CLAIMSLAKE_SILVER      Silver output dir           (default: silver)
    CLAIMSLAKE_QUARANTINE  quarantine dir              (default: silver/quarantine)
    CLAIMSLAKE_METRICS     data-quality metrics dir    (default: data_quality/metrics)
    CLAIMSLAKE_DUCKDB_PATH Gold DuckDB file            (default: <root>/gold/claimslake.duckdb)
    DBT_PROFILES_DIR       dbt profiles dir            (default: <root>/dbt)
"""
from __future__ import annotations

import glob
import logging
import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

log = logging.getLogger("claimslake.airflow")

# ---------------------------------------------------------------------------
# Configuration (resolved at parse time, but no heavy work is done on import).
# ---------------------------------------------------------------------------
REPO_ROOT = os.environ.get(
    "CLAIMSLAKE_REPO_ROOT",
    # dags file lives at <root>/airflow/dags/claimslake_pipeline.py
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
)

BRONZE_PATH = os.environ.get("CLAIMSLAKE_BRONZE", os.path.join(REPO_ROOT, "bronze"))
SILVER_PATH = os.environ.get("CLAIMSLAKE_SILVER", os.path.join(REPO_ROOT, "silver"))
QUARANTINE_PATH = os.environ.get(
    "CLAIMSLAKE_QUARANTINE", os.path.join(SILVER_PATH, "quarantine")
)
METRICS_PATH = os.environ.get(
    "CLAIMSLAKE_METRICS", os.path.join(REPO_ROOT, "data_quality", "metrics")
)
DUCKDB_PATH = os.environ.get(
    "CLAIMSLAKE_DUCKDB_PATH", os.path.join(REPO_ROOT, "gold", "claimslake.duckdb")
)
DBT_PROFILES_DIR = os.environ.get("DBT_PROFILES_DIR", os.path.join(REPO_ROOT, "dbt"))

PATHS = {
    "bronze": BRONZE_PATH,
    "silver": SILVER_PATH,
    "quarantine": QUARANTINE_PATH,
    "metrics": METRICS_PATH,
}


def _load_runner():
    """Import the production runner, adding the repo root to sys.path.

    Imported lazily inside each task so a missing repo path fails the task
    (with a clear log) rather than breaking DAG parsing for the whole
    scheduler.
    """
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)
    from scripts import run_pipeline  # noqa: WPS433 (deliberate lazy import)

    return run_pipeline


# ---------------------------------------------------------------------------
# Task callables (thin wrappers over the existing production functions).
# ---------------------------------------------------------------------------
def _check_prerequisites(**_):
    runner = _load_runner()
    log.info("Checking prerequisites (pyspark, dbt, java) ...")
    runner.check_prerequisites(skip_gold=False)
    log.info("Ensuring output directories exist ...")
    runner.ensure_dirs(PATHS)
    os.makedirs(os.path.dirname(DUCKDB_PATH), exist_ok=True)
    log.info("Prerequisites OK. repo_root=%s", REPO_ROOT)


def _bronze_ingestion(**_):
    runner = _load_runner()
    log.info("Starting Bronze ingestion -> %s", BRONZE_PATH)
    runner.run_bronze()
    log.info("Bronze ingestion complete.")


def _silver_processing(**_):
    runner = _load_runner()
    log.info("Starting Silver PySpark processing -> %s", SILVER_PATH)
    runner.run_silver(PATHS)
    log.info("Silver processing complete.")


def _gold_dbt_build(**_):
    runner = _load_runner()
    os.environ["DBT_PROFILES_DIR"] = DBT_PROFILES_DIR
    os.environ["CLAIMSLAKE_DUCKDB_PATH"] = DUCKDB_PATH
    log.info("Starting Gold dbt build (profiles=%s, duckdb=%s)",
             DBT_PROFILES_DIR, DUCKDB_PATH)
    runner.run_gold(SILVER_PATH)
    log.info("Gold dbt build complete.")


def _validate_outputs(**_):
    """Confirm every expected artifact exists; raise to fail the DAG run."""
    checks = {
        "Bronze Parquet": os.path.join(BRONZE_PATH, "**", "*.parquet"),
        "Silver members Parquet": os.path.join(SILVER_PATH, "members", "**", "*.parquet"),
        "Silver providers Parquet": os.path.join(SILVER_PATH, "providers", "**", "*.parquet"),
        "Silver diagnoses Parquet": os.path.join(SILVER_PATH, "diagnoses", "**", "*.parquet"),
        "Silver claims Parquet": os.path.join(SILVER_PATH, "claims", "**", "*.parquet"),
        "Quarantine output": os.path.join(QUARANTINE_PATH, "**", "*.parquet"),
        "Metrics JSON": os.path.join(METRICS_PATH, "*.json"),
    }
    missing = []
    for label, pattern in checks.items():
        found = glob.glob(pattern, recursive=True)
        if found:
            log.info("OK  %-26s (%d file(s))", label, len(found))
        else:
            missing.append(f"{label} (no match for {pattern})")
            log.error("MISSING  %s -> %s", label, pattern)

    if not os.path.isfile(DUCKDB_PATH):
        missing.append(f"Gold DuckDB file ({DUCKDB_PATH})")
        log.error("MISSING  Gold DuckDB file -> %s", DUCKDB_PATH)
    else:
        log.info("OK  %-26s (%s)", "Gold DuckDB file", DUCKDB_PATH)

    if missing:
        raise FileNotFoundError(
            "Output validation failed; missing artifacts: " + "; ".join(missing)
        )
    log.info("All expected pipeline outputs are present.")


# ---------------------------------------------------------------------------
# DAG definition.
# ---------------------------------------------------------------------------
default_args = {
    "owner": "claimslake",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "execution_timeout": timedelta(minutes=30),
    "depends_on_past": False,
}

with DAG(
    dag_id="claimslake_pipeline",
    description="ClaimsLake Bronze -> Silver -> Gold pipeline (reuses run_pipeline).",
    default_args=default_args,
    schedule=None,          # manual / configurable trigger only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["claimslake", "healthcare", "etl", "dbt", "pyspark"],
) as dag:

    check_prerequisites = PythonOperator(
        task_id="check_prerequisites",
        python_callable=_check_prerequisites,
    )

    bronze_ingestion = PythonOperator(
        task_id="bronze_ingestion",
        python_callable=_bronze_ingestion,
    )

    silver_processing = PythonOperator(
        task_id="silver_processing",
        python_callable=_silver_processing,
    )

    gold_dbt_build = PythonOperator(
        task_id="gold_dbt_build",
        python_callable=_gold_dbt_build,
    )

    validate_outputs = PythonOperator(
        task_id="validate_outputs",
        python_callable=_validate_outputs,
    )

    (
        check_prerequisites
        >> bronze_ingestion
        >> silver_processing
        >> gold_dbt_build
        >> validate_outputs
    )
