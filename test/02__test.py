from os import environ
from typing import Any
from typing import List
from unittest import TestCase

from terminaltables import AsciiTable

from sor import batch_split
from sor import Pool
from sor import PoolToken
from sor import Splits

IS_DEBUG = environ.get("DEBUG") == "1"
TABLE: List[List[Any]] = []


def println(msg: str):
    print("\n" + msg)


def show_table():
    global TABLE
    print(AsciiTable(TABLE).table)


class AlgoTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print("------------------------------------------------")
        print("********* Testing Volume Split ******************")

    def setUp(self) -> None:
        print("")

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
        println("Given the following pools")
        show_table()

        amount_in = float(100)
        println(f"+ Swapping {amount_in} BTC->ETH without volume split")
        TABLE = [
            ["Amount-In (BTC)", *pool_names],
            [amount_in, *[p.swap("BTC", amount_in, "ETH") for p in pools]],
        ]
        show_table()

        println(f"+ Swapping {amount_in} BTC->ETH with volume split")
        max_out = 0
        optimal_splits = {p.name: float(0) for p in pools}

        def test_amount(splits: Splits):
            nonlocal pools, max_out, optimal_splits
            result = 0

            for idx, part in enumerate(splits):
                result += pools[idx].swap("BTC", part, "ETH")

            if result > max_out:
                max_out = result
                optimal_splits = {pools[idx].name: split for idx, split in enumerate(splits)}

        TABLE = [["Optimal Level", "Amout-Out (ETH)", *pool_names]]

        def optimize_output(optimal_lv: int):
            nonlocal amount_in, pools, test_amount
            batch_split(amount_in, len(pools), callback=test_amount, optimal_lv=optimal_lv)
            split_details = [optimal_splits[p.name] for p in pools]
            TABLE.append([optimal_lv, max_out, *split_details])

        [optimize_output(i) for i in [5, 10, 30, 100]]
        show_table()
