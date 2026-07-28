"""Orchestration tests for scripts/run_pipeline.py.

These test the RUNNER's control flow only -- ordering, stop-on-failure, exit
codes, directory creation, and --skip-gold -- without executing Spark or dbt.
The heavy stages are monkeypatched, so no JVM or warehouse is required.
"""
import importlib.util
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNNER_PATH = os.path.join(REPO_ROOT, "scripts", "run_pipeline.py")


def _load_runner():
    """Load scripts/run_pipeline.py as a module by file path."""
    spec = importlib.util.spec_from_file_location("cl_run_pipeline", RUNNER_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def runner():
    return _load_runner()


@pytest.fixture
def stub_stages(runner, monkeypatch):
    """Replace real stages with recorders; skip prerequisite checks."""
    calls = []
    monkeypatch.setattr(runner, "check_prerequisites", lambda skip_gold: None)
    monkeypatch.setattr(runner, "run_bronze", lambda: calls.append("bronze"))
    monkeypatch.setattr(runner, "run_silver", lambda paths: calls.append("silver"))
    monkeypatch.setattr(runner, "run_gold", lambda silver: calls.append("gold"))
    return calls


def test_full_pipeline_runs_stages_in_order(runner, stub_stages, tmp_path):
    rc = runner.main([
        "--bronze-path", str(tmp_path / "bronze"),
        "--silver-path", str(tmp_path / "silver"),
        "--quarantine-path", str(tmp_path / "silver" / "quarantine"),
        "--metrics-path", str(tmp_path / "metrics"),
    ])
    assert rc == 0
    assert stub_stages == ["bronze", "silver", "gold"]


def test_skip_gold_skips_only_gold(runner, stub_stages, tmp_path):
    rc = runner.main([
        "--bronze-path", str(tmp_path / "bronze"),
        "--silver-path", str(tmp_path / "silver"),
        "--skip-gold",
    ])
    assert rc == 0
    assert stub_stages == ["bronze", "silver"]
    assert "gold" not in stub_stages


def test_directories_are_created(runner, stub_stages, tmp_path):
    bronze = tmp_path / "b"
    silver = tmp_path / "s"
    metrics = tmp_path / "m"
    runner.main([
        "--bronze-path", str(bronze),
        "--silver-path", str(silver),
        "--quarantine-path", str(silver / "q"),
        "--metrics-path", str(metrics),
        "--skip-gold",
    ])
    assert bronze.is_dir()
    assert silver.is_dir()
    assert metrics.is_dir()


def test_pipeline_stops_and_exits_nonzero_on_stage_failure(runner, monkeypatch, tmp_path):
    order = []
    monkeypatch.setattr(runner, "check_prerequisites", lambda skip_gold: None)

    def failing_bronze():
        order.append("bronze")
        runner._fail("Bronze ingestion", 2)

    def should_not_run(paths):
        order.append("silver")

    monkeypatch.setattr(runner, "run_bronze", failing_bronze)
    monkeypatch.setattr(runner, "run_silver", should_not_run)

    with pytest.raises(SystemExit) as exc:
        runner.main([
            "--bronze-path", str(tmp_path / "bronze"),
            "--silver-path", str(tmp_path / "silver"),
            "--skip-gold",
        ])
    # Non-zero exit code, and Silver never ran after Bronze failed.
    assert exc.value.code == 2
    assert order == ["bronze"]
