from typing import List
from typing import Literal
from typing import NewType
from typing import Tuple

from pydantic import BaseModel

# Token price to USD
USDPrice = NewType("USDPrice", float)

# Token Symbols
Token = Literal["A", "B", "C", "D", "E", "F"]


# models & classes
class PoolToken(BaseModel):
    token: Token
    reserve: int


class Pool(BaseModel):
    name: str
    tokens: List[PoolToken]
    fee: float


class Dex(BaseModel):
    name: str
    pools: List[Pool]


# Graph modelsn
Edge = Tuple[Dex, Dex]
