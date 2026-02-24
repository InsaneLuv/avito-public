from aiogram import Bot
from aiogram.types import InlineKeyboardButton
from aiogram.utils.formatting import Bold, Code, TextLink, as_line
from aiogram.utils.keyboard import InlineKeyboardBuilder


def new_assist_text(last_user_message: str, ai_assistant_content: str | None = None,  chat_url: str | None = None) -> str:
    text = '<tg-emoji emoji-id="5318861974375767587">🔥</tg-emoji> '
    text += as_line(
        Bold(TextLink("Новый чат", url=chat_url)),
        Bold(
            " с AI-Ассистентом!"
        )
    ).as_html()

    text += "\n"
    text += '<tg-emoji emoji-id="5397735522598659551">✏️</tg-emoji> '
    text += Bold('Пользователь написал').as_html()
    text += "\n"
    text += Code(last_user_message).as_html()

    if ai_assistant_content:
        text += "\n\n"
        text += '<tg-emoji emoji-id="5397681122542893003">🤖</tg-emoji> '
        text += Bold('AI-Ответ').as_html()
        text += "\n"
        text += Code(ai_assistant_content).as_html()
    return text


def new_assist_builder(chat_url: str, ad_url: str | None = None) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    row = builder.row()
    row.add(InlineKeyboardButton(text="Чат", url=chat_url, style="success", icon_custom_emoji_id="5397735522598659551"))
    if ad_url:
        row.add(InlineKeyboardButton(text="Объявление", url=ad_url, style="primary",
                                     icon_custom_emoji_id="5318861974375767587"))
    return builder


class TGNotificator:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.chat_id = -1003657683249

    async def new_assist(self, chat_url: str, ad_url: str | None = None,
                         last_message_content: str | None = None, ai_assistant_content: str | None = None):
        text = new_assist_text(
            last_message_content if last_message_content else "Неизв. содержимое", ai_assistant_content if ai_assistant_content else None, chat_url
        )
        kb = new_assist_builder(chat_url, ad_url).as_markup()
        return await self.bot.send_message(chat_id=self.chat_id, text=text, reply_markup=kb, parse_mode='HTML')
