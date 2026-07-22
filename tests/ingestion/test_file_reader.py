"""
Tests for ingestion/src/file_reader.py

These tests create real temporary CSV files and exercise the actual
file_reader functions - no mocking of the core logic.
"""

from ingestion.src.config_loader import SourceConfig
from ingestion.src.file_reader import compute_file_hash, discover_files, read_csv


def _make_source_config(tmp_path, file_pattern="members*.csv"):
    # source_dir is an absolute tmp path; SourceConfig.source_dir_abs does
    # os.path.join(REPO_ROOT, source_dir), and os.path.join returns the second
    # argument unchanged when it is already absolute - so discovery scans
    # exactly this temp directory.
    return SourceConfig(
        name="members",
        description="test",
        source_dir=str(tmp_path),
        file_pattern=file_pattern,
        file_format="csv",
        load_type="full",
        primary_key=["member_id"],
        expected_columns=["member_id", "first_name"],
        required_columns=["member_id", "first_name"],
        schema_drift_policy="fail",
        incremental_key=None,
        bronze_path=str(tmp_path / "bronze" / "members"),
    )


def test_discover_files_finds_matching_csv(tmp_path):
    (tmp_path / "members_sample.csv").write_text("member_id,first_name
M0000001,Alex
")
    config = _make_source_config(tmp_path)

    discovered = discover_files(config)

    assert len(discovered) == 1
    assert discovered[0].file_name == "members_sample.csv"
    assert len(discovered[0].file_hash) == 64  # sha256 hex length


def test_discover_files_returns_empty_when_no_match(tmp_path):
    config = _make_source_config(tmp_path, file_pattern="nonexistent*.csv")
    assert discover_files(config) == []


def test_compute_file_hash_is_deterministic(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("member_id,first_name
M0000001,Alex
")
    assert compute_file_hash(str(p)) == compute_file_hash(str(p))


def test_compute_file_hash_changes_with_content(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("member_id,first_name
M0000001,Alex
")
    h1 = compute_file_hash(str(p))
    p.write_text("member_id,first_name
M0000002,Sam
")
    h2 = compute_file_hash(str(p))
    assert h1 != h2


def test_read_csv_returns_header_and_rows(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("member_id,first_name
M0000001,Alex
M0000002,Sam
")

    header, rows = read_csv(str(p))

    assert header == ["member_id", "first_name"]
    assert len(rows) == 2
    assert rows[0]["member_id"] == "M0000001"
