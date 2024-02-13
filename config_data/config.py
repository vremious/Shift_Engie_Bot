from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str  # Токен для доступа к телеграм-боту


@dataclass
class SecKey:
    security_key: str


@dataclass
class Config:
    tg_bot: TgBot


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(tg_bot=TgBot(token=env('BOT_TOKEN')))


def load_proxy(path: str | None = None):
    env = Env()
    env.read_env(path)
    return env('PROXY_URL')


def load_secret(path: str | None = None):
    env = Env()
    env.read_env(path)
    return SecKey(security_key=env('SECURITY_KEY'))


def load_oracle_dsn(path: str | None = None):
    env = Env()
    env.read_env(path)
    return env('ORACLE_DSN')


def load_oracle_user(path: str | None = None):
    env = Env()
    env.read_env(path)
    return env('ORACLE_USER')


def load_oracle_password(path: str | None = None):
    env = Env()
    env.read_env(path)
    return env('ORACLE_PASSWORD')


def cats(path: str | None = None):
    env = Env()
    env.read_env(path)
    return env('API_CATS_URL')


def dogs(path: str | None = None):
    env = Env()
    env.read_env(path)
    return env('API_DOGS_URL')
