import asyncio
import time
from functools import wraps

from dishka import FromDishka
from dishka.integrations.taskiq import inject
from taskiq import InMemoryBroker

from app.services.avito import AvitoBL

broker = InMemoryBroker()


def rate_limit(cooldown: int):
    """Ограничивает частоту вызова асинхронной функции."""
    _lock = asyncio.Lock()
    _last_run: float | None = None

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal _last_run
            async with _lock:
                now = time.time()
                if _last_run is not None and (now - _last_run) < cooldown:
                    return None
                _last_run = now
            return await func(*args, **kwargs)
        return wrapper
    return decorator


@broker.task()
@inject
@rate_limit(cooldown=15)
async def avito_bl_exec(avito: FromDishka[AvitoBL]):
    await avito.meta()