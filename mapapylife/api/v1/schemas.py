from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional, Tuple, Union
from typing_extensions import Self

from pydantic import field_validator, ConfigDict, BaseModel, Field
from pydantic.networks import HttpUrl

Point = Tuple[int, int]
Polygon = List[Point]
MultiPolygon = List[Polygon]


class LocationV1(BaseModel):
    id: int
    name: str
    root: Optional[str] = Field(None, alias="root_name")
    model_config = ConfigDict(populate_by_name=True)

    @field_validator("root", mode="before")
    def field_as_obj(cls, v):
        if isinstance(v, str):
            return v

        return str(v) if v else None


class OwnerV1(BaseModel):
    id: int
    login: str = Field(alias="name")
    premium: Optional[datetime] = None
    model_config = ConfigDict(populate_by_name=True)


class OrganizationV1(BaseModel):
    id: int
    name: str
    logo_url: Optional[HttpUrl] = None


class HouseV1(BaseModel):
    id: int
    x: float
    y: float
    title: str
    location: Optional[LocationV1] = None
    owner: Optional[OwnerV1] = None
    organization: Optional[OrganizationV1] = None
    price: Optional[Decimal] = None
    expires: Optional[datetime] = None
    last_update: datetime


class HousesResponseV1(BaseModel):
    data: List[HouseV1]
    last_update: Optional[datetime] = None


class BlipV1(BaseModel):
    id: int
    x: float
    y: float
    name: str
    icon: str


class BlipsResponseV1(BaseModel):
    data: List[BlipV1]


class EventV1(BaseModel):
    id: int
    x: float
    y: float
    name: str
    location: LocationV1
    description: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    post_url: HttpUrl


class EventsResponseV1(BaseModel):
    data: List[EventV1]


class ZoneV1(BaseModel):
    id: int
    name: str
    description: str
    points: Union[Polygon, MultiPolygon]


class ZonesResponseV1(BaseModel):
    data: List[ZoneV1]


class LookupResultV1(BaseModel):
    zone_name: Optional[str] = None
    city_name: Optional[str] = None

    @classmethod
    def model_validate(cls, obj: Any, *, strict: bool | None = None, from_attributes: bool | None = None, context: Any | None = None) -> Self:
        obj.zone_name = obj.name if obj.root else None
        obj.city_name = obj.root.name if obj.root else obj.name
        return super().model_validate(obj, strict=strict, from_attributes=from_attributes, context=context)


class SearchResultV1(BaseModel):
    id: int
    name: str
    group_: str = Field(alias="group")
    similarity: float
    highlighted: str
    model_config = ConfigDict(populate_by_name=True)
