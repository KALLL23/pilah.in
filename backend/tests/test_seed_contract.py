from pathlib import Path

from app.scripts.seed_data import _read_csv


def test_committed_operational_seeds_are_intentionally_empty() -> None:
    root = Path(__file__).resolve().parents[2] / "data" / "semarang"

    assert _read_csv(root / "waste_knowledge.csv") == []
    assert _read_csv(root / "facilities.csv") == []
    assert not (root / "city_boundary.geojson").exists()
