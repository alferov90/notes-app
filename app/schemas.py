from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer


class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    is_active: bool
    created_at: datetime
    telegram_connected: bool = False


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserStats(BaseModel):
    events_count: int
    active_events: int
    telegram_connected: bool


class TelegramStatus(BaseModel):
    configured: bool
    connected: bool
    bot_username: str | None = None
    bot_ok: bool = False
    bot_error: str | None = None


class TelegramLink(BaseModel):
    link: str


class EventBase(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    event_time: time
    emoji: str = Field(default="⏰", max_length=8)
    days: str = Field(default="all", max_length=32)
    is_active: bool = True


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    event_time: time | None = None
    emoji: str | None = Field(default=None, max_length=8)
    days: str | None = Field(default=None, max_length=32)
    is_active: bool | None = None


class EventRead(EventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_notified_date: date | None = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("event_time")
    def serialize_time(self, t: time) -> str:
        return t.strftime("%H:%M")
