import logging.config
import os

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    TITLE: str
    VERSION: str
    ORIGIN_VERSION: str
    REDIS_HOST: str
    DROP_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    EXPIRE_TIME: str
    SELECTEL_S3_ACCESS_KEY: str
    SELECTEL_S3_SECRET_KEY: str
    BUCKET_NAME_AVATARS: str
    BUCKET_NAME_BACK_PADS: str
    RABBIT_LOGIN: str
    RABBIT_PASSWORD: str
    RABBIT_HOST: str
    AVATARS_LINK: str
    BACK_PADS_LINK: str
    X_ACCESS_TOKEN: str
    MODE: int = 0
    COMMUNITY_SERVICE_URL: str
    COMMUNITY_SERVICE_TOKEN: str
    EVENT_SERVICE_URL: str
    EVENT_SERVICE_TOKEN: str
    ORGANISER_SERVICE_URL: str
    ORGANISER_SERVICE_TOKEN: str

    @property
    def DATABASE_URL_asyncpg(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def DATABASE_URL_psycopg(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def rabbit_conn(self):
        return f"amqp://{self.RABBIT_LOGIN}:{self.RABBIT_PASSWORD}@{self.RABBIT_HOST}"

    @property
    def mode(self):
        if self.MODE == 0:
            return True
        else:
            return False

    model_config = SettingsConfigDict(env_file=os.path.abspath(".env"))


settings = Settings()


def setup_logging():
    with open('logging.yml', 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)


