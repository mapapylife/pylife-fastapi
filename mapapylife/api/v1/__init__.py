from fastapi import APIRouter, Depends
from fastapi_limiter.depends import RateLimiter

from mapapylife.api.v1.routes import lookup, points, search

router = APIRouter(
    prefix="/api/v1",
    dependencies=[
        Depends(RateLimiter(times=45, seconds=60)),
    ],
)

router.include_router(lookup.router)
router.include_router(points.router)
router.include_router(search.router)
