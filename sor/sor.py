from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from .models import Dex
from .models import Pool
from .models import Token
from .preprocess import map_pool_by_name


class SmartOrderRouter:
    """TO BE IMPLEMENTED"""

    _dexes: Optional[List[Dex]] = None
    pools: Tuple[List[Pool], Dict[str, Pool]]

    @property
    def dexes(self):
        return self._dexes

    @dexes.setter
    def dexes(self, dexes: List[Dex]):
        self._dexes = dexes
        self.pools = map_pool_by_name(dexes)

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
