import os
import re

from aiohttp import ClientSession
from pylife_api import PylifeAPIClient
from shapely.geometry import box
from shapely.ops import unary_union
from tortoise import Tortoise, run_async

from mapapylife.models import Blip, House, Player, Organization, Zone

MTA_ZONENAMES = "https://github.com/multitheftauto/mtasa-blue/raw/master/Shared/mods/deathmatch/logic/CZoneNames.cpp"
ZONE_REGEX = r"{(-?\d+), (-?\d+), (?:-?\d+), (-?\d+), (-?\d+), (?:-?\d+), \"(.*?)\"}"

# https://github.com/multitheftauto/mtasa-blue/blob/master/Shared/mods/deathmatch/logic/CZoneNames.cpp#L15-L24
CITY_NAMES = [
    "Tierra Robada",
    "Bone County",
    "Las Venturas",
    "San Fierro",
    "Red County",
    "Whetstone",
    "Flint County",
    "Los Santos",
]

# Define exceptions for zones
exceptions = {
    # https://gta.fandom.com/pl/wiki/Mulholland
    102: 90,
}


async def generate_zones():
    print("Generating table for zones...")
    zones = {}

    # Load zone names from file
    with open("data/zonenames.txt", encoding="utf-8") as f:
        for line in f.readlines():
            zone_id = int(line.split(",")[0])
            zones[zone_id] = {
                "name": line.split(",")[1],
                "description": line.split(",")[2].rstrip(),
                "points": [],
            }

    # Download zone data from MTA repository
    async with ClientSession() as session:
        async with session.get(MTA_ZONENAMES) as resp:
            resp.raise_for_status()
            response = await resp.text()

            for line in response.splitlines():
                matches = re.findall(ZONE_REGEX, str(line))
                if matches:
                    row = matches[0]
                    zone_id = next((index for index, zone in zones.items() if zone["name"] == row[4]))
                    zones[zone_id]["points"].append(box(int(row[0]), int(row[1]), int(row[2]), int(row[3])))

    # Now we iterate through every zone and save to database
    for index, zone in zones.items():
        union = unary_union(zone["points"])

        # Check if union has more than one polygon
        if union.geom_type == "MultiPolygon":
            points = [[(int(point[0]), int(point[1])) for point in polygon.exterior.coords] for polygon in union.geoms]
        else:
            points = [(int(point[0]), int(point[1])) for point in union.exterior.coords]

        await Zone.create(id=index, name=zone["name"], description=zone["description"], points=points)


async def generate_root_zone_ids():
    # First we load city zones
    city_zones = {
        zone.id: zone.get_polygon()
        for zone in await Zone.filter(name__in=CITY_NAMES).order_by("id").distinct()
    }

    # Define function to calculate area
    def calculate_area(z1, z2):
        return z1.intersection(z2).area / z1.area

    # Now we iterate though every zone and check which city zone it belongs
    for zone in await Zone.filter(name__not_in=CITY_NAMES).order_by("id").distinct():
        polygon = zone.get_polygon()

        # Check if zone is in exceptions
        if zone.id in exceptions:
            zone.root_id = exceptions[zone.id]
        else:
            for city_id, city_polygon in city_zones.items():
                if polygon.intersects(city_polygon) and calculate_area(polygon, city_polygon) > 0.5:
                    zone.root_id = city_id
                    break

        await zone.save()


async def generate_organizations(client: PylifeAPIClient):
    print("Generating table for organizations...")

    # Pull organizations from API and save them to database
    for organization in await client.get_organizations():
        await Organization.create(
            id=organization.id,
            name=organization.name,
            tag=organization.tag,
            logo_url=organization.logo,
            registered=organization.registered,
        )


async def generate_players(client: PylifeAPIClient):
    print("Generating table for players...")

    # Pull players from API and save them to database
    for player in await client.get_players():
        await Player.create(
            id=player.id,
            login=player.login,
            premium=player.premium,
            registered=player.registered,
            last_online=player.last_online,
        )


async def generate_houses(client: PylifeAPIClient):
    print("Generating table for houses...")

    # Pull houses from API and save them to database
    for house in await client.get_houses():
        # Get zone from house position
        zone = await Zone.get_zone(house.position.x, house.position.y)

        await House.create(
            id=house.id,
            x=house.position.x,
            y=house.position.y,
            title=house.title,
            location_id=zone.id,
            owner_id=house.owner,
            organization_id=house.organization,
            price=house.price,
            expires=house.expires,
        )


async def generate_blips():
    print("Generating table for blips...")

    # Load blips from file
    with open("data/blips.txt", encoding="utf-8") as f:
        for line in f.readlines():
            line = line.rstrip()

            if line == "" or line.startswith("#"):
                continue

            blip = line.split(",")
            await Blip.create(x=blip[0], y=blip[1], name=blip[2], icon=blip[3])


async def run():
    db_url = os.getenv("DB_URL", "sqlite://db.sqlite3")

    # Connect to database and generate schemas
    await Tortoise.init(db_url=db_url, modules={"models": ["mapapylife.models"]})
    await Tortoise.generate_schemas()

    # Generate zones
    await generate_zones()
    await generate_root_zone_ids()

    # Connect to Pylife API and generate tables
    async with PylifeAPIClient(auth_token=os.environ["AUTH_TOKEN"]) as client:
        await generate_organizations(client)
        await generate_players(client)
        await generate_houses(client)

    # Generate blips
    await generate_blips()

    # Close database connection
    await Tortoise.close_connections()


if __name__ == "__main__":
    run_async(run())
