from collections.abc import Callable
from typing import List
from typing import Optional

from pydantic import BaseModel

from .models import Pool
from .models import Token
from .preprocess import TokenPairsPools


Edge = List[Token]
Splits = List[float]
BatchSplitCallback = Callable[[Splits], None]


class SwapEdge(BaseModel):
    token_in: Token
    token_out: Token
    pools: List[Pool]


class SwapRoute(BaseModel):
    edges: List[SwapEdge]


def find_edges(
    token_in: Token,
    token_out: Token,
    pool_list: List[Pool],
    token_pairs_pools: TokenPairsPools,
    max_hop=4,
) -> List[Edge]:
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


def batch_split(
    batch_size: float,
    batch_count: int,
    optimal_lv=5,
    callback: Optional[BatchSplitCallback] = None,
) -> Optional[List[Splits]]:
    result: List[Splits] = []

    def split(
        current_batch_size: float,
        batch_idx=0,
        queue: Optional[Splits] = None,
    ):
        nonlocal batch_count, optimal_lv, result, callback

        if not queue:
            queue = []

        if len(queue) == batch_count - 1:
            queue.append(current_batch_size)
            splits = queue.copy()

            if callback:
                callback(splits)
            else:
                result.append(splits)

            queue.pop()
            return

        for i in range(optimal_lv + 1):
            split_head = round(current_batch_size * i / optimal_lv, 5)
            split_remain = round(current_batch_size - split_head, 5)
            queue.append(split_head)
            # FIXME: edge-cases
            # 1/ when no more amount to distribute
            # 2/ duplicated distributions
            split(split_remain, batch_idx=batch_idx + 1, queue=queue)
            queue.pop()

    split(batch_size)

    return result if not callback else None


def sort_pools(
    pools: List[Pool],
    amount_in: float,
    token_in: Token,
    token_out: Token,
):
    def simulate_swap(pool: Pool):
        return pool.swap(token_in, amount_in, token_out)

    pools.sort(key=simulate_swap, reverse=True)


def swap_edge_amount_out(swap_edge: SwapEdge, amount_in: float, optimal_lv=5):
    sort_pools(
        swap_edge.pools,
        amount_in,
        swap_edge.token_in,
        swap_edge.token_out,
    )
    pool_order = [pool.name for pool in swap_edge.pools]
    max_out, optimal_splits = float(0), []

    def test_amount(splits: Splits):
        nonlocal max_out, optimal_splits, pool_order
        result = float(0)

        for idx, part in enumerate(splits):
            result += swap_edge.pools[idx].swap(
                swap_edge.token_in,
                part,
                swap_edge.token_out,
            )

        if result > max_out:
            max_out = result
            optimal_splits = [s / amount_in * 100 for s in splits]

    batch_split(
        amount_in,
        len(swap_edge.pools),
        optimal_lv=optimal_lv,
        callback=test_amount,
    )

    return max_out, optimal_splits, pool_order
