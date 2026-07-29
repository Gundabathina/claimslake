"""Tests for the claimslake_pipeline Airflow DAG.

These tests exercise the DAG *definition* only (parse-time structure); they do
not run tasks, and therefore need neither Spark, dbt, nor an Airflow metadata
database. Airflow is an optional, orchestration-only dependency (installed via
airflow/requirements-airflow.txt), so the whole module is skipped cleanly when
Airflow is not installed - this keeps the core test suite / CI green without
pulling in the heavy Airflow stack.
"""
from __future__ import annotations

import os

import pytest

pytest.importorskip("airflow")  # skip entire module if Airflow is absent

from airflow.models import DagBag  # noqa: E402 (after importorskip by design)

DAG_ID = "claimslake_pipeline"
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
DAGS_FOLDER = os.path.join(REPO_ROOT, "airflow", "dags")

EXPECTED_TASK_IDS = {
    "check_prerequisites",
    "bronze_ingestion",
    "silver_processing",
    "gold_dbt_build",
    "validate_outputs",
}

# Expected linear order: upstream -> downstream.
EXPECTED_CHAIN = [
    "check_prerequisites",
    "bronze_ingestion",
    "silver_processing",
    "gold_dbt_build",
    "validate_outputs",
]


@pytest.fixture(scope="module")
def dagbag():
    # include_examples=False so only our DAG is parsed.
    return DagBag(dag_folder=DAGS_FOLDER, include_examples=False)


@pytest.fixture(scope="module")
def dag(dagbag):
    d = dagbag.get_dag(DAG_ID)
    assert d is not None, f"DAG {DAG_ID!r} not found in {DAGS_FOLDER}"
    return d


def test_dag_imports_without_errors(dagbag):
    assert dagbag.import_errors == {}, f"DAG import errors: {dagbag.import_errors}"


def test_dag_is_registered(dag):
    assert dag.dag_id == DAG_ID


def test_expected_task_ids_exist(dag):
    assert set(dag.task_ids) == EXPECTED_TASK_IDS


def test_dependency_order_is_correct(dag):
    for upstream, downstream in zip(EXPECTED_CHAIN, EXPECTED_CHAIN[1:]):
        task = dag.get_task(downstream)
        assert upstream in task.upstream_task_ids, (
            f"{downstream} should depend on {upstream}; "
            f"actual upstreams: {sorted(task.upstream_task_ids)}"
        )
    # First task has no upstream; last task has no downstream.
    assert dag.get_task(EXPECTED_CHAIN[0]).upstream_task_ids == set()
    assert dag.get_task(EXPECTED_CHAIN[-1]).downstream_task_ids == set()


def test_catchup_is_disabled(dag):
    assert dag.catchup is False


def test_retry_configuration_exists(dag):
    for task in dag.tasks:
        assert task.retries and task.retries >= 1, (
            f"task {task.task_id} must configure retries"
        )
        assert task.retry_delay is not None, (
            f"task {task.task_id} must configure retry_delay"
        )
        assert task.execution_timeout is not None, (
            f"task {task.task_id} must configure execution_timeout"
        )


def test_dag_has_tags_and_manual_schedule(dag):
    assert "claimslake" in dag.tags
    # schedule=None means manual/triggered runs only.
    assert dag.schedule_interval is None
