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
Token = Literal["A", "B", "C", "D", "E", "F"]
Tokens: Set[Token] = {"A", "B", "C", "D", "E", "F"}

TokenUnitPrices: Dict[Token, USDPrice] = {
    token: USDPrice(randint(1, 10)) for token in Tokens
}


# models & classes
class PoolToken(BaseModel):
    token: Token
    reserve: int

    def __str__(self):
        reserveUsd = TokenUnitPrices[self.token] * self.reserve
        return f"[{self.token}] {self.reserve} (${reserveUsd})"


class Pool(BaseModel):
    name: str
    tokens: List[PoolToken]
    fee: float

    def __str__(self):
        title = f"POOL: {self.name} (fee: {self.fee})"
        tokens = (" " * 5).join([str(t) for t in self.tokens])
        return title + "\n\t\t" + tokens


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
