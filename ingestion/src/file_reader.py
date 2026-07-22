"""
file_reader.py

Discovery, hashing, and reading of source CSV files for a given source
configuration.

Reading uses only the standard library csv module - no pandas dependency
is needed to read. pandas/pyarrow are used only downstream, in the
Bronze-writing step, to produce Parquet output.
"""

import csv
import glob
import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Tuple

from ingestion.src.config_loader import SourceConfig


@dataclass
class DiscoveredFile:
    path: str
    file_name: str
    file_hash: str
    modified_time: str


def compute_file_hash(path: str, chunk_size: int = 65536) -> str:
    """SHA-256 hash of a file's contents.

    Used for two things:
      1. Idempotency - 'has this exact file already been ingested?'
      2. Change detection - 'has this file's content changed since the
         last time we saw it?'
    """
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def discover_files(config: SourceConfig) -> List[DiscoveredFile]:
    """Return every file matching this source's file_pattern, sorted by
    file name so batch ordering (batch_1 before batch_2) is deterministic."""
    pattern = os.path.join(config.source_dir_abs, config.file_pattern)
    matches = sorted(glob.glob(pattern))

    discovered: List[DiscoveredFile] = []
    for path in matches:
        modified = datetime.fromtimestamp(
            os.path.getmtime(path), tz=timezone.utc
        ).isoformat()
        discovered.append(
            DiscoveredFile(
                path=path,
                file_name=os.path.basename(path),
                file_hash=compute_file_hash(path),
                modified_time=modified,
            )
        )
    return discovered


def read_csv(path: str) -> Tuple[List[str], List[dict]]:
    """Read a CSV file into (header, rows).

    header is the list of column names; rows is a list of dicts keyed by
    column name. Raises FileNotFoundError if the file is missing (which
    the retry handler treats as non-retryable).
    """
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        rows = list(reader)
    return header, rows
