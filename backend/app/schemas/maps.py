from typing import Any, Literal

from pydantic import BaseModel, Field


class PointGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: list[float] = Field(min_length=2, max_length=2)


class GeoJSONFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: PointGeometry
    properties: dict[str, Any]


class GeoJSONFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[GeoJSONFeature]
