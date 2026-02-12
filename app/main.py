from contextlib import asynccontextmanager

from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import get_app_settings
from app.core.providers import ConfigProvider


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def setup_dependencies(app: FastAPI):
    container = make_async_container(
        ConfigProvider("prod"),
    )
    setup_dishka(container, app)
    return container


def get_application() -> FastAPI:
    settings = get_app_settings()

    application = FastAPI(**settings.app.fastapi_kwargs, lifespan=lifespan)
    setup_dependencies(application)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.allowed_hosts,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    from app.api.routes.health import router
    application.include_router(router, prefix=settings.app.api_prefix)
    from app.api.routes.prompt import router
    application.include_router(router, prefix=settings.app.api_prefix)
    return application


app = get_application()

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
