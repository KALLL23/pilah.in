"""Configuration loading and validation for object detection training."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from . import TAXONOMY


class ConfigError(ValueError):
    """Raised when a detection pipeline configuration is invalid."""


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
    def images_root(self) -> Path:
        return self.raw_root / self.data["dataset"]["images_dir"]

    @property
    def labels_root(self) -> Path:
        return self.raw_root / self.data["dataset"]["labels_dir"]

    @property
    def processed_root(self) -> Path:
        return self.resolve(self.data["dataset"]["processed_root"])

    @property
    def run_root(self) -> Path:
        return self.resolve(self.data["output"]["runs_dir"]) / self.data["model"]["version"]

    @property
    def source_names(self) -> tuple[str, ...]:
        names = self.data["dataset"]["source_names"]
        if isinstance(names, list):
            return tuple(str(name) for name in names)
        return tuple(str(names[index] if index in names else names[str(index)]) for index in range(len(names)))


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
    for key in ("version", "raw_root", "processed_root", "images_dir", "labels_dir", "source_names", "class_mapping"):
        _require(dataset, key, "dataset")
    configured_taxonomy = tuple(dataset.get("taxonomy", TAXONOMY))
    if configured_taxonomy != TAXONOMY:
        raise ConfigError(f"dataset.taxonomy must exactly match {list(TAXONOMY)}")

    source_names_value = dataset["source_names"]
    if isinstance(source_names_value, list):
        source_names = tuple(str(name) for name in source_names_value)
    elif isinstance(source_names_value, dict) and source_names_value:
        try:
            indexed = {int(key): str(value) for key, value in source_names_value.items()}
            source_names = tuple(indexed[index] for index in range(len(indexed)))
        except (KeyError, TypeError, ValueError) as exc:
            raise ConfigError("dataset.source_names mapping must use contiguous class IDs starting at 0") from exc
    else:
        raise ConfigError("dataset.source_names must be a non-empty list or class-ID mapping")
    if not source_names or len(set(source_names)) != len(source_names):
        raise ConfigError("dataset.source_names must contain unique, non-empty names")

    class_mapping = dataset["class_mapping"]
    if not isinstance(class_mapping, dict):
        raise ConfigError("dataset.class_mapping must be a mapping")
    missing = sorted(set(source_names) - set(class_mapping))
    unknown_targets = sorted({str(value) for value in class_mapping.values()} - set(TAXONOMY))
    if missing:
        raise ConfigError(f"dataset.class_mapping is missing source classes: {', '.join(missing)}")
    if unknown_targets:
        raise ConfigError(f"dataset.class_mapping contains unsupported targets: {', '.join(unknown_targets)}")

    ratios = [float(_require(raw["split"], key, "split")) for key in ("train", "val", "test")]
    if any(ratio <= 0 for ratio in ratios) or abs(sum(ratios) - 1.0) > 1e-8:
        raise ConfigError("split.train + split.val + split.test must equal 1.0 and be positive")
    _require(raw["split"], "seed", "split")
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
