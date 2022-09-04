from repos.redis import Redis


class PolygonPoolRepository:
    def __init__(self, redis: Redis):
        self._r = redis

    async def read_pools(self):
        keys = await self._r.get_all_keys(":pairs:0x*")

        pools = []

        for key in keys[:10]:
            tokens = set(key[7:].split("-"))
            pool_addresses = await self._r.get_key(key)
            pairs_pools = []

            for address in pool_addresses:
                pairs_pools.append({address: tokens})

            pools += pairs_pools

        return pools
