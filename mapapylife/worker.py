import asyncio
import logging
import sys
from datetime import datetime

from pylife_api import PylifeAPIClient
from tortoise import Tortoise, connections

from mapapylife.config import get_settings
from mapapylife.models import House, Organization, Player, Zone

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("worker")

# Get settings
settings = get_settings()


async def update_houses():
    # List containing houses to be updated
    updates = []

    # Load current houses from database
    houses = {house.id: house for house in await House.all()}

    # Prefetch player and organization IDs from database
    players = await Player.all().values_list("id", flat=True)
    organizations = await Organization.all().values_list("id", flat=True)

    # Get all houses from API
    async with PylifeAPIClient(auth_token=settings.auth_token) as client:
        logger.info("Pulling houses from API...")

        for house in await client.get_houses():
            # Check if player exists in database
            if house.owner and house.owner not in players:
                logger.info(f"Player with ID {house.owner} not found in database, pulling from API...")
                player = await client.get_player(house.owner)

                # Add player to database
                await Player.create(
                    id=player.id,
                    login=player.login,
                    premium=player.premium,
                    registered=player.registered,
                    last_online=player.last_online,
                )

                # Add player ID to list
                players.append(player.id)

            # Check if organization exists in database
            if house.organization and house.organization not in organizations:
                logger.info(f"Organization with ID {house.organization} not found in database, pulling from API...")
                organization = await client.get_organization(house.organization)

                # Add organization to database
                await Organization.create(
                    id=organization.id,
                    name=organization.name,
                    tag=organization.tag,
                    logo_url=organization.logo,
                    registered=organization.registered,
                )

                # Add organization ID to list
                organizations.append(organization.id)

            # Get current house from database
            old_house = houses.get(house.id)

            if not old_house:
                logger.warning(f'House "{house.title}" with ID {house.id} does not exist in database!')
                updates.append(house)
            else:
                # Check if house has changed
                for field, api_field in House.api_fields.items():
                    if getattr(old_house, field) != getattr(house, api_field):
                        updates.append(house)
                        break

    # Output number of houses to be updated
    if len(updates) > 0:
        logger.info(f"Found {len(updates)} house(s) to be updated.")
    else:
        logger.info("Everything up-to-date, nothing to do.")

    # Update houses
    for house in updates:
        logger.info(f'Updating house "{house.title}" with ID {house.id}...')

        # Prepare default values
        defaults = {
            "name": house.title,
            "owner_id": house.owner,
            "organization_id": house.organization,
            "price": house.price,
            "expires": house.expires,
        }

        # Check if house does not exist in database
        if house.id not in houses:
            logger.info("House does not exist in database, adding new house...")

            # Get zone from house position
            zone = await Zone.get_zone(house.position.x, house.position.y)

            # Add position to default values
            defaults.update({
                "x": house.position.x,
                "y": house.position.y,
                "location_id": zone.id,
            })

        # Update or create house in database
        await House.update_or_create(id=house.id, defaults=defaults)


async def update_players():
    # List containing players to be updated
    updates = []

    # Load current players from database
    players = {player.id: player for player in await Player.all()}

    # Get all players from API
    async with PylifeAPIClient(auth_token=settings.auth_token) as client:
        logger.info("Pulling players from API...")

        for player in await client.get_players():
            # Get current player from database
            old_player = players.get(player.id)

            if not old_player:
                logger.warning(f'Player "{player.login}" with ID {player.id} does not exist in database!')
                updates.append(player)
            else:
                # Check if player has changed
                for field, api_field in Player.api_fields.items():
                    if getattr(old_player, field) != getattr(player, api_field):
                        updates.append(player)
                        break

    # Output number of players to be updated
    if len(updates) > 0:
        logger.info(f"Found {len(updates)} player(s) to be updated.")
    else:
        logger.info("Everything up-to-date, nothing to do.")

    # Update players
    for player in updates:
        logger.info(f'Updating player "{player.login}" with ID {player.id}...')

        # Update player in database
        await Player.update_or_create(
            id=player.id,
            defaults={
                "login": player.login,
                "premium": player.premium,
                "registered": player.registered,
                "last_online": player.last_online,
            },
        )


async def update_organizations():
    # List containing organizations to be updated
    updates = []

    # Load current organizations from database
    organizations = {organization.id: organization for organization in await Organization.all()}

    # Get all organizations from API
    async with PylifeAPIClient(auth_token=settings.auth_token) as client:
        logger.info("Pulling organizations from API...")

        for organization in await client.get_organizations():
            # Get current organization from database
            old_organization = organizations.get(organization.id)

            if not old_organization:
                logger.warning(f'Organization "{organization.name}" with ID {organization.id} does not exist in database!')
                updates.append(organization)
            else:
                # Check if organization has changed
                for field, api_field in Organization.api_fields.items():
                    if getattr(old_organization, field) != getattr(organization, api_field):
                        updates.append(organization)
                        break

    # Output number of organizations to be updated
    if len(updates) > 0:
        logger.info(f"Found {len(updates)} organization(s) to be updated.")
    else:
        logger.info("Everything up-to-date, nothing to do.")

    # Update organizations
    for organization in updates:
        logger.info(f'Updating organization "{organization.name}" with ID {organization.id}...')

        # Update organization in database
        await Organization.update_or_create(
            id=organization.id,
            defaults={
                "name": organization.name,
                "tag": organization.tag,
                "logo_url": organization.logo,
                "registered": organization.registered,
            },
        )


async def run_job(job_name: str):
    # Store start timestamp
    start_time = datetime.now()

    logger.info(f"Cron job started at {start_time}")
    logger.info(f'Running job "{job_name}"...')

    # Connect to database
    await Tortoise.init(db_url=settings.db_url, modules={"models": ["mapapylife.models"]})

    try:
        await globals()[job_name]()
    except asyncio.CancelledError:
        pass

    # Disconnect from database
    await connections.close_all()

    elapsed_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Done! Job finished in {round(elapsed_time, 2)} seconds.")


if __name__ == "__main__":
    # Check if job was specified
    if len(sys.argv) < 2:
        print("No job specified!")
        exit(1)

    asyncio.run(run_job(sys.argv[1]))
