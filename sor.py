from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

from main import Dex
from main import Token
from main import Tokens


class SmartOrderRouter:
    """TO BE IMPLEMENTED"""

    _dexes: Optional[List[Dex]] = None
    map_token_pools: Dict[Token, List[Tuple[str, float]]]
    token_graph: Tuple[Dict[Token, Dict[Token, Set[str]]], Set[str]]

    @property
    def dexes(self):
        return self._dexes

    @dexes.setter
    def dexes(self, dexes: List[Dex]):
        self._dexes = dexes
        self._make_map_token_pools(self._dexes)
        self._create_graph()

    def _make_map_token_pools(self, dexes: List[Dex]):
        result: Dict[Token, List[Any]] = {token: [] for token in Tokens}
        for dex in dexes:
            for pool in dex.pools:
                for ptk in pool.tokens:
                    result[ptk.token].append((pool.name, ptk.weight))
                    result[ptk.token].sort(key=lambda t: t[1], reverse=True)

        self.map_token_pools = result

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

    def find_paths(
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
            visited=None,
        ):
            if not queue:
                queue = []

            if not visited:
                visited = set()

            queue.append(token)
            visited.add(token)

            if token == token_out:
                path = queue.copy()
                paths.append(path)
                return

            for node in graph[token].keys():
                if node in visited:
                    continue

                if len(queue) >= 2 and node == queue[-2]:
                    continue

                trace(node, paths, queue=queue, visited=visited)

                while queue[-1] != token:
                    visited.remove(queue.pop())

        result: List[List[Token]] = []
        trace(token_in, paths=result)
        return result

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
