from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from tortoise import Tortoise, connections

from mapapylife.api import v1
from mapapylife.config import get_settings
from mapapylife.routes import index, widget


def get_application() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        debug=settings.debug,
        title="Mapa Play Your Life API",
        description="Interaktywna mapa serwera Play Your Life v2, sprawdź Twój cel oraz zobacz dostępne domy.",
        version="2.0",
        license_info={
            "name": "GPLv3 License",
            "url": "https://github.com/mapapylife/pylife-fastapi/blob/master/LICENSE",
        },
        docs_url="/docs/",
        redoc_url="/redoc/",
        openapi_url="/api/openapi.json",
    )

    @app.middleware("http")
    async def add_cache_control_header(request: Request, call_next):
        response = await call_next(request)

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache"

        return response

    @app.on_event("startup")
    async def startup_event():
        await Tortoise.init(db_url=settings.db_url, modules={"models": ["mapapylife.models"]})

    @app.on_event("shutdown")
    async def shutdown_event():
        await connections.close_all()

    @app.get("/healthcheck", include_in_schema=False)
    async def get_healthcheck():
        return {
            "success": True,
            "message": "healthy",
        }

    app.include_router(v1.router)
    app.include_router(index.router)
    app.include_router(widget.router)

    app.mount("/static", StaticFiles(directory="static"), name="static")
    return app


app = get_application()
