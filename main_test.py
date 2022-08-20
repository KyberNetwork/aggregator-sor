from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from unittest import main
from unittest import TestCase

from pprint import pprint

from main import Dex
from main import Pool
from main import PoolToken
from main import Token
from main import Tokens


class SmartOrderRouter:
    """TO BE IMPLEMENTED"""

    _dexes: Optional[List[Dex]] = None
    map_token_pools: Optional[Dict[Token, List[Tuple[str, float]]]] = None

    @property
    def dexes(self):
        return self._dexes

    @dexes.setter
    def dexes(self, dexes: List[Dex]):
        self._dexes = dexes
        self._make_map_token_pools(self._dexes)

    def _make_map_token_pools(self, dexes: List[Dex]):
        result: Dict[Token, List[Any]] = {token: [] for token in Tokens}
        for dex in dexes:
            for pool in dex.pools:
                for ptk in pool.tokens:
                    result[ptk.token].append((pool.name, ptk.weight))
                    result[ptk.token].sort(key=lambda t: t[1], reverse=True)

        self.map_token_pools = result

    def edges(self):
        assert self.dexes
        result = {}
        for d in self.dexes:
            for p in d.pools:
                for t in p.tokens:
                   to_tokens = [tt.token for tt in p.tokens if tt != t]

                   if t.token not in result:
                       result.update({t.token: {}})

                   for ttk in to_tokens:
                       if ttk not in result[t.token]:
                           result[t.token].update({ttk: set()})

                       result[t.token][ttk].add(p.name)
        return result


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

        self.sor.dexes = [uniswap, metaswap, luaswap]
        print(self.sor.map_token_pools)

        self.sor.find_best_price_out("ETH", 2, "BTC")


        pprint(self.sor.edges(), indent=4, width=2)


if __name__ == "__main__":
    main(verbosity=2)
