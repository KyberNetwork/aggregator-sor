from test.mock import mock
from test.utils import debug
from typing import List
from unittest import TestCase

from terminaltables import AsciiTable

from sor import find_paths
from sor import Pool
from sor.algorithm import path_to_edges
from sor.models import Token


class AlgoTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print("----------------------------------------------------------")
        print("********* Testing Path Finder ****************************")

    def test_1(self):
        tokens: List[Token] = ["BTC", "ETH", "KNC", "USDC", "SOL"]
        _, pools, pool_map, token_pairs_pools = mock()

        def get_token_amount(pool: Pool, token: Token):
            pool_token = pool.get_token(token)
            if not pool_token:
                return ""
            return pool_token.amount

        def render_table_row(token: Token):
            nonlocal pools
            return [token, *[get_token_amount(p, token) for p in pools]]

        table = [
            ["Token", *[p.name for p in pools]],
            *[render_table_row(t) for t in tokens],
        ]

        print("\nGiven the following pools")
        print(AsciiTable(table).table)

        debug()

        token_in, token_out, max_hop = "BTC", "ETH", 4
        print(f"\nPaths from {token_in} to {token_out} with max_hop={max_hop}")
        paths = find_paths(token_in, token_out, pools, token_pairs_pools, max_hop=max_hop)
        print("\n".join(map(str, paths)))

        debug()

        print(f"\nEdges from {token_in} to {token_out} with max_hop={max_hop}")

        for path in paths:
            joined_path = "->".join(path)
            edge = path_to_edges(path, token_pairs_pools, pool_map)
            print(joined_path, "\t", edge)
