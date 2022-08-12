""" Creating mock data
"""
from random import randint
from random import sample
from typing import List
from typing import Set

from faker import Faker

from main import *

fake = Faker()

Tokens: Set[Token] = {"A", "B", "C", "D", "E", "F"}


def random_token_price():
    return USDPrice(randint(1, 100) / 5)


def random_swap_fee():
    return randint(1, 5) / 100


def create_random_token_prices():
    return {tk: random_token_price() for tk in Tokens}


def create_pool_tokens(count: int) -> List[PoolToken]:
    tokens = sample(Tokens, count)
    return [
        PoolToken(
            token=token,
            reserve=randint(100, 1000),
        )
        for token in tokens
    ]


def create_pool(token_count: int, fee: float) -> Pool:
    tokens = create_pool_tokens(token_count)
    name = "-".join(fake.words(nb=2))
    return Pool(tokens=tokens, fee=fee, name=name)


def create_many_pools(count: int) -> List[Pool]:
    return [
        create_pool(
            randint(2, 6),
            random_swap_fee(),
        )
        for _ in range(count)
    ]


def create_dexes(count: int) -> List[Dex]:
    return [
        Dex(
            pools=create_many_pools(randint(1, 10)),
            name="-".join(fake.words(nb=3)),
        )
        for _ in range(count)
    ]
