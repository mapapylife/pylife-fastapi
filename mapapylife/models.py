from functools import lru_cache
from typing import Union

from shapely import Point, Polygon, MultiPolygon
from tortoise.models import Model
from tortoise import fields


def get_search_query(*args: str) -> str:
    raw_query = (
        "SELECT id, name, group_, tsv, "
        "similarity(name, $1) AS similarity, ts_headline('simple', name, query) AS highlighted FROM ("
    )

    # args contain table names, so we can use them to build the query
    for i, index in enumerate(args):
        raw_query += (
            f"SELECT id, name, '{index}' AS group_, tsv, CASE WHEN $1 = '' THEN '' "
            f"ELSE to_tsquery('simple', CAST(plainto_tsquery('simple', $1) AS text) || ':*') "
            f"END AS query FROM map_index_{index}"
        )

        # Add UNION ALL if not last index
        if i < len(args) - 1:
            raw_query += " UNION ALL "

    raw_query += ") AS combined WHERE tsv @@ query ORDER BY similarity DESC LIMIT $2;"
    return raw_query


class House(Model):
    id = fields.IntField(pk=True)
    x = fields.FloatField(null=False)
    y = fields.FloatField(null=False)
    title = fields.CharField(max_length=255, null=False)
    location = fields.ForeignKeyField("models.Zone", null=True)
    owner = fields.ForeignKeyField("models.Player", on_delete=fields.SET_NULL, null=True)
    organization = fields.ForeignKeyField("models.Organization", on_delete=fields.SET_NULL, null=True)
    price = fields.DecimalField(max_digits=10, decimal_places=2, null=False)
    expires = fields.DatetimeField(null=True)
    last_update = fields.DatetimeField(null=False, auto_now=True)

    # Dict of fields to be updated from API
    api_fields = {
        "title": "title",
        "owner_id": "owner",
        "organization_id": "organization",
        "price": "price",
        "expires": "expires",
    }

    class Meta:
        table = "map_houses"

    def __str__(self):
        return f"{self.id}. {self.title}"


class Blip(Model):
    id = fields.IntField(pk=True)
    x = fields.FloatField(null=False)
    y = fields.FloatField(null=False)
    name = fields.CharField(max_length=255, null=False)
    icon = fields.CharField(max_length=255, null=False)

    class Meta:
        table = "map_blips"

    def __str__(self):
        return self.name


class Event(Model):
    id = fields.IntField(pk=True)
    x = fields.FloatField(null=False)
    y = fields.FloatField(null=False)
    name = fields.CharField(max_length=255, null=False)
    location = fields.ForeignKeyField("models.Zone", null=False)
    description = fields.TextField(null=False)
    start_date = fields.DatetimeField(null=True)
    end_date = fields.DatetimeField(null=True)
    post_url = fields.TextField(null=False)

    class Meta:
        table = "map_events"

    def __str__(self):
        return self.name


class Zone(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, null=False)
    description = fields.CharField(max_length=255, null=False)
    points = fields.JSONField(null=False)
    root = fields.ForeignKeyField("models.Zone", null=True)

    class Meta:
        table = "map_zones"

    @lru_cache
    def get_polygon(self) -> Union[Polygon, MultiPolygon]:
        if len(self.points[0]) == 2:
            polygon = Polygon(self.points)
        else:
            polygon = MultiPolygon([Polygon(polygon) for polygon in self.points])

        return polygon

    def __contains__(self, item):
        return self.get_polygon().contains(item)

    def __str__(self):
        return self.name

    @staticmethod
    async def get_zone(x: float, y: float) -> "Zone":
        point = Point(x, y)
        city_zone = next(zone for zone in await Zone.filter(root_id__isnull=True) if point in zone)

        for zone in await Zone.filter(root_id=city_zone.id):
            if point in zone:
                return zone

        return city_zone


class Player(Model):
    id = fields.IntField(pk=True)
    login = fields.CharField(max_length=22, null=False)
    premium = fields.DatetimeField(null=True)
    registered = fields.DatetimeField(null=False)
    last_online = fields.DatetimeField(null=False)

    # Dict of fields to be updated from API
    api_fields = {
        "login": "login",
        "premium": "premium",
        "last_online": "last_online",
    }

    class Meta:
        table = "map_players"

    def __str__(self):
        return self.login


class Organization(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, null=False)
    tag = fields.CharField(max_length=255, null=False)
    logo_url = fields.TextField(null=True)
    registered = fields.DatetimeField(null=False)

    # Dict of fields to be updated from API
    api_fields = {
        "name": "name",
        "tag": "tag",
        "logo_url": "logo",
    }

    class Meta:
        table = "map_organizations"

    def __str__(self):
        return self.name
