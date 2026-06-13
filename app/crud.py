import secrets
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

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
    events_count = (
        db.query(func.count(models.RoutineEvent.id))
        .filter(models.RoutineEvent.user_id == user_id)
        .scalar()
        or 0
    )
    active_events = (
        db.query(func.count(models.RoutineEvent.id))
        .filter(
            models.RoutineEvent.user_id == user_id,
            models.RoutineEvent.is_active.is_(True),
        )
        .scalar()
        or 0
    )
    user = get_user(db, user_id)
    return schemas.UserStats(
        events_count=events_count,
        active_events=active_events,
        telegram_connected=bool(user and user.telegram_chat_id),
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


def get_events(db: Session, user_id: int) -> list[models.RoutineEvent]:
    return (
        db.query(models.RoutineEvent)
        .filter(models.RoutineEvent.user_id == user_id)
        .order_by(models.RoutineEvent.event_time)
        .all()
    )


def get_event(db: Session, user_id: int, event_id: int) -> models.RoutineEvent | None:
    return (
        db.query(models.RoutineEvent)
        .filter(
            models.RoutineEvent.id == event_id,
            models.RoutineEvent.user_id == user_id,
        )
        .first()
    )


def create_event(
    db: Session, user_id: int, event: schemas.EventCreate
) -> models.RoutineEvent:
    db_event = models.RoutineEvent(user_id=user_id, **event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def update_event(
    db: Session, event: models.RoutineEvent, updates: schemas.EventUpdate
) -> models.RoutineEvent:
    data = updates.model_dump(exclude_unset=True)
    if data:
        data["last_notified_date"] = None
    for field, value in data.items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event: models.RoutineEvent) -> None:
    db.delete(event)
    db.commit()


def mark_event_notified(db: Session, event: models.RoutineEvent, on_date: date) -> None:
    event.last_notified_date = on_date
    db.commit()
