from fastapi import APIRouter

from mapapylife.api.v1.routes import lookup, points, search

router = APIRouter(prefix="/api/v1")
router.include_router(lookup.router)
router.include_router(points.router)
router.include_router(search.router)
