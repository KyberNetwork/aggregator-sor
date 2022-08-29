from test.mock import mock
from test.utils import debug
from typing import Any
from typing import List
from unittest import TestCase

from terminaltables import AsciiTable

from sor import calc_amount_out_on_consecutive_edges
from sor import find_paths
from sor import path_to_edges
from sor.algorithm import calc_amount_out_on_multi_paths
from sor.algorithm import filter_inefficient_paths


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

        paths = find_paths(
            "BTC",
            "ETH",
            pools,
            token_pairs_pools,
            max_hop=4,
        )

        print("\n** SINGLE ROUTE CALCULATION", end=" ")
        print("(amount-in -> amount-out on each route)")

        table: List[Any] = [["Route", "Amount-In", "Amount-Out", "Splits"]]

        for path in paths:
            edges = path_to_edges(path, token_pairs_pools, pool_map)
            amount_out, splits, _ = calc_amount_out_on_consecutive_edges(edges, amount_in)
            row = ["->".join(path), amount_in, amount_out, splits]
            table.append(row)
            debug(lambda: show_table(table))

        show_table(table)

        debug()

        print("\n** MULTI ROUTE CALCULATION (AUTO-ROUTER)")
        paths = filter_inefficient_paths(paths, amount_in, token_pairs_pools, pool_map)
        print(paths)
        max_out, route_splits, outputs = calc_amount_out_on_multi_paths(
            paths,
            amount_in,
            token_pairs_pools,
            pool_map,
            optimal_lv=3,
        )

        table = [["Route", "Amount-In", "Amount-Out", "Splits"]]

        debug()

        for idx, amount_out in enumerate(outputs):
            path = paths[idx]
            amount_in = sum(route_splits[idx][0].values())
            table.append(["->".join(path), amount_in, amount_out, route_splits[idx]])

        show_table(table)
        print("Total amount-out ->", max_out)
