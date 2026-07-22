# ingestion/metadata/

Holds the local ingestion audit database, ingestion_metadata.db, a SQLite
file written by metadata_tracker.py.

Every ingestion run records one row per file processed, capturing:
ingestion_id, source_name, source_file, file_hash, ingestion_start_time,
ingestion_end_time, record_count, status, error_message, load_type, and
target_path.

## Generated, not source-controlled

Like the bronze/ output, the .db file is a generated artifact and is
excluded from git (see .gitignore). Only this README is tracked. The
database is created automatically the first time the ingestion engine runs.

## Why SQLite

SQLite gives a single-file, zero-setup store that still supports a real
indexed query for the idempotency check (has this exact file already been
ingested successfully?), which a flat CSV/JSON log cannot do as cleanly. A
full database server would be unnecessary overhead for a local project. See
ingestion/README.md for the full rationale.
