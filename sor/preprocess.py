from typing import Callable
from typing import Dict
from typing import List
from typing import Set
from typing import Tuple

from .models import Dex
from .models import Pool
from .models import Token


def each_pool(dexes: List[Dex], f: Callable[[Pool], None]):
    for dex in dexes:
        for pool in dex.pools:
            f(pool)


def map_pool_by_name(dexes: List[Dex]) -> Tuple[List[Pool], Dict[str, Pool]]:
    poolmap: Dict[str, Pool] = {}
    poollist: List[Pool] = []

    def handle_pool(pool: Pool):
        nonlocal poollist, poolmap
        poolmap.update({pool.name: pool})
        poollist.append(pool)

    each_pool(dexes, handle_pool)
    return poollist, poolmap


TokenPairsPools = Dict[Token, Dict[Token, Set[str]]]


def determine_token_pair_pools(dexes: List[Dex]) -> TokenPairsPools:
    pairs: TokenPairsPools = {}

    def handle_pool(pool: Pool):
        nonlocal pairs
        for from_token in pool.tokens:
            if from_token.token not in pairs:
                pairs.update({from_token.token: dict()})

            for to_token in pool.tokens:
                if to_token.token == from_token.token:
                    continue

                if to_token.token not in pairs[from_token.token]:
                    pairs[from_token.token].update({to_token.token: set()})

                pairs[from_token.token][to_token.token].add(pool.name)

    each_pool(dexes, handle_pool)
    return pairs
