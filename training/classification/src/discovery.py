"""Discover source images without assuming a shared directory layout."""

from __future__ import annotations

from pathlib import Path
from typing import Any

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class DiscoveryError(RuntimeError):
    """Raised when a configured source cannot be discovered safely."""


def load_mapping(path: Path) -> dict[str, str]:
    import yaml

    content = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    mappings = content.get("mappings", content)
    if not isinstance(mappings, dict):
        raise DiscoveryError(f"Mapping must be a YAML mapping: {path}")
    return {str(key).strip().casefold(): str(value).strip() for key, value in mappings.items()}


def discover_source(raw_root: Path, source: dict[str, Any], repo_root: Path) -> list[dict[str, Any]]:
    name = source["name"]
    root = raw_root / source.get("directory", name)
    if not root.is_dir():
        raise DiscoveryError(
            f"Source '{name}' directory not found: {root}. Extract the dataset into this directory."
        )
    mapping_path = Path(source["mapping"])
    if not mapping_path.is_absolute():
        mapping_path = repo_root / mapping_path
    mapping = load_mapping(mapping_path)
    images = sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.casefold() in IMAGE_EXTENSIONS),
        key=lambda path: path.relative_to(root).as_posix().casefold(),
    )
    if not images:
        raise DiscoveryError(f"Source '{name}' contains no supported images under {root}")

    records: list[dict[str, Any]] = []
    unresolved: list[str] = []
    for image in images:
        relative = image.relative_to(root)
        parent_parts = list(relative.parts[:-1])
        matches = [part for part in reversed(parent_parts) if part.casefold() in mapping]
        if matches:
            original_class = matches[0]
        elif parent_parts:
            # The immediate parent is the safest candidate when the class is
            # absent from the mapping. The mapping stage will then fail closed
            # and report that exact label instead of guessing or skipping it.
            original_class = parent_parts[-1]
        else:
            unresolved.append(relative.as_posix())
            continue
        records.append(
            {
                "source": name,
                "source_path": str(image.resolve()),
                "relative_path": relative.as_posix(),
                "original_class": original_class,
            }
        )
    if unresolved:
        examples = ", ".join(unresolved[:3])
        raise DiscoveryError(
            f"Cannot recognize class directory for source '{name}' ({len(unresolved)} files; e.g. {examples}). "
            "Add the actual class name to its mapping file or adjust the extracted directory layout."
        )
    return records


def discover_all(config: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for source in config.data["dataset"]["sources"]:
        records.extend(discover_source(config.raw_root, source, config.repo_root))
    return records
