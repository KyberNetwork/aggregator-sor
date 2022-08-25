from functools import reduce
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Set

from pydantic import BaseModel
from terminaltables import AsciiTable


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


TokenUnitPrices: Dict[Token, USDPrice] = {
    "BTC": USDPrice(21_328.08),
    "ETH": USDPrice(1_630.25),
    "USDC": USDPrice(1.0),
    "TOMO": USDPrice(0.522186),
    "KNC": USDPrice(1.88),
    "USDT": USDPrice(1.0),
    "SOL": USDPrice(34.99),
}

PRICE_TABLE = AsciiTable(
    [["Symbol", "Price (USD)"], *[[token, price] for token, price in TokenUnitPrices.items()]]
)


def calc_value(token: Token, amount: float) -> float:
    price = TokenUnitPrices[token]
    return price * amount


def price_to_amount(token: Token, price: float) -> float:
    unit_price = TokenUnitPrices[token].value
    return price / unit_price


def amm_swap(delta_x: float, x: float, y: float) -> float:
    """Ref: https://youtu.be/1PbZMudPP5E?t=228
    x * y = k = (x + delta_x) * (y + delta_y)
    ==> delta_y = (y * delta_x) / (x + delta_x)
    """
    return (y * delta_x) / (x + delta_x)


# models & classes
class PoolToken(BaseModel):
    token: Token
    amount: float
    weight: Optional[float]

    def __str__(self):
        title = f"[{self.token}] {self.amount}\n"
        info = f"(reserve=${self.reserve}, weight={self.weight})\n"
        return title + info

    @property
    def reserve(self) -> float:
        price = TokenUnitPrices[self.token]
        return price * self.amount


class Pool(BaseModel):
    """Swap calculation based on Constant product market maker (x*y=k)"""

    name: str
    tokens: List[PoolToken]
    fee: float
    k: Optional[float]
    tvl: Optional[float]

    def __init__(self, name: str, fee: float, tokens: List[PoolToken]):
        super(Pool, self).__init__(name=name, tokens=tokens, fee=fee)
        self._update_tvl()
        self._update_k()
        self._set_token_weights()

    def __str__(self):
        title = f"POOL: {self.name} (fee: {self.fee}) [k={self.k}]"
        tokens = ("-" * 3).join([str(t) for t in self.tokens])
        return title + "\n---" + tokens

    def _update_tvl(self):
        self.tvl = sum([t.reserve for t in self.tokens])

    def _update_k(self):
        self.k = reduce(lambda x, y: x * y, [t.reserve for t in self.tokens])

    def _set_token_weights(self):
        assert self.tvl
        for tk in self.tokens:
            tk.weight = tk.reserve / self.tvl

    def get_token(self, token: Token) -> Optional[PoolToken]:
        return next((t for t in self.tokens if t.token == token), None)

    def swap(
        self,
        token_in: Token,
        amount_in: float,
        token_out: Token,
        do_swap=False,
    ) -> float:
        """Return amount-in and amount-out"""
        if not self.k:
            return 0

        if token_in == token_out:
            return 0

        pool_token_in = self.get_token(token_in)
        pool_token_out = self.get_token(token_out)

        if not pool_token_in or not pool_token_out:
            return 0

        amount_in_after_fee = amount_in * (1 - self.fee)
        x, y = pool_token_in.reserve, pool_token_out.reserve
        delta_x = calc_value(token_in, amount_in_after_fee)
        delta_y = amm_swap(delta_x, x, y)
        amount_out = price_to_amount(token_out, delta_y)

        if do_swap:
            pool_token_in.amount += amount_in
            pool_token_out.amount -= amount_out
            self._update_tvl()
            self._update_k()
            self._set_token_weights()

        return round(amount_out, 5)


class Dex(BaseModel):
    name: str
    pools: List[Pool]
    gas: float

    def __str__(self):
        dex_info = f"({len(self.pools)} pools) (gas: {self.gas})"
        title = f"\nDEX: {self.name} {dex_info}"
        pools = "\n\t".join([str(p) for p in self.pools])
        return title + "\n\t" + pools
