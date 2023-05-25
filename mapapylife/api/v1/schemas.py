from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, validator
from pydantic.networks import HttpUrl

Point = Tuple[int, int]
Polygon = List[Point]
MultiPolygon = List[Polygon]


class HouseV1(BaseModel):
    id: int
    x: float
    y: float
    title: str
    location: str
    owner: Optional[str]
    price: Optional[Decimal]
    expires: Optional[datetime]
    last_update: datetime

    class Config:
        orm_mode = True

    @validator("location", "owner", pre=True)
    def field_as_obj(cls, v):
        if isinstance(v, str):
            return v

        return str(v) if v else None


class HousesResponseV1(BaseModel):
    data: List[HouseV1]
    last_update: Optional[datetime]


class BlipV1(BaseModel):
    id: int
    x: float
    y: float
    name: str
    icon: str

    class Config:
        orm_mode = True


class BlipsResponseV1(BaseModel):
    data: List[BlipV1]


class EventV1(BaseModel):
    id: int
    x: float
    y: float
    name: str
    location: str
    description: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    post_url: HttpUrl

    class Config:
        orm_mode = True

    @validator("location", pre=True)
    def field_as_obj(cls, v):
        if isinstance(v, str):
            return v

        return str(v) if v else None


class EventsResponseV1(BaseModel):
    data: List[EventV1]


class ZoneV1(BaseModel):
    id: int
    name: str
    description: str
    points: Union[Polygon, MultiPolygon]

    class Config:
        orm_mode = True


class ZonesResponseV1(BaseModel):
    data: List[ZoneV1]


class LookupResultV1(BaseModel):
    zone_name: Optional[str]
    city_name: Optional[str]

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj: Any) -> "LookupResultV1":
        obj.zone_name = obj.name if obj.root else None
        obj.city_name = obj.root.name if obj.root else obj.name
        return super().from_orm(obj)


class SearchResultV1(BaseModel):
    id: int
    name: str
    group_: str = Field(alias="group")
    similarity: float
    highlighted: str

    class Config:
        allow_population_by_field_name = True
