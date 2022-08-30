from collections.abc import Callable
from typing import List
from typing import Optional
from typing import Tuple


Splits = List[float]
BatchSplitCallback = Callable[[Splits], None]


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

    if split_count == 1:
        return handler(volume_in, 0), [volume_in]

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
