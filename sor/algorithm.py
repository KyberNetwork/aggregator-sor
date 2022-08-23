from collections.abc import Callable
from typing import Dict
from typing import List
from typing import Optional

from .models import Dex
from .models import Edge
from .models import Pool
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


Splits = List[float]
BatchSplitCallback = Callable[[Splits], None]


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
            split(split_remain, batch_idx=batch_idx + 1, queue=queue)
            queue.pop()

    split(batch_size)

    return result if not callback else None
