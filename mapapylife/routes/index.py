from fastapi import APIRouter, Request, Response
from starlette.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="mapapylife/templates")


@router.get("/", include_in_schema=False)
async def get_index(request: Request) -> Response:
    return templates.TemplateResponse("index.jinja2", context={"request": request})
