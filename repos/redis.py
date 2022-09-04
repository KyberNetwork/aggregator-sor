from typing import List

from aioredis import from_url
from aioredis.client import Redis as AioRedis


class Redis:
    def __init__(self, r: AioRedis):
        self._r = r

    @classmethod
    def init(cls, url: str):
        redis = from_url(url, encoding="utf-8", decode_responses=True)
        return cls(redis)

    async def get_all_keys(self, pattern: str) -> List[str]:
        keys = await self._r.keys(pattern)
        return keys

    async def get_key(self, key: str) -> List[str]:
        data = await self._r.zrange(key, 0, -1)
        return data
