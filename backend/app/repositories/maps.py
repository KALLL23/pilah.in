from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class MapRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def report_features(self, user_id: UUID, *, include_resolved: bool) -> list[dict]:
        query = text(
            """
            SELECT id, status::text AS status, risk_score, risk_level::text AS risk_level,
                   risk_reasons, created_at,
                   ST_Y(location::geometry) AS latitude,
                   ST_X(location::geometry) AS longitude
            FROM waste_reports
            WHERE status IN ('VERIFIED', 'IN_PROGRESS')
               OR (status = 'REPORTED' AND user_id = :user_id)
               OR (:include_resolved AND status = 'RESOLVED')
            ORDER BY created_at DESC, id
            """
        )
        result = await self.session.execute(query, {"user_id": user_id, "include_resolved": include_resolved})
        return [dict(row) for row in result.mappings().all()]

    async def facility_features(self) -> list[dict]:
        query = text(
            """
            SELECT f.id, f.name, f.facility_type::text AS facility_type, f.address,
                   ST_Y(f.location::geometry) AS latitude,
                   ST_X(f.location::geometry) AS longitude,
                   COALESCE(array_agg(wc.code ORDER BY wc.id) FILTER (WHERE wc.code IS NOT NULL), '{}') AS categories
            FROM facilities f
            LEFT JOIN facility_categories fc ON fc.facility_id = f.id
            LEFT JOIN waste_categories wc ON wc.id = fc.category_id
            WHERE f.verified = true AND f.is_active = true AND f.access_scope = 'PUBLIC'
            GROUP BY f.id
            ORDER BY f.name, f.id
            """
        )
        result = await self.session.execute(query)
        return [dict(row) for row in result.mappings().all()]

    async def hotspots(self) -> list[dict]:
        query = text(
            """
            WITH candidates AS (
                SELECT id, risk_score, risk_level, created_at,
                       ST_Transform(location::geometry, 32749) AS metric_geometry
                FROM waste_reports
                WHERE status IN ('VERIFIED', 'IN_PROGRESS')
                  AND created_at >= now() - interval '14 days'
            ), clustered AS (
                SELECT *, ST_ClusterDBSCAN(metric_geometry, eps => 50, minpoints => 3) OVER () AS cluster_id
                FROM candidates
            )
            SELECT cluster_id,
                   ST_X(ST_Transform(ST_Centroid(ST_Collect(metric_geometry)), 4326)) AS longitude,
                   ST_Y(ST_Transform(ST_Centroid(ST_Collect(metric_geometry)), 4326)) AS latitude,
                   count(*) AS report_count,
                   avg(risk_score) AS average_risk_score,
                   CASE max(CASE risk_level WHEN 'HIGH' THEN 3 WHEN 'MEDIUM' THEN 2 ELSE 1 END)
                     WHEN 3 THEN 'HIGH' WHEN 2 THEN 'MEDIUM' ELSE 'LOW' END AS highest_risk_level,
                   min(created_at) AS first_seen,
                   max(created_at) AS last_seen
            FROM clustered
            WHERE cluster_id IS NOT NULL
            GROUP BY cluster_id
            ORDER BY average_risk_score DESC, report_count DESC, cluster_id
            """
        )
        result = await self.session.execute(query)
        return [dict(row) for row in result.mappings().all()]


def feature_collection(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


def point_feature(identifier, longitude: float, latitude: float, properties: dict) -> dict:
    return {
        "type": "Feature",
        "id": str(identifier),
        "geometry": {"type": "Point", "coordinates": [float(longitude), float(latitude)]},
        "properties": properties,
    }
