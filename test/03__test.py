from test.mock import mock
from test.utils import debug
from typing import List
from unittest import TestCase

from terminaltables import AsciiTable

from sor import determine_token_pair_pools
from sor import Dex
from sor import find_routes
from sor import map_pool_by_name
from sor import Pool
from sor import PoolToken
from sor import Token


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
        paths = find_routes(
            token_in, token_out, pools, token_pairs_pools, pool_map, max_hop=max_hop
        )

        for p in paths:
            print(p)

    def _test_2(self):
        tokens = [
            PoolToken(token="BTC", amount=2000),
            PoolToken(token="KNC", amount=2000),
            PoolToken(token="ETH", amount=20000),
        ]
        p1 = Pool("p1", 0.015, tokens[:2])
        p2 = Pool("p2", 0.015, tokens[1:])
        p3 = Pool("p3", 0.015, [tokens[0], tokens[2]])
        p4 = Pool("p3", 0.015, tokens)
        dexes = [Dex(name="d", pools=[p1, p2, p3, p4], gas=0.01)]

        token_pairs_pools = determine_token_pair_pools(dexes)
        pools, pool_map = map_pool_by_name(dexes)
        print(token_pairs_pools)
        paths = find_routes("BTC", "ETH", pools, token_pairs_pools, pool_map)
        [print(p) for p in paths]
