import os
import sys

from app.prompts.read import PromptReader

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import AsyncGenerator
import pytest

from app.services.avito import Avito, AvitoBL

import dotenv
from openai import AsyncOpenAI

dotenv.load_dotenv()
from httpx import AsyncClient

SQUID_PROXY_HOST = os.getenv("SQUID_PROXY_HOST")
SQUID_PROXY_PORT = os.getenv("SQUID_PROXY_PORT")
SQUID_PROXY_USER = os.getenv("SQUID_PROXY_USER")
SQUID_PROXY_PASSWORD = os.getenv("SQUID_PROXY_PASSWORD")


@pytest.fixture(scope="session")
def client_id():
    return os.getenv("AVITO_CLIENT_ID")


@pytest.fixture(scope="session")
def client_secret():
    return os.getenv("AVITO_CLIENT_SECRET")


@pytest.fixture(scope="session")
def openai_api_token():
    return os.getenv("OPENAI_API_TOKEN")


@pytest.fixture(scope="session")
async def httpx_client_proxied() -> AsyncGenerator[AsyncClient, None]:
    """Создаем HTTP клиент с прокси для всей сессии."""
    async with AsyncClient(
            proxy=f"http://{SQUID_PROXY_USER}:{SQUID_PROXY_PASSWORD}@{SQUID_PROXY_HOST}:{SQUID_PROXY_PORT}", timeout=600) as client:
        yield client


@pytest.fixture(scope="function")
async def avito(client_id, client_secret):
    """Создаем клиент Avito для всей сессии тестов."""
    # Важно: создаем клиент и используем его в том же event loop
    client = Avito(client_id, client_secret)
    await client.get_user_data()
    return client


@pytest.fixture(scope="session")
async def openai(openai_api_token, httpx_client_proxied):
    """Создаем клиент OpenAI для всей сессии тестов."""
    return AsyncOpenAI(api_key=openai_api_token, http_client=httpx_client_proxied, timeout=600)

@pytest.fixture(scope="session")
async def prompts_reader():
    client = PromptReader()
    return client

@pytest.fixture(scope="session")
async def prompt(prompts_reader):
    return await prompts_reader.read_text("text.md")



@pytest.fixture(scope="function")
async def avito_bl(avito, openai, prompt):
    client = AvitoBL(avito, openai, prompt)
    return client


