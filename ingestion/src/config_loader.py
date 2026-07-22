"""
config_loader.py

Loads and validates ingestion/config/sources.yaml into typed
SourceConfig objects, so the rest of the ingestion engine never has to
hard-code a source's file path, columns, or load type.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import yaml

# repo root = three levels up from ingestion/src/config_loader.py
REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DEFAULT_CONFIG_PATH = os.path.join(
    REPO_ROOT, "ingestion", "config", "sources.yaml"
)


@dataclass
class SourceConfig:
    name: str
    description: str
    source_dir: str
    file_pattern: str
    file_format: str
    load_type: str
    primary_key: List[str]
    expected_columns: List[str]
    required_columns: List[str]
    schema_drift_policy: str
    incremental_key: Optional[str]
    bronze_path: str

    @property
    def source_dir_abs(self) -> str:
        # os.path.join ignores REPO_ROOT when source_dir is already absolute,
        # which is what the test fixtures rely on.
        return os.path.join(REPO_ROOT, self.source_dir)

    @property
    def bronze_path_abs(self) -> str:
        return os.path.join(REPO_ROOT, self.bronze_path)


def load_sources(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, SourceConfig]:
    """Load and validate all source definitions from the YAML config."""
    if not os.path.exists(config_path):
        raise FileNotFoundError("Ingestion config not found: %s" % config_path)

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not raw or "sources" not in raw:
        raise ValueError(
            "Config file %s is missing a top-level 'sources' key" % config_path
        )

    required_fields = [
        "description", "source_dir", "file_pattern", "file_format",
        "load_type", "primary_key", "expected_columns", "required_columns",
        "schema_drift_policy", "bronze_path",
    ]

    sources: Dict[str, SourceConfig] = {}
    for name, cfg in raw["sources"].items():
        missing = [f for f in required_fields if f not in cfg]
        if missing:
            raise ValueError(
                "Source '%s' is missing required config field(s): %s"
                % (name, missing)
            )
        if cfg["schema_drift_policy"] not in ("fail", "warn", "allow"):
            raise ValueError(
                "Source '%s' has invalid schema_drift_policy '%s' "
                "(must be fail/warn/allow)" % (name, cfg["schema_drift_policy"])
            )
        if cfg["load_type"] not in ("full", "incremental"):
            raise ValueError(
                "Source '%s' has invalid load_type '%s' (must be full/incremental)"
                % (name, cfg["load_type"])
            )

        sources[name] = SourceConfig(
            name=name,
            description=cfg["description"],
            source_dir=cfg["source_dir"],
            file_pattern=cfg["file_pattern"],
            file_format=cfg["file_format"],
            load_type=cfg["load_type"],
            primary_key=cfg["primary_key"],
            expected_columns=cfg["expected_columns"],
            required_columns=cfg["required_columns"],
            schema_drift_policy=cfg["schema_drift_policy"],
            incremental_key=cfg.get("incremental_key"),
            bronze_path=cfg["bronze_path"],
        )

    return sources
