import pytest

from app.services.limits import LimitsUOW


@pytest.mark.asyncio
class TestLimitsUOW:

    async def test_get_bot(self, limits_uow: LimitsUOW):
        bot = await limits_uow.get_bot()
        assert bot

    async def test_inc_dec(self, limits_uow: LimitsUOW):
        bot = await limits_uow.get_bot()
        assert bot
        await limits_uow.increment_usage()
        inc_bot = await limits_uow.get_bot()
        assert inc_bot.count > bot.count
        await limits_uow.decrement_usage()
        dec_bot = await limits_uow.get_bot()
        assert dec_bot.count < inc_bot.count
