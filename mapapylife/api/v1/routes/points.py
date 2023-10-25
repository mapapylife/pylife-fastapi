from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from pypika import Parameter
from tortoise.expressions import Q

from mapapylife.api.v1.schemas import (
    BlipV1,
    BlipsResponseV1,
    EventV1,
    EventsResponseV1,
    HouseV1,
    HousesResponseV1,
    ZoneV1,
    ZonesResponseV1,
)
from mapapylife.models import Blip, Event, House, Zone

router = APIRouter(prefix="/points", tags=["points"])


@router.get("/houses")
async def get_houses(raw: bool = False, last_update: Optional[datetime] = None) -> HousesResponseV1:
    """Get all houses"""
    houses = House.all().order_by("id").prefetch_related("location", "location__root", "owner", "organization")

    if last_update:
        houses = houses.filter(last_update__gt=last_update)

    houses = await houses
    data = []

    for house in houses:
        if not raw:
            house.x = 3000 + house.x
            house.y = 3000 - house.y

        data.append(HouseV1.from_orm(house))

    last_update = max(houses, key=lambda h: h.last_update).last_update if houses else None
    return HousesResponseV1(data=data, last_update=last_update)


@router.get("/blips")
async def get_blips(raw: bool = False) -> BlipsResponseV1:
    """Get all blips"""
    blips = await Blip.all().order_by("id")
    data = []

    for blip in blips:
        if not raw:
            blip.x = 3000 + blip.x
            blip.y = 3000 - blip.y

        data.append(BlipV1.from_orm(blip))

    return BlipsResponseV1(data=data)


@router.get("/events")
async def get_events(raw: bool = False) -> EventsResponseV1:
    """Get all events"""
    events = await Event.filter(Q(end_date__gt=Parameter("NOW()")) | Q(end_date__isnull=True)).order_by("id").prefetch_related("location", "location__root")
    data = []

    for event in events:
        if not raw:
            event.x = 3000 + event.x
            event.y = 3000 - event.y

        data.append(EventV1.from_orm(event))

    return EventsResponseV1(data=data)


@router.get("/zones")
async def get_zones(raw: bool = False) -> ZonesResponseV1:
    """Get all zones"""
    zones = await Zone.all().order_by("id")
    data = []

    for zone in zones:
        if not raw:
            for i, polygon in enumerate(zone.points):
                if len(polygon) == 2:
                    zone.points[i] = (3000 + polygon[0], 3000 - polygon[1])
                else:
                    zone.points[i] = [(3000 + point[0], 3000 - point[1]) for point in polygon]

        data.append(ZoneV1.from_orm(zone))

    return ZonesResponseV1(data=data)
