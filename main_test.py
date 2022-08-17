from typing import Dict
from typing import List
from typing import Set
from typing import Tuple
from unittest import main
from unittest import TestCase

from main import Dex
from main import Pool
from main import PoolToken
from main import Token
from main import Tokens


class SmartOrderRouter:
    """TO BE IMPLEMENTED"""

    dexes: List[Dex] = []
    map_token_pools: Dict[Token, Set[str]] = dict()

    def make_map_token_pools(self):
        result: Dict[Token, Set[str]] = {token: set() for token in Tokens}

        for dex in self.dexes:
            for pool in dex.pools:
                for ptk in pool.tokens:
                    result[ptk.token].add(pool.name)

        self.map_token_pools = result

    def find_best_price_out(
        self, token_in: Token, amount_in: int, token_out: Token
    ) -> Tuple[float, List[Tuple[Dex, float]]]:
        """Return the maximum amount of token out for result
        If not possible, return -1
        """
        return -1, []

    def find_best_price_in(
        self, token_out: Token, amount_out: int, token_in: Token
    ) -> Tuple[float, List[Tuple[Dex, float]]]:
        """Return the minimum amount of token in for result
        If not possible, return -1
        """
        return -1, []


class AlgoTest(TestCase):
    sor: SmartOrderRouter

    def setUp(self) -> None:
        self.sor = SmartOrderRouter()
        print("\n======================== TEST CASE =====================\n")

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

        tk3 = PoolToken(token="BTC", amount=200)
        tk4 = PoolToken(token="ETH", amount=1100)
        pool2 = Pool("p1", 0.01, [tk3, tk4])
        metaswap = Dex(name="Metaswap", pools=[pool2], gas=0.4)

        self.sor.dexes = [uniswap, metaswap]

        self.sor.find_best_price_out("ETH", 2, "BTC")


if __name__ == "__main__":
    main(verbosity=2)
