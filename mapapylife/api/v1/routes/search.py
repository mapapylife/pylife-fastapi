from typing import List

from fastapi import APIRouter

from mapapylife.api.v1.schemas import ZoneResultV1
from mapapylife.models import Zone

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/")
async def search(query: str) -> List[ZoneResultV1]:
    """Search for zones by name"""
    zones = await Zone.filter(name__icontains=query).order_by("id").limit(10)
    results = []

    for zone in zones:
        results.append(ZoneResultV1.from_orm(zone))

    return results
