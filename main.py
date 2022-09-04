import asyncio

import typer

from repos import PolygonPoolRepository
from repos import Redis
from settings import Settings
from settings import settings

cli = typer.Typer()

redis = None
loop = None

pool_repo_polygon = None


@cli.command()
def keys():
    global redis, pool_repo_polygon
    assert redis
    assert loop
    assert pool_repo_polygon
    pools = loop.run_until_complete(pool_repo_polygon.read_pools())
    print(pools)


def startup(settings: Settings):
    global redis, pool_repo_polygon
    redis = Redis.init(settings.REDIS_HOST)
    pool_repo_polygon = PolygonPoolRepository(redis)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    startup(settings)
    cli()
