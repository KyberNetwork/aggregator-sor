from os import environ
from typing import Callable
from typing import Optional


def debug(f: Optional[Callable] = None):
    if "DEBUG" in environ:
        if f:
            f()
        input()
