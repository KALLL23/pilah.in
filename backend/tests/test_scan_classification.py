import pytest

from app.ai.classification import ClassificationError, normalize_model_label


@pytest.mark.parametrize(
    ("model_label", "expected"),
    [
        ("plastic", "PLASTIC"),
        ("paper_cardboard", "PAPER_CARDBOARD"),
        ("electronic-special", "ELECTRONIC_SPECIAL"),
        ("residual mixed", "RESIDUAL_MIXED"),
    ],
)
def test_normalizes_model_labels_to_database_taxonomy(model_label: str, expected: str) -> None:
    assert normalize_model_label(model_label) == expected


def test_rejects_model_label_outside_fixed_taxonomy() -> None:
    with pytest.raises(ClassificationError, match="Unsupported classification label"):
        normalize_model_label("PET_BOTTLE")
