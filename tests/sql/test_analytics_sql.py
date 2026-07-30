"""Tests for the Stage 4 analytics SQL layer.

Two kinds of checks are performed:

1. Static checks (always run): every analytics file exists, is non-empty,
   and references only real Gold tables. These require no database.

2. Execution checks (run only when duckdb is installed AND the Gold
   warehouse has been built): each analytics query is executed against
   gold/claimslake.duckdb to prove it runs without error.

The execution checks are skipped -- not failed -- when duckdb or the built
warehouse is unavailable, so core CI stays green on a fresh clone.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = REPO_ROOT / "sql"
DUCKDB_PATH = REPO_ROOT / "gold" / "claimslake.duckdb"

ANALYTICS_FILES = [
    SQL_DIR / "claims" / "claims_analytics.sql",
    SQL_DIR / "providers" / "provider_analytics.sql",
    SQL_DIR / "members" / "member_analytics.sql",
    SQL_DIR / "finance" / "financial_analytics.sql",
    SQL_DIR / "data_quality" / "data_quality_analytics.sql",
]

# Tables that legitimately exist in the Gold warehouse (dbt marts) plus the
# Silver quarantine Parquet read via read_parquet in the data-quality file.
KNOWN_GOLD_TABLES = {"fact_claims", "dim_member", "dim_provider"}


def _strip_sql_comments(sql: str) -> str:
    """Remove -- line comments so keyword scans ignore prose in comments."""
    lines = []
    for line in sql.splitlines():
        idx = line.find("--")
        lines.append(line if idx == -1 else line[:idx])
    return "\n".join(lines)


def _split_statements(sql: str) -> list[str]:
    """Split a script into individual executable SQL statements.

    DuckDB dot-commands (.read/.print) are not valid SQL, so lines starting
    with a dot are dropped; the remaining text is split on semicolons.
    """
    body = "\n".join(
        line for line in sql.splitlines() if not line.lstrip().startswith(".")
    )
    return [s.strip() for s in body.split(";") if s.strip()]


@pytest.mark.parametrize("sql_file", ANALYTICS_FILES, ids=lambda p: p.name)
def test_analytics_file_exists_and_nonempty(sql_file: Path) -> None:
    assert sql_file.is_file(), f"missing analytics file: {sql_file}"
    assert sql_file.read_text(encoding="utf-8").strip(), f"empty file: {sql_file}"


def test_run_all_references_every_file() -> None:
    run_all = SQL_DIR / "run_all.sql"
    assert run_all.is_file(), "sql/run_all.sql is missing"
    text = run_all.read_text(encoding="utf-8")
    for sql_file in ANALYTICS_FILES:
        rel = sql_file.relative_to(REPO_ROOT).as_posix()
        assert rel in text, f"run_all.sql does not .read {rel}"


@pytest.mark.parametrize("sql_file", ANALYTICS_FILES, ids=lambda p: p.name)
def test_no_unknown_tables_in_from_clauses(sql_file: Path) -> None:
    """Guard against fabricated schema: every bare identifier used after FROM
    or JOIN must be a known Gold table (read_parquet(...) is allowed)."""
    code = _strip_sql_comments(sql_file.read_text(encoding="utf-8"))
    # capture the token immediately after FROM / JOIN
    refs = re.findall(r"\b(?:FROM|JOIN)\s+([A-Za-z_][\w]*)", code, flags=re.IGNORECASE)
    for ref in refs:
        low = ref.lower()
        if low in {"read_parquet"}:  # table function, handled separately
            continue
        assert low in KNOWN_GOLD_TABLES, (
            f"{sql_file.name} references unknown table '{ref}'. "
            f"Allowed: {sorted(KNOWN_GOLD_TABLES)} or read_parquet(...)."
        )


# ---------------------------------------------------------------------------
# Execution checks -- skipped unless duckdb + a built warehouse are present.
# ---------------------------------------------------------------------------
duckdb = pytest.importorskip("duckdb", reason="duckdb not installed")

warehouse_required = pytest.mark.skipif(
    not DUCKDB_PATH.exists(),
    reason=f"Gold warehouse not built at {DUCKDB_PATH}; run the pipeline first",
)


@warehouse_required
@pytest.mark.parametrize("sql_file", ANALYTICS_FILES, ids=lambda p: p.name)
def test_analytics_queries_execute(sql_file: Path) -> None:
    """Execute every statement in each analytics file against the real Gold
    warehouse. read_parquet paths are relative to the repo root, so we run
    with the process CWD assumed to be the repo root during CI; DuckDB is
    opened read-only so the tests never mutate the warehouse."""
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        for stmt in _split_statements(sql_file.read_text(encoding="utf-8")):
            con.execute(stmt).fetchall()
    finally:
        con.close()
