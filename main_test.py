from typing import Dict
from typing import List
from typing import Set
from typing import Tuple
from unittest import main
from unittest import TestCase

from main import Dex
from main import Edge
from main import Pool
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

    def test_case_1(self):
        dexes = create_dexes(1)
        self.sor.dexes = dexes

        for dex in self.sor.dexes:
            print(dex)

        map_token_pools = self.sor.map_token_pools()
        print(map_token_pools)

        assert len(self.sor.dexes) == len(dexes)
        assert self.sor.find_best_price_in("A", 10, "B")[0]

    def test_case_2(self):
        dexes = create_dexes(30)
        self.sor.dexes = dexes
        assert len(self.sor.dexes) == len(dexes)
        assert self.sor.find_best_price_out("A", 10, "B")[0]


if __name__ == "__main__":
    main(verbosity=2)
