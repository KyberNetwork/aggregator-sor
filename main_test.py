from typing import Dict
from typing import List
from typing import Set
from typing import Tuple
from unittest import main
from unittest import TestCase

from main import Dex
from main import Edge
from main import Pool
from main import PoolToken
from main import Token
from main import Tokens
from mock import create_dexes


class SmartOrderRouter:
    """TO BE IMPLEMENTED"""

    dexes: List[Dex] = []

    def calculate_token_amount_out_by_pool(
        self, token_in: Token, token_out: Token, pool: Pool
    ):
        if token_in == token_out:
            raise ValueError("TokenIn == TokenOut")

        token_pair = {token_in, token_out}
        pool_token_pairs = [t for t in pool.tokens if t.token in token_pair]

        if len(pool_token_pairs) < 2:
            return 0

        # FIXME: need token USD price
        # calculate price using Constant Product AMM
        return -1

    def map_token_pools(self) -> Dict[Token, Set[str]]:
        result: Dict[Token, Set[str]] = {token: set() for token in Tokens}

        for dex in self.dexes:
            for pool in dex.pools:
                for ptk in pool.tokens:
                    result[ptk.token].add(pool.name)

        return result

    def find_best_price_out(
        self, token_in: Token, amount_in: int, token_out: Token
    ) -> Tuple[int, List[Edge]]:
        """Return the maximum amount of token out for result
        If not possible, return -1
        """
        return -1, []

    def find_best_price_in(
        self, token_out: Token, amount_out: int, token_in: Token
    ) -> Tuple[int, List[Edge]]:
        """Return the minimum amount of token in for result
        If not possible, return -1
        """
        return -1, []


class AlgoTest(TestCase):
    sor: SmartOrderRouter

    def setUp(self) -> None:
        self.sor = SmartOrderRouter()
        print("\n======================== TEST CASE =====================\n")

    def test_model(self):
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

        expect = (7, 6.9290396351061645)
        result = pool.swap("USDT", 7, "USDC")
        assert expect == result

        print("\n Before swap\n", pool)
        pool.swap("USDT", 7000, "USDC", do_swap=True)
        print("\n After swap\n", pool)

        pool.swap("USDT", 10000000000, "USDC", do_swap=True)
        print("\n Swap with excessive amount\n", pool)

    def test_case_1(self):
        dexes = create_dexes(1)
        self.sor.dexes = dexes
        assert len(self.sor.dexes) == len(dexes)
        assert self.sor.find_best_price_in("ETH", 10, "TOMO")[0]

    def test_case_2(self):
        dexes = create_dexes(30)
        self.sor.dexes = dexes
        assert len(self.sor.dexes) == len(dexes)
        assert self.sor.find_best_price_out("ETH", 10, "BTC")[0]


if __name__ == "__main__":
    main(verbosity=2)
