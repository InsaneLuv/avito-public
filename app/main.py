import asyncio
from contextlib import asynccontextmanager

import aiogram
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dishka import FromDishka
from dishka.integrations.aiogram import AiogramProvider
from dishka.integrations.aiogram import inject
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from taskiq import AsyncBroker

from app.core.config import get_app_settings
from app.core.providers import ConfigProvider, ServiceProvider
from app.prompts.read import PromptEditor
from app.tasks.base import broker, avito_bl_exec

scheduler = AsyncIOScheduler()
from aiogram import Bot, Dispatcher, F, types, Router
from aiogram.types import Message
from aiogram.filters import Command

dp = Dispatcher()
router = Router()


@router.message(F.document.file_name.endswith(".md"))
@inject
async def handle_md_file(message: Message, bot: Bot, editor: FromDishka[PromptEditor]):
    file = await bot.get_file(message.document.file_id)
    content = await bot.download_file(file.file_path)
    text = content.read().decode("utf-8")
    await editor.write_text(text)
    await message.answer(f"Готово!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not broker.is_worker_process:
        await broker.startup()
    settings = get_app_settings()
    setup_dependencies_aiogram()
    dp.include_router(router)
    bot = Bot(token=settings.app.TG_BOT_TOKEN.get_secret_value())
    asyncio.create_task(dp.start_polling(bot))
    scheduler.start()
    scheduler.add_job(avito_bl_exec.kiq, 'interval', seconds=5)
    yield
    if not broker.is_worker_process:
        await broker.shutdown()

    scheduler.shutdown()


def setup_dependencies_aiogram():
    from dishka import make_async_container
    from dishka.integrations.aiogram import setup_dishka
    container = make_async_container(
        ConfigProvider("prod"),
        ServiceProvider(),
        AiogramProvider()
    )
    setup_dishka(container, router, auto_inject=True)
    return container


def setup_dependencies(app: FastAPI):
    from dishka import make_async_container
    from dishka.integrations.fastapi import setup_dishka, FastapiProvider
    container = make_async_container(
        ConfigProvider("prod"),
        ServiceProvider(),
        FastapiProvider()
    )
    setup_dishka(container, app)
    return container


def setup_dependencies_taskiq(_broker: AsyncBroker):
    from dishka import make_async_container
    from dishka.integrations.taskiq import setup_dishka, TaskiqProvider
    container = make_async_container(
        ConfigProvider("prod"),
        ServiceProvider(),
        TaskiqProvider()
    )
    setup_dishka(container, broker=_broker)
    return container


def get_application() -> FastAPI:
    settings = get_app_settings()

    application = FastAPI(**settings.app.fastapi_kwargs, lifespan=lifespan)
    setup_dependencies(application)
    setup_dependencies_taskiq(broker)

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
