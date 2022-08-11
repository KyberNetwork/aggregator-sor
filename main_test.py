from typing import Tuple
from unittest import TestCase, main
from main import *


class SmartOrderRouter(BaseModel):
    """TO BE IMPLEMENTED"""

    dexes: List[Dex] = []

    def findBestPriceOut(
        self, token_in: Token, amount_in: int, token_out: Token
    ) -> Tuple[int, List[Edge]]:
        """Return the maximum amount of token out for result
        If not possible, return -1
        """
        return -1, []

    def findBestPriceIn(
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
        dexes = create_dexes(3)
        self.sor.dexes = dexes
        assert len(self.sor.dexes) == len(dexes)
        assert self.sor.findBestPriceIn("A", 10, "B")[0]

    def test_case_2(self):
        dexes = create_dexes(30)
        self.sor.dexes = dexes
        assert len(self.sor.dexes) == len(dexes)
        assert self.sor.findBestPriceOut("A", 10, "B")[0]


if __name__ == "__main__":
    main(verbosity=2)
