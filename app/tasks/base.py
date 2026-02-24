from dishka import FromDishka
from dishka.integrations.taskiq import inject
from taskiq import InMemoryBroker

from app.services.avito import AvitoBL

broker = InMemoryBroker()

@broker.task()
@inject
async def avito_bl_exec(avito: FromDishka[AvitoBL]):
    await avito.meta()