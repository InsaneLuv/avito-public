import pytest

from app.services.avito import AvitoBL


@pytest.mark.asyncio
class TestAvitoBL:

    async def test_avito_bl(self, avito_bl: AvitoBL):
        await avito_bl.meta()
