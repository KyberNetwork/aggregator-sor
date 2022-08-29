from test.utils import debug
from typing import Any
from typing import List
from unittest import TestCase

from terminaltables import AsciiTable

from sor import batch_split
from sor import calc_amount_out_on_single_edge
from sor import Edge
from sor import Pool
from sor import PoolToken
from sor import Splits

TABLE: List[List[Any]] = []


def show_table():
    global TABLE
    print(AsciiTable(TABLE).table)


class AlgoTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print("------------------------------------------------")
        print("********* Testing Volume Split ******************")

    def setUp(self) -> None:
        debug()

    def test_1(self):
        volume = 10
        print(f"Partitioning a volume={volume} to multi parts")

        result = batch_split(volume, 2)
        assert result is not None
        assert len(result) == 6

        for split in result:
            print(f"Split = {split}")
            assert len(split) == 2
            assert sum(split) == volume

    def test_2(self):
        volume = 10
        count = 0
        print(f"Partitioning a volume={volume} to multi parts")
        print("(smaller part's size)")

        def callback(splits: Splits):
            nonlocal count
            print(f"Splits={splits}")
            assert sum(splits) == volume
            count += 1

        result = batch_split(volume, 2, callback=callback, optimal_lv=10)

        assert result is None
        assert count == 11

    def test_3(self):
        global IS_DEBUG, TABLE

        tk1 = PoolToken(token="BTC", amount=200)
        tk2 = PoolToken(token="ETH", amount=2000)
        pool1 = Pool("pool1", 0.01, [tk1, tk2])

        tk3 = PoolToken(token="BTC", amount=80)
        tk4 = PoolToken(token="ETH", amount=900)
        pool2 = Pool("pool2", 0.01, [tk3, tk4])

        tk5 = PoolToken(token="BTC", amount=40)
        tk6 = PoolToken(token="ETH", amount=500)
        pool3 = Pool("pool3", 0.01, [tk5, tk6])

        pools = [pool1, pool2, pool3]
        pool_names = [p.name for p in pools]

        TABLE = [
            ["Token", *pool_names],
            ["BTC", *[p.tokens[0].amount for p in pools]],
            ["ETH", *[p.tokens[1].amount for p in pools]],
        ]
        print("\nGiven the following pools")
        show_table()

        debug()

        amount_in = float(100)
        print(f"\n+ Swapping {amount_in} BTC->ETH without volume split")
        TABLE = [
            ["Amount-In (BTC)", *pool_names],
            [amount_in, *[p.swap("BTC", amount_in, "ETH") for p in pools]],
        ]
        show_table()

        debug()

        print(f"\n+ Swapping {amount_in} BTC->ETH with volume split")
        edge = Edge(token_in="BTC", token_out="ETH", pools=pools)

        TABLE = [["Optimal Level", "Amount-In", "Amout-Out", *pool_names]]

        expected = [805.90474, 806.00997, 807.49601, 807.65271]

        for idx, optimal_lv in enumerate([5, 10, 30, 100]):
            max_out, optimal_splits = calc_amount_out_on_single_edge(
                edge,
                amount_in,
                optimal_lv=optimal_lv,
            )
            assert max_out == expected[idx]
            split_details = [optimal_splits[p.name] for p in pools]
            TABLE.append([optimal_lv, amount_in, max_out, *split_details])
            debug(show_table)

        show_table()
