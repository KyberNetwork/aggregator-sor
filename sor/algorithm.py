from collections.abc import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from pydantic import BaseModel

from .models import Pool
from .models import Token
from .preprocess import TokenPairsPools


Path = List[Token]
Splits = List[float]
EdgeSplit = Dict[str, float]
PoolMap = Dict[str, Pool]
BatchSplitCallback = Callable[[Splits], None]


class Edge(BaseModel):
    token_in: Token
    token_out: Token
    pools: List[Pool]

    def __repr__(self):
        pools = f"({', '.join([p.name for p in self.pools])})"
        return f"{self.token_in}->{self.token_out} {pools}"


def clone_edges(edges: List[Edge]) -> Tuple[List[Edge], PoolMap]:
    cloned_edges: List[Edge] = []
    cloned_pools: PoolMap = {}

    for edge in edges:
        clone_edge = Edge(
            token_in=edge.token_in,
            token_out=edge.token_out,
            pools=edge.pools,
        )

        for pool in clone_edge.pools:
            if pool.name not in cloned_pools:
                cloned_pools.update({pool.name: pool.clone()})

        cloned_pool_list = [cloned_pools[p.name] for p in clone_edge.pools]
        clone_edge.pools = cloned_pool_list
        cloned_edges.append(clone_edge)

    return cloned_edges, cloned_pools


def validate_edges_continuity(edges: List[Edge]) -> bool:
    """A valid path must not be broken"""
    for i in range(len(edges) - 1):
        current, next = edges[i], edges[i + 1]
        if current.token_out != next.token_in:
            return False

    return True


def find_paths(
    token_in: Token,
    token_out: Token,
    pool_list: List[Pool],
    token_pairs_pools: TokenPairsPools,
    max_hop=4,
) -> List[Path]:
    if token_in not in token_pairs_pools:
        return []

    if token_out not in token_pairs_pools:
        return []

    if token_in == token_out:
        return []

    if not pool_list:
        return []

    result = []

    def trace(token: Token, queue=None):
        nonlocal token_out, max_hop

        if not queue:
            queue = []

        queue.append(token)

        if len(queue) > max_hop:
            return

        if token == token_out:
            result.append(queue.copy())
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


def path_to_edges(
    path: Path, token_pairs_pools: TokenPairsPools, pool_map: Dict[str, Pool]
) -> List[Edge]:
    result: List[Edge] = []

    for i in range(len(path) - 1):
        token_in, token_out = path[i], path[i + 1]
        pool_names = token_pairs_pools[token_in][token_out]
        pools = [pool_map[name] for name in pool_names]
        result.append(Edge(token_in=token_in, token_out=token_out, pools=pools))

    return result


def batch_split(
    batch_volume: float,
    batch_count: int,
    optimal_lv=5,
    callback: Optional[BatchSplitCallback] = None,
) -> Optional[List[Splits]]:
    result: List[Splits] = []

    def split(
        current_batch_volume: float,
        batch_idx=0,
        queue: Optional[Splits] = None,
    ):
        nonlocal batch_count, optimal_lv, result, callback

        if not queue:
            queue = []

        if len(queue) == batch_count - 1:
            queue.append(current_batch_volume)
            splits = queue.copy()

            if callback:
                callback(splits)
            else:
                result.append(splits)

            queue.pop()
            return

        for i in range(optimal_lv + 1):
            split_head = round(current_batch_volume * i / optimal_lv, 5)
            split_remain = round(current_batch_volume - split_head, 5)
            queue.append(split_head)
            # FIXME: edge-cases
            # 1/ when no more amount to distribute
            # 2/ duplicated distributions
            split(split_remain, batch_idx=batch_idx + 1, queue=queue)
            queue.pop()

    split(batch_volume)
    return result if not callback else None


def sort_pools(
    token_in: Token,
    token_out: Token,
    amount_in: float,
    pools: List[Pool],
):
    def simulate_swap(pool: Pool):
        return pool.swap(token_in, amount_in, token_out)

    pools.sort(key=simulate_swap, reverse=True)


def calc_amount_out_on_single_edge(
    edge: Edge,
    amount_in: float,
    optimal_lv=5,
    do_swap=False,
) -> Tuple[float, EdgeSplit]:
    """
    Optimize amount out by splitting volume over pools in parallel
    This function mutates pool state when required
    But we only mutate (do_swap=True) only when max_result is found
    """
    pools, token_in, token_out = edge.pools, edge.token_in, edge.token_out
    sort_pools(token_in, token_out, amount_in, pools)
    max_out = float(0)
    optimal_splits: EdgeSplit = {}

    def try_each_split(splits: Splits):
        nonlocal max_out, optimal_splits
        result = float(0)

        for idx, part in enumerate(splits):
            result += pools[idx].swap(token_in, part, token_out)

        if result > max_out:
            max_out = result
            optimal_splits = {pools[idx].name: split for idx, split in enumerate(splits)}

    batch_split(
        amount_in,
        len(pools),
        optimal_lv=optimal_lv,
        callback=try_each_split,
    )

    if do_swap:
        for pool in pools:
            split_volume = optimal_splits[pool.name]
            pool.swap(token_in, split_volume, token_out, do_swap=True)

    return max_out, optimal_splits


def calc_amount_out_on_consecutive_edges(
    edges: List[Edge],
    amount_in: float,
    optimal_lv=5,
) -> Tuple[float, List[EdgeSplit], PoolMap]:
    """
    Optimizing on running over multi consecutive edges,
    ie: BTC -> USDC -> ETH
    When optimization, pool state must persist over iteration
    Meanwhile, we need to maintain function purity
    because the edges might be process multiple times independently
    -> Solution: clone the Edges
    """
    # Confirm validity of edges,
    if not validate_edges_continuity(edges):
        raise Exception("Broken path:", edges)

    # Clone Edges, because we want to maintain function's purity
    cloned_edges, cloned_pools = clone_edges(edges)
    current_in = amount_in
    splits: List[EdgeSplit] = []

    for edge in cloned_edges:
        current_in, split = calc_amount_out_on_single_edge(
            edge,
            current_in,
            optimal_lv=optimal_lv,
            do_swap=True,
        )
        splits.append(split)

    return current_in, splits, cloned_pools


# FIXME: fix this function
def calc_amount_out_on_multi_routes(
    paths: List[Path],
    amount_in: float,
    token_pairs_pools: TokenPairsPools,
    pool_map: Dict[str, Pool],
    optimal_lv=5,
):
    max_out = float(0)
    route_splits: List[float] = []

    def try_each_split(splits: Splits):
        nonlocal max_out, route_splits
        result = float(0)

        for idx, part in enumerate(splits):
            amount_out, _, _ = calc_amount_out_on_consecutive_edges(
                path_to_edges(paths[idx], token_pairs_pools, pool_map),
                part,
                optimal_lv=optimal_lv,
            )

            result += amount_out

        if result > max_out:
            max_out = result
            route_splits = splits

    batch_split(
        amount_in,
        len(paths),
        optimal_lv=optimal_lv,
        callback=try_each_split,
    )

    return max_out, route_splits
