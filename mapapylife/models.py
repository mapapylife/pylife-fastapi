from functools import lru_cache
from typing import Union

from shapely import Point, Polygon, MultiPolygon
from tortoise.models import Model
from tortoise import fields


class House(Model):
    id = fields.IntField(pk=True)
    x = fields.FloatField(null=False)
    y = fields.FloatField(null=False)
    name = fields.CharField(max_length=255, null=False)
    location = fields.ForeignKeyField("models.Zone", null=False)
    owner = fields.ForeignKeyField("models.Player", on_delete=fields.SET_NULL, null=True)
    organization = fields.ForeignKeyField("models.Organization", on_delete=fields.SET_NULL, null=True)
    price = fields.FloatField(null=True)
    expires = fields.DatetimeField(null=True)
    last_update = fields.DatetimeField(null=False, auto_now=True)

    class Meta:
        table = "houses"

    def __str__(self):
        return f"{self.id}. {self.name}"


class Blip(Model):
    id = fields.IntField(pk=True)
    x = fields.FloatField(null=False)
    y = fields.FloatField(null=False)
    name = fields.CharField(max_length=255, null=False)
    icon = fields.CharField(max_length=255, null=False)

    class Meta:
        table = "blips"

    def __str__(self):
        return self.name


class Zone(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, null=False)
    description = fields.CharField(max_length=255, null=False)
    points = fields.JSONField(null=False)
    root = fields.ForeignKeyField("models.Zone", null=True)

    class Meta:
        table = "zones"

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

    class Meta:
        table = "players"

    def __str__(self):
        return self.login


class Organization(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, null=False)
    tag = fields.CharField(max_length=255, null=False)
    logo_url = fields.TextField(null=True)
    registered = fields.DatetimeField(null=False)

    class Meta:
        table = "organizations"

    def __str__(self):
        return self.name
