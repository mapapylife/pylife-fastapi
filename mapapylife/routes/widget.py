import json

from fastapi import APIRouter, HTTPException, Request, Response
from starlette.templating import Jinja2Templates

from mapapylife.models import House

router = APIRouter(prefix="/widget")
templates = Jinja2Templates(directory="mapapylife/templates")


@router.get("/{house_id}", include_in_schema=False)
async def get_house(request: Request, house_id: int) -> Response:
    house = await House.get_or_none(id=house_id).prefetch_related("location", "owner")

    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    data = {
        "id": house.id,
        "x": 3000 + house.x,
        "y": 3000 - house.y,
        "title": house.title,
        "location": house.location.name,
        "owner": house.owner.login if house.owner else None,
        "price": house.price,
        "expires": house.expires,
    }

    return templates.TemplateResponse("widget.jinja2", context={"request": request, "data": json.dumps(data, default=str)})
