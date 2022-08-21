from pprint import pprint
from typing import List
from unittest import main
from unittest import TestCase

from main import Dex
from main import Pool
from main import PoolToken
from main import SwapRoute
from sor import SmartOrderRouter


class AlgoTest(TestCase):
    sor: SmartOrderRouter

    def setUp(self) -> None:
        self.sor = SmartOrderRouter()

    def test_case_0(self):
        tokens = [
            PoolToken(token="USDC", amount=50000),
            PoolToken(token="USDT", amount=50000),
        ]

        pool = Pool(name="x", fee=0.01, tokens=tokens)

        # Test confirm valid reserve
        assert pool.k == tokens[0].reserve * tokens[1].reserve == 2_500_000_000

        # Test invalid swaps (either token not found in pool)
        expect = (0, 0)
        invalid_swap = pool.swap("USDT", 1, "ETH")
        assert invalid_swap == expect
        invalid_swap = pool.swap("ETH", 1, "USDT")
        assert invalid_swap == expect
        invalid_swap = pool.swap("USDT", 1, "USDT")
        assert invalid_swap == expect
        invalid_swap = pool.swap("ETH", 1, "ETH")
        assert invalid_swap == expect

        # Test valid swap
        expect = (7000, 6086.421921658177)
        result = pool.swap("USDT", 7000, "USDC")
        assert expect == result

        expect = (7, 6.929039635106574)
        result = pool.swap("USDT", 7, "USDC")
        assert expect == result

        print("\n Before swap\n", pool)
        pool.swap("USDT", 7000, "USDC", do_swap=True)
        print("\n After swap\n", pool)

        pool.swap("USDT", 10000000000, "USDC", do_swap=True)
        print("\n Swap with excessive amount\n", pool)

    def test_case_1(self):
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

        self.sor.dexes = [uniswap, metaswap, luaswap, vuswap, kyberswap]
        print(self.sor.map_token_pools)

        self.sor.find_best_price_out("ETH", 2, "BTC")

        edge_map, edges = self.sor.token_graph
        pprint(edge_map, indent=4, width=2)
        print(edges)

        routes = self.sor.find_routes("TOMO", "ETH", hop_limit=3)
        print("\n-------- SWAPPING ROUTES TOMO->ETH\n", routes)

        swap_routes: List[SwapRoute] = []

        test_amount_in = 50

        for route in routes:
            swap_route = self.sor.find_routes_per_path(route, test_amount_in)
            swap_routes.append(swap_route)

        swap_routes.sort(key=lambda sr: sr.amount_out, reverse=True)

        print("** Swap-Routes, sorted by amount_out")
        for route in swap_routes:
            print(route)

        optimal_level = 5
        print("\n--------------- SPLITTING ROUTES", end="  ")
        print(f"(optimal_level={optimal_level})")
        max_amount, divides = self.sor.split_routes(
            swap_routes,
            optimal_level=optimal_level,
        )
        print("-MaxAmount:", max_amount, "\n-Splits", divides, "\n")

        # testing splits
        out = 0
        for nth, divide in enumerate(divides):
            swap_routes[nth].update_amount_in(divide)
            out += swap_routes[nth].amount_out

        out = round(out, 5)
        swap_routes[0].update_amount_in(test_amount_in)
        print(max_amount, out, swap_routes[0].amount_out)
        assert max_amount == out
        assert out > swap_routes[0].amount_out


if __name__ == "__main__":
    try:
        main(verbosity=2)
    except Exception:
        pass
