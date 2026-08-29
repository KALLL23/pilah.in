"""Configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from . import TAXONOMY


class ConfigError(ValueError):
    """Raised when a pipeline configuration is invalid."""


@dataclass(frozen=True)
class PipelineConfig:
    path: Path
    repo_root: Path
    data: dict[str, Any]

    def resolve(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.repo_root / path

    @property
    def raw_root(self) -> Path:
        return self.resolve(self.data["dataset"]["raw_root"])

    @property
    def processed_root(self) -> Path:
        return self.resolve(self.data["dataset"]["processed_root"])

    @property
    def run_root(self) -> Path:
        return self.resolve(self.data["output"]["runs_dir"]) / self.data["model"]["version"]


def _require(mapping: dict[str, Any], key: str, section: str) -> Any:
    if key not in mapping:
        raise ConfigError(f"Missing required configuration: {section}.{key}")
    return mapping[key]


def load_config(path: str | Path) -> PipelineConfig:
    config_path = Path(path).resolve()
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Configuration file not found: {config_path}") from exc
    if not isinstance(raw, dict):
        raise ConfigError("Configuration root must be a YAML mapping")
    for section in ("dataset", "split", "model", "output"):
        if not isinstance(raw.get(section), dict):
            raise ConfigError(f"Missing or invalid configuration section: {section}")
    dataset = raw["dataset"]
    for key in ("version", "raw_root", "processed_root", "sources"):
        _require(dataset, key, "dataset")
    if not isinstance(dataset["sources"], list) or not dataset["sources"]:
        raise ConfigError("dataset.sources must be a non-empty list")
    names = [item.get("name") if isinstance(item, dict) else None for item in dataset["sources"]]
    if any(not name for name in names) or len(set(names)) != len(names):
        raise ConfigError("Each dataset source needs a unique name")
    ratios = [float(_require(raw["split"], key, "split")) for key in ("train", "val", "test")]
    if any(ratio <= 0 for ratio in ratios) or abs(sum(ratios) - 1.0) > 1e-8:
        raise ConfigError("split.train + split.val + split.test must equal 1.0 and be positive")
    configured_taxonomy = tuple(dataset.get("taxonomy", TAXONOMY))
    if configured_taxonomy != TAXONOMY:
        raise ConfigError(f"dataset.taxonomy must exactly match {list(TAXONOMY)}")
    for key in ("version", "name", "imgsz", "epochs", "batch", "device"):
        _require(raw["model"], key, "model")
    for key in ("runs_dir", "production_model", "archive_dir"):
        _require(raw["output"], key, "output")
    repo_root = config_path.parent
    while repo_root.parent != repo_root and not (repo_root / ".git").exists():
        repo_root = repo_root.parent
    if not (repo_root / ".git").exists():
        repo_root = Path.cwd().resolve()
    return PipelineConfig(config_path, repo_root, raw)
