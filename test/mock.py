from typing import List
from typing import Tuple

from sor import determine_token_pair_pools
from sor import Dex
from sor import map_pool_by_name
from sor import Pool
from sor import PoolToken
from sor.algorithm import PoolMap
from sor.preprocess import TokenPairsPools


def mock() -> Tuple[List[Dex], List[Pool], PoolMap, TokenPairsPools]:
    tk1 = PoolToken(token="BTC", amount=200)
    tk2 = PoolToken(token="ETH", amount=600)
    pool1 = Pool("pool1", 0.01, [tk1, tk2])
    uniswap = Dex(name="Uniswap", pools=[pool1], gas=0.2)

    tk3 = PoolToken(token="BTC", amount=300)
    tk4 = PoolToken(token="ETH", amount=700)
    pool2 = Pool("pool2", 0.01, [tk3, tk4])
    metaswap = Dex(name="Metaswap", pools=[pool2], gas=0.4)

    tk5 = PoolToken(token="USDC", amount=10000)
    tk6 = PoolToken(token="BTC", amount=11)
    tk7 = PoolToken(token="KNC", amount=110)
    pool3 = Pool("pool3", 0.01, [tk5, tk6, tk7])
    luaswap = Dex(name="Luaswap", pools=[pool3], gas=0.3)

    tk8 = PoolToken(token="USDC", amount=10000)
    tk9 = PoolToken(token="ETH", amount=910)
    pool4 = Pool("pool4", 0.01, [tk8, tk9])
    vuswap = Dex(name="Vuswap", pools=[pool4], gas=0.3)

    tk10 = PoolToken(token="SOL", amount=2000)
    tk11 = PoolToken(token="ETH", amount=1100)
    pool5 = Pool("pool5", 0.01, [tk10, tk11])
    kyberswap = Dex(name="Kyberswap", pools=[pool5], gas=0.3)

    dexes = [uniswap, metaswap, luaswap, vuswap, kyberswap]
    token_pairs_pools = determine_token_pair_pools(dexes)
    pools, pool_map = map_pool_by_name(dexes)
    return dexes, pools, pool_map, token_pairs_pools
