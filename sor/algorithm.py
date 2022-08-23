from typing import Dict
from typing import List

from .models import Dex
from .models import Edge
from .models import Pool
from .models import SwapPath
from .models import Token
from .preprocess import TokenPairsPools


def find_edges(
    dexes: List[Dex],
    token_in: Token,
    token_out: Token,
    pool_list: List[Pool],
    pool_map: Dict[str, Pool],
    token_pairs_pools: TokenPairsPools,
    max_hop=4,
) -> List[Edge]:
    if token_in not in token_pairs_pools:
        return []

    if token_out not in token_pairs_pools:
        return []

    if token_in == token_out:
        return []

    if not dexes:
        return []

    if not pool_list:
        return []

    if not pool_map:
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


def find_routes(edge: Edge, pools: List[Pool]) -> List[List[SwapPath]]:
    return []


def batch_split(
    batch_size: float,
    batch_count: int,
    optimal_lv=5,
) -> List[List[float]]:
    result: List[List[float]] = []

    def split(current_batch_size: float, batch_idx=0, queue=None):
        nonlocal batch_count, optimal_lv, result

        if not queue:
            queue = []

        if len(queue) == batch_count - 1:
            queue.append(current_batch_size)
            result.append(queue.copy())
            queue.pop()
            return

        split_count = batch_count * (optimal_lv - batch_idx) + 1

        for i in range(split_count):
            split_head = round(current_batch_size * i / split_count, 2)
            split_remain = round(current_batch_size - split_head, 2)
            queue.append(split_head)

            if split_remain == 0:
                while len(queue) < batch_count:
                    queue.append(0)
                result.append(queue.copy())
                while len(queue) > batch_idx + 1:
                    queue.pop()
            else:
                split(split_remain, batch_idx=batch_idx + 1, queue=queue)
            queue.pop()

    split(batch_size)
    return result
