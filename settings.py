from os import environ

from pydantic import BaseSettings


class Settings(BaseSettings):
    REDIS_HOST: str

    def __init__(self):
        super(Settings, self).__init__()

    class Config:
        env_file = environ.get("ENV", ".env")
        case_sensitive = True


settings = Settings()
