from unittest import TestCase

from sor import batch_split
from sor import Pool
from sor import PoolToken
from sor import Splits


class AlgoTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print("------------------------------------------------")
        print("********* Testing VolumeSplit ******************")

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
        print(
            f"Partitioning a volume={volume} to multi parts \
            with Callback & Increased number of partition"
        )

        def callback(splits: Splits):
            nonlocal count
            print(f"Splits={splits}")
            assert sum(splits) == volume
            count += 1

        result = batch_split(volume, 2, callback=callback, optimal_lv=10)

        assert result is None
        assert count == 11

    def test_3(self):
        amount_in = 100
        print(
            f"Partitioning a swap of {amount_in} BTC->ETH \
        over list of Pools"
        )
        tk1 = PoolToken(token="BTC", amount=200)
        tk2 = PoolToken(token="ETH", amount=2000)
        pool1 = Pool("pool1", 0.01, [tk1, tk2])

        tk3 = PoolToken(token="BTC", amount=80)
        tk4 = PoolToken(token="ETH", amount=900)
        pool2 = Pool("pool2", 0.01, [tk3, tk4])

        tk5 = PoolToken(token="BTC", amount=40)
        tk6 = PoolToken(token="ETH", amount=500)
        pool3 = Pool("pool3", 0.01, [tk5, tk6])
        test_pools, max_out, optimal_splits = [pool1, pool2, pool3], 0, None

        print("+ Swapping without volume split")
        for pool in test_pools:
            print(
                pool.name,
                f"swap {amount_in} BTC->ETH:",
                pool.swap("BTC", amount_in, "ETH"),
            )

        print("+ Swapping with volume split")

        def test_amount(splits: Splits):
            nonlocal test_pools, max_out, optimal_splits
            result = 0

            for idx, part in enumerate(splits):
                result += test_pools[idx].swap("BTC", part, "ETH")

            if result > max_out:
                max_out = result
                optimal_splits = splits

        pool_names = [p.name for p in test_pools]

        batch_split(amount_in, len(test_pools), callback=test_amount)
        print("=> RESULT (optimal=5):", max_out, optimal_splits, pool_names)

        batch_split(amount_in, len(test_pools), callback=test_amount, optimal_lv=10)
        print("=> RESULT (optimal=10):", max_out, optimal_splits, pool_names)

        batch_split(amount_in, len(test_pools), callback=test_amount, optimal_lv=30)
        print("=> RESULT (optimal=30):", max_out, optimal_splits, pool_names)
