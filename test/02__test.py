from pprint import pprint
from unittest import TestCase

from sor import batch_split
from sor import determine_token_pair_pools
from sor import Dex
from sor import find_edges
from sor import map_pool_by_name
from sor import Pool
from sor import PoolToken
from sor import Splits
from sor import SwapEdge
from sor.algorithm import swap_edge_amount_out


class PreprocessTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print("----------------------------------------------------------")
        print("********* Testing Models *********************************")

    def test_case(self):
        tk1 = PoolToken(token="BTC", amount=20)
        tk2 = PoolToken(token="ETH", amount=100)
        pool1 = Pool("p1", 0.01, [tk1, tk2])
        uniswap = Dex(name="Uniswap", pools=[pool1], gas=0.2)

        tk3 = PoolToken(token="BTC", amount=2000)
        tk4 = PoolToken(token="ETH", amount=1100)
        pool2 = Pool("p2", 0.01, [tk3, tk4])
        metaswap = Dex(name="Metaswap", pools=[pool2], gas=0.4)

        tk5 = PoolToken(token="USDC", amount=2000)
        tk6 = PoolToken(token="BTC", amount=1100)
        tk7 = PoolToken(token="TOMO", amount=1100)
        pool3 = Pool("p3", 0.01, [tk5, tk6, tk7])
        luaswap = Dex(name="Luaswap", pools=[pool3], gas=0.3)

        tk8 = PoolToken(token="USDC", amount=2000)
        tk9 = PoolToken(token="ETH", amount=1100)
        pool4 = Pool("p4", 0.01, [tk8, tk9])
        vuswap = Dex(name="Vuswap", pools=[pool4], gas=0.3)

        tk10 = PoolToken(token="SOL", amount=2000)
        tk11 = PoolToken(token="ETH", amount=1100)
        pool5 = Pool("p5", 0.01, [tk10, tk11])
        kyberswap = Dex(name="Kyberswap", pools=[pool5], gas=0.3)

        dexes = [uniswap, metaswap, luaswap, vuswap, kyberswap]

        pool_list, pool_map = map_pool_by_name(dexes)
        token_pairs_pool = determine_token_pair_pools(dexes)

        assert len(pool_list) == 5
        assert len(pool_map) == 5
        assert len(token_pairs_pool) == 5

        assert pool1.name in token_pairs_pool["BTC"]["ETH"]
        assert pool2.name in token_pairs_pool["BTC"]["ETH"]

        pprint(pool_map, width=-1)
        pprint(token_pairs_pool, width=-1)

        edges = find_edges(
            dexes,
            "BTC",
            "ETH",
            pool_list,
            pool_map,
            token_pairs_pool,
        )
        print(edges)

        print("\n\n", batch_split(10, 2, optimal_lv=10))

        tk12 = PoolToken(token="BTC", amount=40)
        tk13 = PoolToken(token="ETH", amount=30)
        pool6 = Pool("p6", 0.01, [tk12, tk13])
        test_pools, max_out, optimal_splits = [pool1, pool6, pool2], 0, None

        def test_amount(splits: Splits):
            nonlocal test_pools, max_out, optimal_splits
            result = 0

            for idx, part in enumerate(splits):
                result += test_pools[idx].swap("BTC", part, "ETH")

            if result > max_out:
                max_out = result
                optimal_splits = splits

        batch_split(100, len(test_pools), callback=test_amount)
        print("======= RESULT", max_out, optimal_splits)
        print("\n**********************************\n")
        batch_split(100, len(test_pools), callback=test_amount, optimal_lv=10)
        print("======= RESULT", max_out, optimal_splits)
        print("\n**********************************\n")

        swap_edge = SwapEdge(token_in="BTC", token_out="ETH", pools=test_pools)
        max_out, split_percents, pool_names = swap_edge_amount_out(
            swap_edge,
            100,
            optimal_lv=3,
        )

        print("======= SWAP_EDGE", max_out, "__", split_percents, pool_names)
