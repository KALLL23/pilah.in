from pathlib import Path

from app.scripts.seed_data import _read_csv


def test_committed_operational_seeds_are_populated() -> None:
    root = Path(__file__).resolve().parents[2] / "data" / "semarang"

    assert len(_read_csv(root / "facilities.csv")) > 0
    assert (root / "city_boundary.geojson").exists()
    assert (root / "waterways.geojson").exists()
    assert (root / "residential.geojson").exists()
    assert (root / "public_facilities.geojson").exists()
