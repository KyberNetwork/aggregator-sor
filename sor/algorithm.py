from __future__ import annotations

from functools import cache
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

from pydantic import BaseModel
from pydantic import validator

from .core import find_optimal_distribution
from .models import Pool
from .models import Token
from .preprocess import TokenPairsPools


PoolMap = Dict[str, Pool]


class PoolSet(BaseModel):
    pools: Set[str]

    def __init__(self, **kwargs):
        if not kwargs:
            return super().__init__(pools=set())
        return super().__init__(**kwargs)

    def __hash__(self):
        names = ",".join(sorted(list(self.pools)))
        return hash(names)

    def copy(self):
        return PoolSet(pools=self.pools.copy())

    def merge(self, another_poolset: "PoolSet"):
        self.pools.update(another_poolset.pools)


class Edge(BaseModel):
    token_in: Token
    token_out: Token
    pools: List[Pool]

    def sort_pools(self, amount_in: float):
        def test_swap(p: Pool):
            nonlocal amount_in
            return p.swap(self.token_in, amount_in, self.token_out)

        self.pools.sort(key=test_swap, reverse=True)

    def __str__(self):
        pools = f"({', '.join([p.name for p in self.pools])})"
        return f"{self.token_in}->{self.token_out} {pools}"

    def __hash__(self) -> int:
        return hash(str(self))

    def swap(
        self,
        amount_in: float,
        ignore_pools: Optional[PoolSet] = None,
        optimal_lv=5,
    ) -> Tuple[float, Dict, PoolSet]:
        if amount_in == 0:
            return 0, dict(), PoolSet()

        self.sort_pools(amount_in)
        pools = self.pools

        if ignore_pools:
            pools = [pool for pool in self.pools if pool.name not in ignore_pools.pools]

        if len(pools) == 0:
            return 0, dict(), PoolSet()

        @cache
        def handler(value, idx):
            nonlocal pools
            pool = pools[idx]
            return pool.swap(self.token_in, value, self.token_out)

        max_out, splits = find_optimal_distribution(
            amount_in,
            len(pools),
            handler,
            optimal_lv=optimal_lv,
        )

        if max_out == 0:
            # NOTE: Ineffective swap, when a pool is so much unbalanced, ignore
            return 0, dict(), PoolSet()

        optimal_splits = {pools[i].name: val for i, val in enumerate(splits)}
        visited_pools = {name for name, value in optimal_splits.items() if value > 0}
        return max_out, optimal_splits, PoolSet(pools=visited_pools)


class Route(BaseModel):
    edges: List[Edge]

    @validator("edges")
    def validate_path_continuity(cls, edges: List[Edge]):
        for i in range(len(edges) - 1):
            current, next = edges[i], edges[i + 1]
            if current.token_out != next.token_in:
                raise ValueError("Broken Route")

        return edges

    def __str__(self):
        assert self.edges
        ins = "->".join([e.token_in for e in self.edges])
        out = self.edges[-1].token_out
        return ins + "->" + out

    def __hash__(self):
        return hash(str(self))

    def swap(
        self,
        amount_in: float,
        ignore_pools: Optional[PoolSet] = None,
        optimal_lv=5,
    ) -> Tuple[float, List[Dict], PoolSet]:
        if not amount_in:
            return 0, [], ignore_pools or PoolSet()

        current_in = amount_in
        visited_pools = PoolSet() if not ignore_pools else ignore_pools.copy()
        path_splits: List[Dict] = []

        @cache
        def cache_swap(
            edge: Edge,
            current_amount_in: float,
            current_visited_pools: PoolSet,
            optimal: int,
        ):
            return edge.swap(
                current_amount_in,
                optimal_lv=optimal,
                ignore_pools=current_visited_pools,
            )

        for edge in self.edges:
            current_in, splits, just_visisted_pools = cache_swap(
                edge,
                current_in,
                visited_pools,
                optimal_lv,
            )
            visited_pools.merge(just_visisted_pools)
            path_splits.append(splits)

        return current_in, path_splits, visited_pools


def construct_path(
    tokens: List[Token],
    tpp: TokenPairsPools,
    pool_map: PoolMap,
) -> Route:
    edges: List[Edge] = []

    for i in range(len(tokens) - 1):
        token_in, token_out = tokens[i], tokens[i + 1]
        pool_names = tpp[token_in][token_out]
        pools = [pool_map[name] for name in pool_names]
        edge = Edge(token_in=token_in, token_out=token_out, pools=pools)
        edges.append(edge)

    return Route(edges=edges)


def find_routes(
    token_in: Token,
    token_out: Token,
    pool_list: List[Pool],
    token_pairs_pools: TokenPairsPools,
    pool_map: PoolMap,
    max_hop=4,
) -> List[Route]:
    if token_in not in token_pairs_pools:
        return []

    if token_out not in token_pairs_pools:
        return []

    if token_in == token_out:
        return []

    if not pool_list:
        return []

    result: List[Route] = []

    def trace(token: Token, queue=None):
        nonlocal token_out, max_hop, token_pairs_pools, pool_map, result

        if not queue:
            queue = []

        queue.append(token)

        if len(queue) > max_hop:
            return

        if token == token_out:
            route = construct_path(queue.copy(), token_pairs_pools, pool_map)
            result.append(route)
            return

        nodes = list(token_pairs_pools[token].keys())

        for node in nodes:
            if len(queue) >= 2 and node == queue[-2]:
                continue

            trace(node, queue=queue)

            while queue[-1] != token:
                queue.pop()

    trace(token_in)
    return result


def calc_amount_out_on_multi_routes(
    routes: List[Route],
    amount_in: float,
    optimal_lv=5,
):
    max_out = float(0)
    route_splits = []
    amount_outs = []
    visited_pools: PoolSet = PoolSet()

    @cache
    def cache_swap(route: Route, value: float, ignore_pools: PoolSet, optimal: int):
        return route.swap(value, ignore_pools=ignore_pools, optimal_lv=optimal)

    def handler(value: float, idx: int):
        nonlocal routes, visited_pools

        if idx == 0:
            visited_pools.pools = set()

        current_path = routes[idx]
        current_out, _, just_visisted_pools = cache_swap(
            current_path,
            value,
            visited_pools,
            optimal_lv,
        )
        visited_pools.merge(just_visisted_pools)
        return current_out

    max_out, splits = find_optimal_distribution(
        amount_in,
        len(routes),
        optimal_lv=optimal_lv,
        handler=handler,
    )

    visited_pools.pools = set()
    used_paths: List[Route] = []

    for idx, split in enumerate(splits):
        # NOTE: recalculate to explain the detail data
        # the value is already cached so its fast
        route = routes[idx]
        current_out, path_splits, just_visisted_pools, = cache_swap(
            route,
            split,
            visited_pools,
            optimal_lv,
        )
        visited_pools.merge(just_visisted_pools)
        if current_out > 0:
            used_paths.append(route)
            amount_outs.append(current_out)
            route_splits.append(path_splits)

    return max_out, splits, route_splits, amount_outs, used_paths
