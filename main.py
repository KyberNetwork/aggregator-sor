from functools import reduce
from random import randint
from typing import Dict
from typing import List
from typing import Literal
from typing import Set
from typing import Tuple

from pydantic import BaseModel


class USDPrice:
    """Token price to USD"""

    __v: int

    def __init__(self, value):
        self.__v = value

    def __repr__(self):
        return f"${self.__v}"

    def __mul__(self, number: int):
        return self.__v * number

    def __add__(self, number: int):
        return self.__v + number

    def __sub__(self, number: int):
        return self.__v - number


# Token Symbols
Token = Literal["BTC", "ETH", "USDC", "TOMO", "KNC", "SOL"]
Tokens: Set[Token] = {"BTC", "ETH", "USDC", "TOMO", "KNC", "SOL"}


def set_token_price(token: Token) -> USDPrice:
    price = 1 if token == "USDC" else randint(2, 5)
    return USDPrice(price)


TokenUnitPrices: Dict[Token, USDPrice] = {
    token: set_token_price(token) for token in Tokens
}


# models & classes
class PoolToken(BaseModel):
    token: Token
    amount: int

    def __str__(self):
        return f"[{self.token}] {self.amount} (${self.reserve})"

    @property
    def reserve(self) -> int:
        price = TokenUnitPrices[self.token]
        return price * self.amount


class Pool(BaseModel):
    """Swap calculation based on Constant product market maker (x*y=k)"""

    name: str
    tokens: List[PoolToken]
    fee: float

    def __str__(self):
        title = f"POOL: {self.name} (fee: {self.fee}) [k={self.k}]"
        tokens = (" " * 5).join([str(t) for t in self.tokens])
        return title + "\n\t\t" + tokens

    @property
    def k(self):
        return reduce(lambda x, y: x * y, [t.reserve for t in self.tokens])


class Dex(BaseModel):
    name: str
    pools: List[Pool]
    gas: int

    def __str__(self):
        dex_info = f"({len(self.pools)} pools) (gas: {self.gas})"
        title = f"\nDEX: {self.name} {dex_info}"
        pools = "\n\t".join([str(p) for p in self.pools])
        return title + "\n\t" + pools


# Graph modelsn
Edge = Tuple[Dex, Dex]
