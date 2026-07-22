#!/usr/bin/env python3
"""
Convenience entry point so 'make ingest' works. Equivalent to:

    python -m ingestion.src.ingestion_engine --all

All real logic lives in ingestion/src/ingestion_engine.py; this wrapper only
exists so the Makefile 'ingest' target has something to call.
"""

import os
import sys

# Ensure the repo root is importable even when this is run as a plain script
# (python ingestion/run_ingestion.py), not just as a module.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.src.ingestion_engine import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(["--all"]))
