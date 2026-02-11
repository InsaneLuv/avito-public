import enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ImageSizes(BaseModel):
    model_config = ConfigDict(extra='ignore')

    size_140x105: Optional[str] = Field(None, alias="140x105")
    size_32x32: Optional[str] = Field(None, alias="32x32")
    size_640x480: Optional[str] = Field(None, alias="640x480")
    size_1280x960: Optional[str] = Field(None, alias="1280x960")
    size_192x192: Optional[str] = Field(None, alias="192x192")
    size_24x24: Optional[str] = Field(None, alias="24x24")
    size_256x256: Optional[str] = Field(None, alias="256x256")
    size_36x36: Optional[str] = Field(None, alias="36x36")
    size_48x48: Optional[str] = Field(None, alias="48x48")
    size_64x64: Optional[str] = Field(None, alias="64x64")
    size_72x72: Optional[str] = Field(None, alias="72x72")
    size_96x96: Optional[str] = Field(None, alias="96x96")


class ItemImages(BaseModel):
    count: int
    main: Dict[str, str]  # На самом деле здесь только "140x105", но сделаем словарем для гибкости


class ItemContext(BaseModel):
    id: int
    images: ItemImages | None = None
    price_string: str | None = None
    status_id: int | None = None
    title: str | None = None
    url: str | None = None
    user_id: int | None = None


class ContextValue(BaseModel):
    type: str
    value: ItemContext


class CallContent(BaseModel):
    status: str
    target_user_id: int


class ImageContent(BaseModel):
    sizes: ImageSizes


class ItemContent(BaseModel):
    image_url: str
    item_url: str
    price_string: str
    title: str


class LinkPreview(BaseModel):
    description: str
    domain: str
    images: ImageSizes
    title: str
    url: str


class LinkContent(BaseModel):
    # preview: LinkPreview
    text: str
    url: str


class LocationContent(BaseModel):
    kind: str
    lat: float
    lon: float
    text: str
    title: str


class VoiceContent(BaseModel):
    voice_id: str


class MessageContent(BaseModel):
    call: Optional[CallContent] = None
    flow_id: Optional[str] = None
    image: Optional[ImageContent] = None
    item: Optional[ItemContent] = None
    link: Optional[LinkContent] = None
    location: Optional[LocationContent] = None
    text: Optional[str] = None
    voice: Optional[VoiceContent] = None


class Message(BaseModel):
    author_id: int
    content: MessageContent
    created: int  # timestamp
    direction: str
    id: str
    type: str

    def for_ai(self):
        text = self.content.text
        link = self.content.link
        voice = self.content.voice
        picture = self.content.image

        content = None

        if text:
            content = text
        if link:
            content = link.text
        if voice:
            content = "Прикрепил аудиосообщение (невозможно прочитать)"
        if picture:
            content = "Прикрепил картинку (невозможно прочитать)"

        return {
            "role": "user" if self.direction == "in" else "assistant",
            "content": content,
        }


class Avatar(BaseModel):
    default: str
    # images: ImageSizes


class PublicUserProfile(BaseModel):
    avatar: Avatar
    item_id: int
    url: str
    user_id: int


class User(BaseModel):
    id: int
    name: str
    public_user_profile: Optional[PublicUserProfile] = None


class Chat(BaseModel):
    context: Optional[ContextValue] = None
    created: int  # timestamp
    id: str
    last_message: Message
    updated: int  # timestamp
    users: List[User]


class ChatsResponse(BaseModel):
    chats: List[Chat]


class ChatTypeEnum(enum.StrEnum):
    u2i = "u2i"
    u2u = "u2u"


class ChatsPayloadFilter(BaseModel):
    item_ids: list[int] | None = Field(default=None)
    unread_only: bool = False
    chat_types: list[ChatTypeEnum] | None = Field(default=None)
    limit: int = 100
    offset: int = 0


class UserData(BaseModel):
    email: str
    id: int
    name: str
    phone: str
    phones: List[str]
    profile_url: str


class MessagesResponse(BaseModel):
    messages: list[Message]
    meta: Any


class SimpleActionResponse(BaseModel):
    ok: bool


class Subscribtion(BaseModel):
    url: str
    version: str


class SubscribtionsResponse(BaseModel):
    subscriptions: list[Subscribtion] | None = Field(default_factory=list)


class SendMessage(BaseModel):
    text: str


class SendMessagePayload(BaseModel):
    message: SendMessage
    type: str = "text"
