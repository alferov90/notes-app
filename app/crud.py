import secrets
from datetime import datetime, timezone

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.config import settings
from app.security import hash_password


def get_user(db: Session, user_id: int) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(
        email=user.email.lower(),
        name=user.name.strip(),
        hashed_password=hash_password(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(
    db: Session, user: models.User, updates: schemas.UserUpdate
) -> models.User:
    data = updates.model_dump(exclude_unset=True)
    if "password" in data:
        data["hashed_password"] = hash_password(data.pop("password"))
    if "name" in data:
        data["name"] = data["name"].strip()
    for field, value in data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def get_user_stats(db: Session, user_id: int) -> schemas.UserStats:
    notes_count = (
        db.query(func.count(models.Note.id))
        .filter(models.Note.user_id == user_id)
        .scalar()
        or 0
    )
    pinned_count = (
        db.query(func.count(models.Note.id))
        .filter(models.Note.user_id == user_id, models.Note.is_pinned.is_(True))
        .scalar()
        or 0
    )
    reminders_count = (
        db.query(func.count(models.Note.id))
        .filter(
            models.Note.user_id == user_id,
            models.Note.reminder_at.isnot(None),
            models.Note.reminder_sent.is_(False),
        )
        .scalar()
        or 0
    )
    return schemas.UserStats(
        notes_count=notes_count,
        pinned_count=pinned_count,
        reminders_count=reminders_count,
    )


def get_user_by_link_token(db: Session, token: str) -> models.User | None:
    return (
        db.query(models.User)
        .filter(models.User.telegram_link_token == token)
        .first()
    )


def create_telegram_link(db: Session, user: models.User) -> str:
    user.telegram_link_token = secrets.token_hex(24)
    db.commit()
    db.refresh(user)
    return f"https://t.me/{settings.telegram_bot_username}?start={user.telegram_link_token}"


def link_telegram(db: Session, user: models.User, chat_id: int) -> None:
    user.telegram_chat_id = chat_id
    user.telegram_link_token = None
    db.commit()


def unlink_telegram(db: Session, user: models.User) -> None:
    user.telegram_chat_id = None
    user.telegram_link_token = None
    db.commit()


def get_due_reminders(db: Session) -> list[models.Note]:
    now = datetime.now(timezone.utc)
    return (
        db.query(models.Note)
        .options(joinedload(models.Note.owner))
        .join(models.User)
        .filter(
            models.Note.reminder_at.isnot(None),
            models.Note.reminder_at <= now,
            models.Note.reminder_sent.is_(False),
            models.User.telegram_chat_id.isnot(None),
        )
        .all()
    )


def mark_reminder_sent(db: Session, note: models.Note) -> None:
    note.reminder_sent = True
    db.commit()


def get_notes(
    db: Session, user_id: int, search: str | None = None
) -> list[models.Note]:
    query = db.query(models.Note).filter(models.Note.user_id == user_id)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(models.Note.title.ilike(pattern), models.Note.content.ilike(pattern))
        )
    return query.order_by(
        models.Note.is_pinned.desc(), models.Note.updated_at.desc()
    ).all()


def get_note(db: Session, user_id: int, note_id: int) -> models.Note | None:
    return (
        db.query(models.Note)
        .filter(models.Note.id == note_id, models.Note.user_id == user_id)
        .first()
    )


def create_note(
    db: Session, user_id: int, note: schemas.NoteCreate
) -> models.Note:
    db_note = models.Note(user_id=user_id, **note.model_dump())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def update_note(
    db: Session, note: models.Note, updates: schemas.NoteUpdate
) -> models.Note:
    data = updates.model_dump(exclude_unset=True)
    if "reminder_at" in data:
        if data["reminder_at"] is None:
            data["reminder_sent"] = False
        else:
            reminder = data["reminder_at"]
            if reminder.tzinfo is None:
                reminder = reminder.replace(tzinfo=timezone.utc)
            data["reminder_at"] = reminder
            data["reminder_sent"] = False
    for field, value in data.items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note: models.Note) -> None:
    db.delete(note)
    db.commit()
