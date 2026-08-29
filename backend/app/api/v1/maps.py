from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.db.session import get_db
from app.repositories.maps import MapRepository, feature_collection, point_feature
from app.schemas.maps import GeoJSONFeatureCollection

router = APIRouter(prefix="/api/v1/map", tags=["map"])


@router.get("/reports", response_model=GeoJSONFeatureCollection)
async def map_reports(
    include_resolved: bool = Query(default=False),
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> dict:
    rows = await MapRepository(session).report_features(user_id, include_resolved=include_resolved)
    return feature_collection(
        [
            point_feature(
                row["id"],
                row.pop("longitude"),
                row.pop("latitude"),
                {
                    "status": row["status"],
                    "risk_score": float(row["risk_score"]),
                    "risk_level": row["risk_level"],
                    "risk_reasons": row["risk_reasons"],
                    "created_at": row["created_at"].isoformat(),
                },
            )
            for row in rows
        ]
    )


@router.get("/facilities", response_model=GeoJSONFeatureCollection)
async def map_facilities(
    _user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> dict:
    rows = await MapRepository(session).facility_features()
    return feature_collection(
        [
            point_feature(
                row["id"],
                row["longitude"],
                row["latitude"],
                {
                    "name": row["name"],
                    "facility_type": row["facility_type"],
                    "address": row["address"],
                    "accepted_categories": list(row["categories"]),
                },
            )
            for row in rows
        ]
    )


@router.get("/hotspots", response_model=GeoJSONFeatureCollection)
async def map_hotspots(
    _user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> dict:
    rows = await MapRepository(session).hotspots()
    return feature_collection(
        [
            point_feature(
                row["cluster_id"],
                row["longitude"],
                row["latitude"],
                {
                    "cluster_id": row["cluster_id"],
                    "report_count": int(row["report_count"]),
                    "average_risk_score": round(float(row["average_risk_score"]), 2),
                    "highest_risk_level": row["highest_risk_level"],
                    "first_seen": row["first_seen"].isoformat(),
                    "last_seen": row["last_seen"].isoformat(),
                },
            )
            for row in rows
        ]
    )
