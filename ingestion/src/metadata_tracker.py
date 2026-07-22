"""
metadata_tracker.py

Tracks every ingestion run in a local SQLite database
(ingestion/metadata/ingestion_metadata.db).

Why SQLite instead of a plain CSV/JSON log:
  - Before every run we need to answer 'has this exact file already been
    ingested successfully?' (the idempotency check). Against a CSV/JSON
    file that means parsing and scanning the whole file by hand each
    time. SQLite answers it with a single indexed query
    (WHERE source_name = ? AND file_hash = ?), with almost no extra code.
  - It is still a single file with zero setup: no server or daemon to
    run, which would be overkill for a local portfolio project.
  - It stores exactly the same fields a CSV/JSON audit log would (see the
    ingestion_log table below), so nothing about the audit trail is lost;
    only the storage mechanism changed.
"""

import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import List, Optional

METADATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "metadata"
)
DB_PATH = os.path.join(METADATA_DIR, "ingestion_metadata.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS ingestion_log (
    ingestion_id          TEXT PRIMARY KEY,
    source_name           TEXT NOT NULL,
    source_file           TEXT NOT NULL,
    file_hash             TEXT NOT NULL,
    ingestion_start_time  TEXT NOT NULL,
    ingestion_end_time    TEXT,
    record_count          INTEGER,
    status                TEXT NOT NULL,
    error_message         TEXT,
    load_type             TEXT NOT NULL,
    target_path           TEXT
);
"""

SUCCESS_STATUSES = ("SUCCESS", "SUCCESS_WITH_DRIFT")


class MetadataTracker:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        with self._connect() as conn:
            conn.execute(SCHEMA)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def already_ingested(self, source_name: str, file_hash: str) -> bool:
        """Idempotency check: has a file with this exact content hash
        already been ingested successfully for this source?"""
        placeholders = ",".join("?" for _ in SUCCESS_STATUSES)
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT 1 FROM ingestion_log WHERE source_name = ? AND file_hash = ? "
                "AND status IN (%s) LIMIT 1" % placeholders,
                (source_name, file_hash, *SUCCESS_STATUSES),
            )
            return cur.fetchone() is not None

    def start(self, source_name: str, source_file: str, file_hash: str,
              load_type: str) -> str:
        ingestion_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO ingestion_log "
                "(ingestion_id, source_name, source_file, file_hash, "
                " ingestion_start_time, status, load_type) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ingestion_id, source_name, source_file, file_hash,
                 datetime.now(timezone.utc).isoformat(), "IN_PROGRESS", load_type),
            )
        return ingestion_id

    def complete(self, ingestion_id: str, record_count: int, status: str,
                 target_path: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE ingestion_log SET ingestion_end_time = ?, record_count = ?, "
                "status = ?, target_path = ? WHERE ingestion_id = ?",
                (datetime.now(timezone.utc).isoformat(), record_count, status,
                 target_path, ingestion_id),
            )

    def fail(self, ingestion_id: str, error_message: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE ingestion_log SET ingestion_end_time = ?, status = ?, "
                "error_message = ? WHERE ingestion_id = ?",
                (datetime.now(timezone.utc).isoformat(), "FAILED",
                 error_message, ingestion_id),
            )

    def history(self, source_name: Optional[str] = None) -> List[dict]:
        with self._connect() as conn:
            if source_name:
                cur = conn.execute(
                    "SELECT * FROM ingestion_log WHERE source_name = ? "
                    "ORDER BY ingestion_start_time",
                    (source_name,),
                )
            else:
                cur = conn.execute(
                    "SELECT * FROM ingestion_log ORDER BY ingestion_start_time"
                )
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
