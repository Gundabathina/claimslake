#!/usr/bin/env python3
"""ClaimsLake end-to-end local runner.

Runs the complete local pipeline in order:

    source CSVs -> Bronze ingestion -> Silver PySpark -> Gold dbt build

This is an ORCHESTRATOR only. It does not reimplement any pipeline logic:
it calls the existing entry points --

  * Bronze: ingestion.src.ingestion_engine.main(argv)
  * Silver: spark_jobs.src.silver_pipeline.main(argv)
  * Gold:   dbt build (in ./dbt), via subprocess

Each stage stops the pipeline immediately on failure (non-zero exit).

Usage:
    python scripts/run_pipeline.py               # full pipeline
    python scripts/run_pipeline.py --skip-gold   # Bronze + Silver only
    make pipeline

Configurable paths (CLI flag overrides env var overrides default):
    --bronze-path      CLAIMSLAKE_BRONZE      (default: bronze)
    --silver-path      CLAIMSLAKE_SILVER      (default: silver)
    --quarantine-path  CLAIMSLAKE_QUARANTINE  (default: silver/quarantine)
    --metrics-path     CLAIMSLAKE_METRICS     (default: data_quality/metrics)
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time

# Ensure the repo root is importable when run as "python scripts/run_pipeline.py".
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _banner(msg: str) -> None:
    print("\n" + "=" * 70, flush=True)
    print(f"  {msg}", flush=True)
    print("=" * 70, flush=True)


def _summary(stage: str, seconds: float, detail: str = "") -> None:
    tail = f" - {detail}" if detail else ""
    print(f"[OK] {stage} completed in {seconds:0.1f}s{tail}", flush=True)


def _fail(stage: str, code: int) -> "NoReturn":  # type: ignore[valid-type]
    print(f"[FAIL] {stage} exited with status {code}. Stopping pipeline.",
          file=sys.stderr, flush=True)
    sys.exit(code if code else 1)


def check_prerequisites(skip_gold: bool) -> None:
    """Fail fast if required tooling / packages are missing."""
    _banner("Checking prerequisites")
    problems = []
    try:
        import pyspark  # noqa: F401
        print("  pyspark: found", flush=True)
    except ImportError:
        problems.append("pyspark not installed (pip install pyspark==4.0.0)")
    if not skip_gold and shutil.which("dbt") is None:
        problems.append("dbt not on PATH (pip install -r dbt/requirements-dbt.txt)")
    if not os.environ.get("JAVA_HOME") and shutil.which("java") is None:
        problems.append("Java not found; PySpark needs a JVM (JDK 17)")
    if problems:
        for p in problems:
            print(f"  MISSING: {p}", file=sys.stderr, flush=True)
        _fail("prerequisite check", 1)
    print("  all prerequisites satisfied", flush=True)


def ensure_dirs(paths: dict) -> None:
    for label, path in paths.items():
        os.makedirs(path, exist_ok=True)
        print(f"  ensured {label}: {path}", flush=True)


def run_bronze() -> None:
    _banner("Stage 1/3  Bronze ingestion")
    start = time.time()
    from ingestion.src.ingestion_engine import main as bronze_main
    code = bronze_main(["--all"])
    if code:
        _fail("Bronze ingestion", code)
    _summary("Bronze ingestion", time.time() - start)


def run_silver(paths: dict) -> None:
    _banner("Stage 2/3  Silver PySpark processing")
    start = time.time()
    from spark_jobs.src.silver_pipeline import main as silver_main
    argv = [
        "--all",
        "--input-path", paths["bronze"],
        "--output-path", paths["silver"],
        "--quarantine-path", paths["quarantine"],
        "--metrics-path", paths["metrics"],
    ]
    code = silver_main(argv)
    if code:
        _fail("Silver processing", code)
    _summary("Silver processing", time.time() - start)


def run_gold(silver_path: str) -> None:
    _banner("Stage 3/3  Gold dbt build")
    start = time.time()
    dbt_dir = os.path.join(REPO_ROOT, "dbt")
    # dbt runs with cwd=dbt_dir, so a relative DuckDB path in the profile would
    # resolve under dbt/. Resolve an ABSOLUTE repo-root path and make sure its
    # parent directory exists, so a fresh clone works with no manual mkdir.
    duckdb_path = os.environ.get(
        "CLAIMSLAKE_DUCKDB_PATH",
        os.path.join(REPO_ROOT, "gold", "claimslake.duckdb"),
    )
    duckdb_path = os.path.abspath(duckdb_path)
    os.makedirs(os.path.dirname(duckdb_path), exist_ok=True)
    print(f"  Gold DuckDB warehouse: {duckdb_path}", flush=True)
    env = dict(os.environ)
    env.setdefault("DBT_PROFILES_DIR", dbt_dir)
    # Feed the absolute path to the profile (path: env_var('CLAIMSLAKE_DUCKDB_PATH', ...)).
    env["CLAIMSLAKE_DUCKDB_PATH"] = duckdb_path
    cmd = ["dbt", "build", "--vars", f"{{silver_root: {os.path.abspath(silver_path)}}}"]
    print(f"  running: {' '.join(cmd)} (cwd={dbt_dir})", flush=True)
    proc = subprocess.run(cmd, cwd=dbt_dir, env=env)
    if proc.returncode:
        _fail("Gold dbt build", proc.returncode)
    _summary("Gold dbt build", time.time() - start)


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the ClaimsLake pipeline end to end.")
    p.add_argument("--bronze-path", default=_env("CLAIMSLAKE_BRONZE", "bronze"))
    p.add_argument("--silver-path", default=_env("CLAIMSLAKE_SILVER", "silver"))
    p.add_argument("--quarantine-path",
                   default=_env("CLAIMSLAKE_QUARANTINE", "silver/quarantine"))
    p.add_argument("--metrics-path",
                   default=_env("CLAIMSLAKE_METRICS", "data_quality/metrics"))
    p.add_argument("--skip-gold", action="store_true",
                   help="Run Bronze + Silver only (skip dbt).")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    paths = {
        "bronze": args.bronze_path,
        "silver": args.silver_path,
        "quarantine": args.quarantine_path,
        "metrics": args.metrics_path,
    }
    overall = time.time()
    check_prerequisites(args.skip_gold)
    _banner("Ensuring output directories")
    ensure_dirs(paths)
    run_bronze()
    run_silver(paths)
    if args.skip_gold:
        print("\n[SKIP] Gold stage skipped (--skip-gold).", flush=True)
    else:
        run_gold(paths["silver"])
    _banner(f"Pipeline complete in {time.time() - overall:0.1f}s")
    print("Outputs:", flush=True)
    print(f"  Bronze Parquet      -> {paths['bronze']}/", flush=True)
    print(f"  Silver Parquet      -> {paths['silver']}/", flush=True)
    print(f"  Quarantine records  -> {paths['quarantine']}/", flush=True)
    print(f"  Data-quality metrics-> {paths['metrics']}/", flush=True)
    if not args.skip_gold:
        print("  Gold DuckDB models  -> gold/claimslake.duckdb "
              "(dim_member, dim_provider, fact_claims)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
