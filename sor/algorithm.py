from collections.abc import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
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
    path: Path,
    token_pairs_pools: TokenPairsPools,
    pool_map: Dict[str, Pool],
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

    if batch_count == 0:
        return None

    if batch_count == 1:
        result = [[batch_volume]]
        return result if not callback else callback(result[0])

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
            result.append(splits) if not callback else callback(splits)
            queue.pop()
            return

        for i in range(optimal_lv + 1):
            split_head = round(current_batch_volume * i / optimal_lv, 5)
            split_remain = round(current_batch_volume - split_head, 5)
            queue.append(split_head)

            if split_remain > 0:
                # FIXME: edge-cases
                # 2/ duplicated distributions
                split(split_remain, batch_idx=batch_idx + 1, queue=queue)
            else:
                splits = queue.copy()
                result.append(splits) if not callback else callback(splits)

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


def find_optimal_distribution(
    volume_in: float,
    split_count: int,
    handler: Callable[[float, int], float],
    optimal_lv=5,
) -> Tuple[float, Splits]:

    if volume_in == 0:
        return 0, []

    result = float(0)
    optimal_splits: List[float] = []

    def try_each_split(splits: Splits):
        nonlocal result, optimal_splits
        current_result = sum([handler(value, i) for i, value in enumerate(splits)])

        if current_result > result:
            result = current_result
            optimal_splits = splits

    batch_split(
        volume_in,
        split_count,
        optimal_lv=optimal_lv,
        callback=try_each_split,
    )

    return result, optimal_splits


def calc_amount_out_on_single_edge(
    edge: Edge,
    amount_in: float,
    optimal_lv=5,
    do_swap=False,
    ignore_pools: Optional[Set[str]] = None,
) -> Tuple[float, EdgeSplit]:
    """
    Optimize amount out by splitting volume over pools in parallel
    This function mutates pool state when required
    But we only mutate (do_swap=True) only when max_result is found
    """
    if not ignore_pools:
        ignore_pools = set()

    pools, token_in, token_out = edge.pools, edge.token_in, edge.token_out
    sort_pools(token_in, token_out, amount_in, pools)

    pools = [pool for pool in pools if pool.name not in ignore_pools]

    if amount_in == 0:
        return 0, {}

    def handler(value, idx):
        nonlocal pools, token_in, token_out
        pool = pools[idx]
        return pool.swap(token_in, value, token_out)

    max_out, splits = find_optimal_distribution(
        amount_in,
        len(pools),
        handler,
        optimal_lv=optimal_lv,
    )

    optimal_splits = {pools[i].name: val for i, val in enumerate(splits)}

    if max_out == 0:
        # NOTE: Ineffective swap, when a pool is so much unbalanced, ignore
        return 0, {}

    if do_swap:
        for pool in pools:
            split_volume = optimal_splits.get(pool.name, 0)
            pool.swap(token_in, split_volume, token_out, do_swap=True)

    return max_out, optimal_splits


def calc_amount_out_on_consecutive_edges(
    edges: List[Edge],
    amount_in: float,
    optimal_lv=5,
    visited_pools: Optional[Set[str]] = None,
) -> Tuple[float, List[EdgeSplit], PoolMap, Set[str]]:
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

    if not visited_pools:
        visited_pools = set()

    if amount_in == 0:
        return 0, [{}], {}, set()

    cloned_edges, cloned_pools = clone_edges(edges)
    current_in = amount_in
    splits: List[EdgeSplit] = []

    for edge in cloned_edges:
        current_in, split = calc_amount_out_on_single_edge(
            edge,
            current_in,
            optimal_lv=optimal_lv,
            do_swap=True,
            ignore_pools=visited_pools,
        )

        assert visited_pools is not None
        for pool_name, value in split.items():
            if value > 0:
                visited_pools.add(pool_name)

            if value == 0 and pool_name in visited_pools:
                visited_pools.remove(pool_name)

        splits.append(split)

    assert visited_pools
    return current_in, splits, cloned_pools, visited_pools


def filter_inefficient_paths(
    paths: List[Path],
    amount_in: float,
    token_pairs_pools: TokenPairsPools,
    pool_map: PoolMap,
    optimal_lv=2,
) -> List[Path]:
    max_out = float(0)
    inefficient_paths = set()
    amout_outs = {}

    for i, path in enumerate(paths):
        edges = path_to_edges(path, token_pairs_pools, pool_map)
        amount_out, _, _, _ = calc_amount_out_on_consecutive_edges(edges, amount_in)
        amout_outs.update({"-".join(path): amount_out})

        if amount_out > max_out:
            max_out = amount_out

    for path in paths:
        amount_out = amout_outs["-".join(path)]
        if amount_out < 0.10 * max_out:
            inefficient_paths.add("-".join(path))

    paths.sort(key=lambda path: amout_outs["-".join(path)], reverse=True)
    return [path for path in paths if "-".join(path) not in inefficient_paths]


def calc_amount_out_on_multi_paths(
    paths: List[Path],
    amount_in: float,
    token_pairs_pools: TokenPairsPools,
    pool_map: PoolMap,
    optimal_lv=5,
):
    max_out = float(0)
    route_splits: List[List[EdgeSplit]] = []
    amount_out_each_path: List[float] = []

    def try_each_split(splits: Splits):
        nonlocal max_out, route_splits, amount_out_each_path
        result = float(0)
        cloned_pool_map = {name: p.clone() for name, p in pool_map.items()}
        split_combinations: List[List[EdgeSplit]] = []
        path_amount_out: List[float] = []
        visited_pools: Set[str] = set()

        checking_edges = []

        for idx, split in enumerate(splits):
            edges = path_to_edges(paths[idx], token_pairs_pools, cloned_pool_map)
            checking_edges.append(edges)
            (
                amount_out,
                edge_splits,
                mutated_pools,
                new_visited_pools,
            ) = calc_amount_out_on_consecutive_edges(
                edges,
                split,
                optimal_lv=optimal_lv,
                visited_pools=visited_pools,
            )

            visited_pools.update(new_visited_pools)
            result += amount_out
            path_amount_out.append(amount_out)
            cloned_pool_map |= mutated_pools
            split_combinations.append(edge_splits)

        if result > max_out:
            max_out = result
            route_splits = split_combinations.copy()
            amount_out_each_path = path_amount_out.copy()

    batch_split(
        amount_in,
        len(paths),
        optimal_lv=optimal_lv,
        callback=try_each_split,
    )

    return max_out, route_splits, amount_out_each_path
