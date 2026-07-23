"""
Root conftest.py

Anchors the pytest rootdir at the repository root and guarantees the
repo root is on sys.path during test collection, so tests can import the
first-party packages, for example:

    from ingestion.src.config_loader import SourceConfig
    from pyspark.src import transformations

Why this file is needed
-----------------------
pyproject.toml already sets pythonpath = ["."] under
[tool.pytest.ini_options]. However, tests/ingestion/ is a package (it
contains __init__.py) while tests/ is not. Under the default "prepend"
import mode, pytest inserts the first NON-package parent of a test
module (tests/) onto sys.path rather than the repo root, which left the
ingestion package unimportable during collection. Adding a root
conftest.py makes pytest treat the repo root as rootdir; the explicit
sys.path insert below makes that guarantee independent of import mode.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
