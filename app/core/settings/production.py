from pydantic import Field, Secret, SecretStr
from pydantic_settings import SettingsConfigDict

from app.core.settings.app import AppBase


class ProdAppSettings(AppBase):
    model_config = SettingsConfigDict(env_file=".env")

    OPENAI_API_TOKEN: SecretStr = Field()
    AVITO_CLIENT_ID: SecretStr = Field()
    AVITO_CLIENT_SECRET: SecretStr = Field()

    SQUID_PROXY_HOST: Secret[str] = Field()
    SQUID_PROXY_PORT: Secret[int] = Field()
    SQUID_PROXY_USER: Secret[str] = Field()
    SQUID_PROXY_PASSWORD: Secret[str] = Field()
    SECUTITY_CODE: Secret[str] = Field()
