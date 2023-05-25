from typing import Annotated, List

from fastapi import APIRouter, Query
from tortoise.transactions import in_transaction

from mapapylife.api.v1.schemas import SearchResultV1
from mapapylife.models import get_search_query

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/")
async def search(query: str, limit: Annotated[int, Query(ge=1, le=100)] = 10) -> List[SearchResultV1]:
    """Search for zones and houses by name"""
    async with in_transaction() as conn:
        results = await conn.execute_query_dict(
            get_search_query("zones", "houses"),
            [query, limit],
        )

    return results
