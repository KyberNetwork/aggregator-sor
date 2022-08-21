from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

from main import Dex
from main import Pool
from main import SwapPath
from main import SwapRoute
from main import Token
from main import Tokens


class SmartOrderRouter:
    """TO BE IMPLEMENTED"""

    _dexes: Optional[List[Dex]] = None
    map_token_pools: Dict[Token, List[Tuple[str, float]]]
    map_name_pools: Dict[str, Pool]
    token_graph: Tuple[Dict[Token, Dict[Token, Set[str]]], Set[str]]

    @property
    def dexes(self):
        return self._dexes

    @dexes.setter
    def dexes(self, dexes: List[Dex]):
        self._dexes = dexes
        self._make_map_token_pools()
        self._make_map_name_pool()
        self._create_graph()

    def _make_map_token_pools(self):
        assert self.dexes
        result: Dict[Token, List[Any]] = {token: [] for token in Tokens}
        for dex in self.dexes:
            for pool in dex.pools:
                for ptk in pool.tokens:
                    result[ptk.token].append((pool.name, ptk.weight))
                    result[ptk.token].sort(key=lambda t: t[1], reverse=True)

        self.map_token_pools = result

    def _make_map_name_pool(self):
        assert self.dexes
        result: Dict[str, Pool] = {}
        for dex in self.dexes:
            for pool in dex.pools:
                result.update({pool.name: pool})

        self.map_name_pools = result

    def _create_graph(self):
        assert self.dexes
        result = {}
        edges = set()
        for d in self.dexes:
            for p in d.pools:
                for t in p.tokens:
                    from_token = t.token
                    to_tokens = [tt.token for tt in p.tokens if tt != t]

                    if from_token not in result:
                        result.update({from_token: {}})

                    for to_token in to_tokens:
                        if to_token not in result[from_token]:
                            result[from_token].update({to_token: set()})

                        edges.add("-".join(sorted([from_token, to_token])))
                        result[from_token][to_token].add(p.name)

        self.token_graph = result, edges

    def find_routes(
        self,
        token_in: Token,
        token_out: Token,
    ) -> List[List[Token]]:
        if token_in not in self.map_token_pools:
            return []

        if token_out not in self.map_token_pools:
            return []

        graph = self.token_graph[0]

        def trace(
            token: Token,
            paths: List[List[Token]],
            queue=None,
            hop_limit=None,
        ):
            if not queue:
                queue = []

            queue.append(token)

            if hop_limit and len(queue) > hop_limit:
                return

            if token == token_out:
                path = queue.copy()
                paths.append(path)
                return

            for node in graph[token].keys():
                if len(queue) >= 2 and node == queue[-2]:
                    continue

                trace(
                    node,
                    paths,
                    queue=queue,
                    hop_limit=hop_limit,
                )

                while queue[-1] != token:
                    queue.pop()

        result: List[List[Token]] = []
        trace(token_in, paths=result, hop_limit=4)
        return result

    def find_routes_per_path(
        self,
        edge: List[Token],
        amount_in: float,
    ) -> SwapRoute:
        result: List[SwapPath] = []

        if not edge:
            return SwapRoute(paths=[])

        current_amount_in = amount_in

        for i in range(len(edge) - 1):
            from_tk, to_tk = edge[i], edge[i + 1]
            pools = self.token_graph[0][from_tk][to_tk]
            paths_per_edge: List[SwapPath] = []

            for pool in pools:
                swap_path = SwapPath(
                    pool=self.map_name_pools[pool],
                    token_in=from_tk,
                    token_out=to_tk,
                    amount_in=current_amount_in,
                )
                paths_per_edge.append(swap_path)

            best_swap_path = paths_per_edge[0]

            for path in paths_per_edge:
                if path.amount_out > best_swap_path.amount_out:
                    best_swap_path = path

            current_amount_in = best_swap_path.amount_out

            result.append(best_swap_path)

        last_swap = result[-1]

        return SwapRoute(
            paths=result,
            token_in=edge[0],
            token_out=edge[-1],
            amount_in=amount_in,
            amount_out=last_swap.amount_out,
        )

    def find_best_price_out(
        self, token_in: Token, amount_in: int, token_out: Token
    ) -> Tuple[float, List[Tuple[Dex, float]]]:
        """Return the maximum amount of token out for result
        If not possible, return -1
        """
        return -1, []

    def find_best_price_in(
        self, token_out: Token, amount_out: int, token_in: Token
    ) -> Tuple[float, List[Tuple[Dex, float]]]:
        """Return the minimum amount of token in for result
        If not possible, return -1
        """
        return -1, []
