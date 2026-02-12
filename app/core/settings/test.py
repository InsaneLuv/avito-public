from pydantic_settings import SettingsConfigDict

from app.core.settings.production import ProdAppSettings


class TestAppSettings(ProdAppSettings):
    model_config = SettingsConfigDict(env_file=".test.env")
