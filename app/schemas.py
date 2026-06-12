from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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
    notes_count: int
    pinned_count: int
    reminders_count: int = 0


class TelegramStatus(BaseModel):
    configured: bool
    connected: bool
    bot_username: str | None = None


class TelegramLink(BaseModel):
    link: str


class NoteBase(BaseModel):
    title: str = Field(default="", max_length=255)
    content: str = ""
    color: str = Field(default="#6366f1", max_length=32)
    is_pinned: bool = False


class NoteCreate(NoteBase):
    reminder_at: datetime | None = None


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    content: str | None = None
    color: str | None = Field(default=None, max_length=32)
    is_pinned: bool | None = None
    reminder_at: datetime | None = None


class NoteRead(NoteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reminder_at: datetime | None = None
    reminder_sent: bool = False
    created_at: datetime
    updated_at: datetime
