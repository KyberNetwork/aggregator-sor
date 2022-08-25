from os import environ


def debug():
    if "DEBUG" in environ:
        input()
