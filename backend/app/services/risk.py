from dataclasses import dataclass

from app.models.models import RiskLevel, WasteVolume

VOLUME_SCORES = {WasteVolume.SMALL: 25, WasteVolume.MEDIUM: 60, WasteVolume.LARGE: 100}


@dataclass(frozen=True)
class RiskResult:
    score: float
    level: RiskLevel
    reasons: list[str]


def persistence_score(confirmations: int) -> int:
    if confirmations <= 0:
        return 0
    if confirmations == 1:
        return 25
    if confirmations == 2:
        return 50
    if confirmations == 3:
        return 75
    return 100


def calculate_risk(
    *,
    waste_volume: WasteVolume,
    organic_presence: bool,
    standing_water: bool,
    drainage_blockage: bool,
    location_vulnerability: int,
    confirmations: int,
) -> RiskResult:
    persistence = persistence_score(confirmations)
    score = round(
        0.25 * VOLUME_SCORES[waste_volume]
        + 0.15 * (100 if organic_presence else 0)
        + 0.20 * (100 if standing_water else 0)
        + 0.20 * (100 if drainage_blockage else 0)
        + 0.10 * max(0, min(100, location_vulnerability))
        + 0.10 * persistence,
        2,
    )
    level = RiskLevel.LOW if score < 40 else RiskLevel.MEDIUM if score < 70 else RiskLevel.HIGH
    reasons: list[str] = []
    if waste_volume == WasteVolume.LARGE:
        reasons.append("Volume sampah besar")
    if organic_presence:
        reasons.append("Sampah organik terdeteksi")
    if standing_water:
        reasons.append("Terdapat genangan air")
    if drainage_blockage:
        reasons.append("Saluran air terhalang")
    if location_vulnerability >= 70:
        reasons.append("Lokasi berada dekat area sensitif")
    elif location_vulnerability >= 40:
        reasons.append("Lokasi berada di area permukiman")
    if confirmations:
        reasons.append(f"Kondisi dikonfirmasi oleh {confirmations} pengguna")
    return RiskResult(score=max(0, min(100, score)), level=level, reasons=reasons)
