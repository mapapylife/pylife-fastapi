from fastapi import APIRouter, HTTPException
from shapely import Point

from mapapylife.api.v1.schemas import LookupResultV1
from mapapylife.models import Zone

router = APIRouter(prefix="/lookup", tags=["lookup"])


@router.get("/")
async def lookup(x: float, y: float, raw: bool = False) -> LookupResultV1:
    """Lookup a zone by coordinates"""
    zones = await Zone.all().order_by("root_id").prefetch_related("root")
    point = Point(x, y) if raw else Point(x - 3000, y + 3000)

    for zone in zones:
        if point in zone:
            return LookupResultV1.from_orm(zone)

    raise HTTPException(status_code=404, detail="Zone not found")
