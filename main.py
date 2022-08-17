from functools import reduce
from random import randint
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Set
from typing import Tuple

from pydantic import BaseModel


class USDPrice:
    """Token price to USD"""

    value: float

    def __init__(self, value: float):
        self.value = value

    def __repr__(self):
        return f"${self.value}"

    def __mul__(self, number: float):
        return self.value * number

    def __add__(self, number: float):
        return self.value + number

    def __sub__(self, number: float):
        return self.value - number


# Token Symbols
Token = Literal["BTC", "ETH", "USDC", "TOMO", "KNC", "SOL", "USDT"]
Tokens: Set[Token] = {"BTC", "ETH", "USDC", "TOMO", "KNC", "SOL", "USDT"}


def set_token_price(token: Token) -> USDPrice:
    price = 1 if token in {"USDC", "USDT"} else randint(2, 5)
    return USDPrice(price)


TokenUnitPrices: Dict[Token, USDPrice] = {
    token: set_token_price(token) for token in Tokens
}


def calc_value(token: Token, amount: float) -> float:
    price = TokenUnitPrices[token]
    return price * amount


def price_to_amount(token: Token, price: float) -> float:
    unit_price = TokenUnitPrices[token].value
    return price / unit_price


def amm_swap(new_x: float, x: float, y: float, k: float) -> float:
    """return delta(y)
    x * y * ...rest = k
    x * y = k / ...rest = x' * y'
    y' = k / (x' * ...rest)
    Ref: https://youtu.be/1PbZMudPP5E?t=228
    """
    rest = k / (x * y)
    new_y = k / (rest * new_x)
    delta = y - new_y
    return delta


# models & classes
class PoolToken(BaseModel):
    token: Token
    amount: float

    def __str__(self):
        return f"[{self.token}] {self.amount} (${self.reserve})"

    @property
    def reserve(self) -> float:
        price = TokenUnitPrices[self.token]
        return price * self.amount

    def update_amount(self, amount_change: float):
        self.amount += amount_change


class Pool(BaseModel):
    """Swap calculation based on Constant product market maker (x*y=k)"""

    name: str
    tokens: List[PoolToken]
    fee: float
    k: Optional[float]

    def __init__(self, name: str, fee: float, tokens: List[PoolToken]):
        super(Pool, self).__init__(name=name, tokens=tokens, fee=fee)
        self._update_k()

    def __str__(self):
        title = f"POOL: {self.name} (fee: {self.fee}) [k={self.k}]"
        tokens = (" " * 5).join([str(t) for t in self.tokens])
        return title + "\n\t\t" + tokens

    def _update_k(self):
        self.k = reduce(lambda x, y: x * y, [t.reserve for t in self.tokens])

    def has_token(self, token: Token) -> Optional[PoolToken]:
        return next((t for t in self.tokens if t.token == token), None)

    def swap(
        self,
        token_in: Token,
        amount_in: float,
        token_out: Token,
        do_swap=False,
    ) -> Tuple[float, float]:
        """Return amount-in and amount-out"""
        if not self.k:
            return 0, 0

        if token_in == token_out:
            return 0, 0

        pool_token_in = self.has_token(token_in)
        pool_token_out = self.has_token(token_out)

        if not pool_token_in or not pool_token_out:
            return 0, 0

        amount_in_after_fee = amount_in * (1 - self.fee)
        x, y = pool_token_in.reserve, pool_token_out.reserve
        new_token_in_mount = amount_in_after_fee + pool_token_in.amount
        new_x = calc_value(token_in, new_token_in_mount)
        delta_y = amm_swap(new_x, x, y, self.k)
        delta_amount = price_to_amount(token_out, delta_y)

        if do_swap:
            pool_token_in.update_amount(amount_in)
            pool_token_out.update_amount(-delta_amount)
            self._update_k()

        return amount_in, delta_amount


class Dex(BaseModel):
    name: str
    pools: List[Pool]
    gas: float

    def __str__(self):
        dex_info = f"({len(self.pools)} pools) (gas: {self.gas})"
        title = f"\nDEX: {self.name} {dex_info}"
        pools = "\n\t".join([str(p) for p in self.pools])
        return title + "\n\t" + pools


# Graph modelsn
Edge = Tuple[Dex, Dex]
