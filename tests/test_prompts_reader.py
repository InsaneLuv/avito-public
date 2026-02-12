import pytest

from app.models.avito import ChatsPayloadFilter, ChatsResponse, ChatTypeEnum, SendMessage, SendMessagePayload
from app.prompts.read import PromptEditor
from app.services.avito import Avito, AvitoBL, AvitoModels


@pytest.mark.asyncio
class TestPromptReader:

    async def test_prompt_file_exists(self, prompts_reader: PromptEditor):
        text = await prompts_reader.read_text("text.md")
        assert "##" in text