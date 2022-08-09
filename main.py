from typing import List, Literal, NewType, Dict, Set
from random import randint, sample
from pydantic import BaseModel
from faker import Faker

fake = Faker()


# Token price to USD
USDPrice = NewType("USDPrice", float)
randPrice = lambda: USDPrice(randint(1, 100) / 5)

# Token Symbols
Token = Literal["A", "B", "C", "D", "E", "F"]

Tokens: Set[Token] = {"A", "B", "C", "D", "E", "F"}
Prices: Dict[Token, USDPrice] = {tk: randPrice() for tk in Tokens}


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


# creating mocks
def create_pool_tokens(count: int) -> List[PoolToken]:
    tokens = sample(Tokens, count)
    return [PoolToken(token=token, reserve=randint(100, 1000)) for token in tokens]


def create_pool(token_count: int, fee: float) -> Pool:
    tokens = create_pool_tokens(token_count)
    name = ",".join(fake.name())
    return Pool(tokens=tokens, fee=fee, name=name)


def create_many_pools(count: int) -> List[Pool]:
    randomFee = lambda: randint(1, 5) / 100
    pool = lambda: create_pool(randint(2, 6), randomFee())
    return [pool() for _ in range(count)]


def create_dexes(count: int) -> List[Dex]:
    dex = lambda: Dex(
        pools=create_many_pools(randint(1, 10)),
        name="-".join(fake.words(nb=3)),
    )
    return [dex() for _ in range(count)]
