from pydantic import BaseModel, ConfigDict
from typing import Generic, TypeVar
from datetime import datetime
import uuid

DataT = TypeVar("DataT")


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class IDMixin(BaseSchema):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseSchema):
    page: int = 1
    size: int = 50
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        return self.size


class PaginatedResponse(BaseSchema, Generic[DataT]):
    items: list[DataT]
    total: int
    page: int
    size: int
    pages: int
    
    @classmethod
    def create(cls, items: list[DataT], total: int, params: PaginationParams) -> "PaginatedResponse[DataT]":
        pages = (total + params.size - 1) // params.size
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )


class GeoJSONFeature(BaseSchema):
    type: str = "Feature"
    geometry: dict
    properties: dict


class GeoJSONFeatureCollection(BaseSchema):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]