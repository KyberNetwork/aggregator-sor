from test.utils import debug
from typing import Any
from typing import List
from unittest import TestCase

from terminaltables import AsciiTable

from sor import calc_amount_out_on_consecutive_edges
from sor import determine_token_pair_pools
from sor import Dex
from sor import find_paths
from sor import map_pool_by_name
from sor import path_to_edges
from sor import Pool
from sor import PoolToken


def show_table(table: List[List[Any]]):
    print(AsciiTable(table).table)


class SwapAlgoTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print("----------------------------------------------------------")
        print("********* Optimized Swap *********************************")

    def setUp(self) -> None:
        debug()

    def test_case(self):
        tk1 = PoolToken(token="BTC", amount=200)
        tk2 = PoolToken(token="ETH", amount=2000)
        pool1 = Pool("pool1", 0.01, [tk1, tk2])
        uniswap = Dex(name="Uniswap", pools=[pool1], gas=0.2)

        tk3 = PoolToken(token="BTC", amount=80)
        tk4 = PoolToken(token="ETH", amount=900)
        pool2 = Pool("pool2", 0.01, [tk3, tk4])
        metaswap = Dex(name="Metaswap", pools=[pool2], gas=0.4)

        tk5 = PoolToken(token="USDC", amount=10000)
        tk6 = PoolToken(token="BTC", amount=11)
        tk7 = PoolToken(token="KNC", amount=1100)
        pool3 = Pool("pool3", 0.01, [tk5, tk6, tk7])
        luaswap = Dex(name="Luaswap", pools=[pool3], gas=0.3)

        tk8 = PoolToken(token="USDC", amount=200)
        tk9 = PoolToken(token="ETH", amount=110)
        pool4 = Pool("pool4", 0.01, [tk8, tk9])
        vuswap = Dex(name="Vuswap", pools=[pool4], gas=0.3)

        tk10 = PoolToken(token="SOL", amount=2000)
        tk11 = PoolToken(token="ETH", amount=1100)
        pool5 = Pool("pool5", 0.01, [tk10, tk11])
        kyberswap = Dex(name="Kyberswap", pools=[pool5], gas=0.3)

        dexes = [uniswap, metaswap, luaswap, vuswap, kyberswap]
        token_pairs_pools = determine_token_pair_pools(dexes)
        pools, pool_map = map_pool_by_name(dexes)

        assert len(pools) == 5
        assert len(pool_map) == 5
        assert len(token_pairs_pools) == 5

        assert pool1.name in token_pairs_pools["BTC"]["ETH"]
        assert pool2.name in token_pairs_pools["BTC"]["ETH"]

        # pprint(token_pairs_pools, width=-1)

        amount_in = 100
        print(f"\nSWAPPING {amount_in} BTC to ETH")

        debug()

        paths = find_paths(
            "BTC",
            "ETH",
            pools,
            token_pairs_pools,
        )

        print("\n** SINGLE ROUTE CALCULATION", end=" ")
        print("(amount-in -> amount-out on each route)")

        table = [["Route", "Amount-In", "Amount-Out", "Splits"]]

        for path in paths:
            edges = path_to_edges(path, token_pairs_pools, pool_map)
            amount_out, splits, _ = calc_amount_out_on_consecutive_edges(edges, amount_in)
            row = ["->".join(path), amount_in, amount_out, splits]
            table.append(row)
            debug(lambda: show_table(table))

        show_table(table)

        # print("\n---------------------- MULTI ROUTE CALCULATION (AUTO-ROUTER)")
        # max_out, route_splits = calc_amount_out_on_multi_routes(
        #     paths, amount_in, token_pairs_pools, pool_map, optimal_lv=10
        # )
        # print("Optimized AMOUNT_OUT =", max_out, route_splits)

        # check_out = 0
        # check_in = 0
        # for idx, split in enumerate(route_splits):
        #     route = paths[idx]
        #     value, splits, pool_names = calc_amount_out_on_single_route(
        #         route, split, token_pairs_pools, pool_map
        #     )
        #     print("->".join(route), "\n======>", value, splits, pool_names)
        #     check_out += value
        #     check_in += split

        # assert check_out == max_out
        # assert check_in == amount_in
