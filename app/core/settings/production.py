from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import SettingsConfigDict

from app.core.settings.app import AppSettings



class ProdAppSettings(AppSettings):
    model_config = SettingsConfigDict(env_file=".env")

    OPENAI_API_TOKEN: SecretStr = Field()
    AVITO_CLIENT_ID: SecretStr = Field()
    AVITO_CLIENT_SECRET: SecretStr = Field()
