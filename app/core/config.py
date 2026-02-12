from functools import lru_cache
from typing import Literal

from pydantic import BaseModel

from app.core.settings.production import ProdAppSettings
from app.core.settings.test import TestAppSettings


class AppSettings(BaseModel):
    app: ProdAppSettings | TestAppSettings


@lru_cache
def get_app_settings(scope: Literal["prod", "test"] = "prod") -> AppSettings:
    app_env = AppSettings(app=ProdAppSettings()) if scope == "prod" else AppSettings(app=TestAppSettings())
    return app_env