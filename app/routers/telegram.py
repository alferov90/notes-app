from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.telegram_client import is_configured

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.get("/status", response_model=schemas.TelegramStatus)
def telegram_status(current_user: User = Depends(get_current_user)):
    from app.config import settings

    return schemas.TelegramStatus(
        configured=is_configured(),
        connected=current_user.telegram_chat_id is not None,
        bot_username=settings.telegram_bot_username or None,
    )


@router.post("/link", response_model=schemas.TelegramLink)
def create_telegram_link(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram-бот не настроен на сервере",
        )
    link = crud.create_telegram_link(db, current_user)
    return schemas.TelegramLink(link=link)


@router.delete("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_telegram(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    crud.unlink_telegram(db, current_user)
