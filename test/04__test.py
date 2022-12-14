from test.mock import mock
from test.utils import debug
from typing import Any
from typing import List
from unittest import TestCase

from terminaltables import AsciiTable

from sor import find_routes
from sor.algorithm import calc_amount_out_on_multi_routes


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
        _, pools, pool_map, token_pairs_pools = mock()

        amount_in = 100
        print(f"\nSWAPPING {amount_in} BTC to ETH")

        debug()

        paths = find_routes(
            "BTC",
            "ETH",
            pools,
            token_pairs_pools,
            pool_map,
            max_hop=4,
        )

        print("\n** SINGLE ROUTE CALCULATION", end=" ")
        print("(amount-in -> amount-out on each route)")

        table: List[Any] = [["Route", "Amount-In", "Amount-Out", "Splits"]]

        for path in paths:
            amount_out, splits, _ = path.swap(amount_in)
            row = [str(path), amount_in, amount_out, splits]
            table.append(row)
            debug(lambda: show_table(table))

        show_table(table)

        debug()

        print("\n** MULTI ROUTE CALCULATION (AUTO-ROUTER)")
        max_out, splits, route_splits, outputs, used_paths = calc_amount_out_on_multi_routes(
            paths, amount_in, optimal_lv=2
        )

        max_out, splits, route_splits, outputs, _ = calc_amount_out_on_multi_routes(
            used_paths, amount_in, optimal_lv=20
        )

        table = [["Route", "Amount-In", "Amount-Out", "Splits"]]

        debug()

        for idx, amount_out in enumerate(outputs):
            path = paths[idx]
            amount_in = sum(route_splits[idx][0].values()) if route_splits[idx] else 0
            table.append([str(path), amount_in, amount_out, route_splits[idx]])

        show_table(table)
        print("Total amount-out ->", max_out)
