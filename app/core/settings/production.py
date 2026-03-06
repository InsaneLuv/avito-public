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
    SECURITY_CODE: Secret[str] = Field()
    BOT_UUID: Secret[str] = Field()
    TG_BOT_TOKEN: Secret[str] = Field()

    LIMITS_SERVICE_URL: str = Field(description="URL sub-service для управления лимитами")
