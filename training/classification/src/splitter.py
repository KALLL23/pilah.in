"""Deterministic stratified, group-aware dataset splitting."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SPLITS = ("train", "val", "test")


class LeakageError(RuntimeError):
    """Raised when any identity, content, or group crosses split boundaries."""


def _rank(seed: int, value: str) -> str:
    return hashlib.sha256(f"{seed}:{value}".encode()).hexdigest()


def assign_splits(records: list[dict[str, Any]], ratios: dict[str, float], seed: int) -> None:
    eligible = [record for record in records if record.get("status") == "valid"]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in eligible:
        groups[str(record["group_id"])].append(record)

    # Assign large groups first. The cost function balances target_class × source
    # strata and total samples, while every group remains indivisible.
    strata_totals = Counter((r["target_class"], r["source"]) for r in eligible)
    desired = {
        split: {stratum: total * float(ratios[split]) for stratum, total in strata_totals.items()}
        for split in SPLITS
    }
    current = {split: Counter() for split in SPLITS}
    split_sizes = Counter()
    desired_sizes = {split: len(eligible) * float(ratios[split]) for split in SPLITS}
    ordered = sorted(groups.items(), key=lambda item: (-len(item[1]), _rank(seed, item[0])))
    for group_id, members in ordered:
        group_counts = Counter((r["target_class"], r["source"]) for r in members)

        def cost(split: str) -> tuple[float, float, str]:
            # Compare the increase in global squared error, not just the final
            # error of the candidate split. This prevents small val/test
            # targets from being filled before the larger training target.
            stratum_delta = sum(
                (
                    (current[split][key] + count - desired[split][key]) ** 2
                    - (current[split][key] - desired[split][key]) ** 2
                )
                / max(1.0, desired[split][key])
                for key, count in group_counts.items()
            )
            size_delta = (
                (split_sizes[split] + len(members) - desired_sizes[split]) ** 2
                - (split_sizes[split] - desired_sizes[split]) ** 2
            ) / max(1.0, desired_sizes[split])
            return stratum_delta + 0.25 * size_delta, split_sizes[split] / max(1.0, desired_sizes[split]), split

        chosen = min(SPLITS, key=cost)
        for record in members:
            record["split"] = chosen
        current[chosen].update(group_counts)
        split_sizes[chosen] += len(members)


def find_leakage(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in ("sha256", "group_id", "image_id"):
        seen: dict[str, set[str]] = defaultdict(set)
        for record in records:
            if record.get("status") == "valid" and record.get("split"):
                seen[str(record[field])].add(str(record["split"]))
        for value, splits in sorted(seen.items()):
            if len(splits) > 1:
                issues.append({"field": field, "value": value, "splits": ",".join(sorted(splits))})
    return issues


def validate_no_leakage(records: list[dict[str, Any]], report_path: Path) -> None:
    issues = find_leakage(records)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["field", "value", "splits"])
        writer.writeheader()
        writer.writerows(issues)
    if issues:
        raise LeakageError(f"Leakage detected ({len(issues)} violations); see {report_path}")
