from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app import models, schemas
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
    return schemas.UserStats(notes_count=notes_count, pinned_count=pinned_count)


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
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note: models.Note) -> None:
    db.delete(note)
    db.commit()
