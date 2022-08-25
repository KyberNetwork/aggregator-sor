from test.utils import debug
from typing import List
from unittest import TestCase

from terminaltables import AsciiTable

from sor import determine_token_pair_pools
from sor import Dex
from sor import find_paths
from sor import Pool
from sor import PoolToken
from sor.algorithm import path_to_edges
from sor.models import Token
from sor.preprocess import map_pool_by_name

# cycol = cycle("bgrcmk")
# def plotting_graph(data: TokenPairsPools):
#     vertices: List[Token] = sorted([k for k, _ in data.items()], key=lambda x: len(x))
#     points: Dict[Token, List[int]] = {
#         v: [idx * 2, idx % 3 * 3 - idx % 2 * 20] for idx, v in enumerate(vertices)
#     }

#     edges = set()

#     for from_token, pairs in data.items():
#         for to_token in pairs.keys():
#             edge = "-".join(sorted([from_token, to_token]))
#             edges.add(edge)

#     for edge in edges:
#         from_token, to_token = edge.split("-")
#         from_point, to_point = points[from_token], points[to_token]
#         x = [from_point[0], to_point[0]]
#         y = [from_point[1], to_point[1]]
#         plt.plot(x, y, color="#aaa")

#     for token, values in points.items():
#         x, y = values
#         plt.scatter(x, y, marker="o")
#         plt.text(x - 0.2, y + 0.4, token)

#     ax = plt.gca()
#     ax.get_xaxis().set_visible(False)
#     ax.get_yaxis().set_visible(False)
#     ax.spines["top"].set_visible(False)
#     ax.spines["right"].set_visible(False)
#     ax.spines["bottom"].set_visible(False)
#     ax.spines["left"].set_visible(False)
#     plt.show()


class AlgoTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print("----------------------------------------------------------")
        print("********* Testing Path Finder ****************************")

    def test_1(self):
        tokens: List[Token] = ["BTC", "ETH", "KNC", "USDC", "SOL"]

        tk1 = PoolToken(token="BTC", amount=200)
        tk2 = PoolToken(token="ETH", amount=2000)
        pool1 = Pool("pool1", 0.01, [tk1, tk2])
        uniswap = Dex(name="Uniswap", pools=[pool1], gas=0.2)

        tk3 = PoolToken(token="BTC", amount=80)
        tk4 = PoolToken(token="ETH", amount=900)
        pool2 = Pool("pool2", 0.01, [tk3, tk4])
        metaswap = Dex(name="Metaswap", pools=[pool2], gas=0.4)

        tk5 = PoolToken(token="USDC", amount=10000)
        tk6 = PoolToken(token="BTC", amount=11)
        tk7 = PoolToken(token="KNC", amount=1100)
        pool3 = Pool("pool3", 0.01, [tk5, tk6, tk7])
        luaswap = Dex(name="Luaswap", pools=[pool3], gas=0.3)

        tk8 = PoolToken(token="USDC", amount=200)
        tk9 = PoolToken(token="ETH", amount=110)
        pool4 = Pool("pool4", 0.01, [tk8, tk9])
        vuswap = Dex(name="Vuswap", pools=[pool4], gas=0.3)

        tk10 = PoolToken(token="SOL", amount=2000)
        tk11 = PoolToken(token="ETH", amount=1100)
        pool5 = Pool("pool5", 0.01, [tk10, tk11])
        kyberswap = Dex(name="Kyberswap", pools=[pool5], gas=0.3)

        dexes = [uniswap, metaswap, luaswap, vuswap, kyberswap]
        token_pairs_pools = determine_token_pair_pools(dexes)
        pools, pool_map = map_pool_by_name(dexes)

        def get_token_amount(pool: Pool, token: Token):
            pool_token = pool.get_token(token)
            if not pool_token:
                return ""
            return pool_token.amount

        def render_table_row(token: Token):
            nonlocal pools
            return [token, *[get_token_amount(p, token) for p in pools]]

        table = [["Token", *[p.name for p in pools]], *[render_table_row(t) for t in tokens]]

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
