""" Creating mock data
"""
from random import randint
from random import sample
from typing import List

from faker import Faker

from sor import Dex
from sor import Pool
from sor import PoolToken
from sor import Tokens

fake = Faker()


def random_swap_fee():
    return randint(1, 5) / 100


def create_pool_tokens(count: int, tokens=None) -> List[PoolToken]:
    tokens = sample(Tokens, count) if not tokens else tokens
    return [
        PoolToken(
            token=token,
            amount=randint(10, 100),
        )
        for token in tokens
    ]


def create_pool(token_count: int, fee: float, tokens=None) -> Pool:
    tokens = create_pool_tokens(token_count, tokens=tokens)
    name = "-".join(fake.words(nb=2))
    return Pool(name, fee, tokens)


def create_many_pools(count: int, tokens=None) -> List[Pool]:
    return [
        create_pool(
            randint(2, 4),
            random_swap_fee(),
            tokens=tokens,
        )
        for _ in range(count)
    ]


def create_dexes(count: int, tokens=None) -> List[Dex]:
    def create_single_dex():
        return Dex(
            pools=create_many_pools(randint(1, 3 * count), tokens=tokens),
            name="-".join(fake.words(nb=3)),
            gas=randint(10, 20),
        )

    return [create_single_dex() for _ in range(count)]
