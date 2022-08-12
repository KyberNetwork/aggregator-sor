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

    def __str__(self):
        return f"[{self.token}] {self.reserve}"


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

    def __str__(self):
        title = f"\nDEX: {self.name} ({len(self.pools)} pools)"
        pools = "\n\t".join([str(p) for p in self.pools])
        return title + "\n\t" + pools


# Graph modelsn
Edge = Tuple[Dex, Dex]
