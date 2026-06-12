from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import get_current_user
from app.security import create_access_token, verify_password
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    db_user = crud.create_user(db, user)
    token = create_access_token(db_user.id)
    return schemas.Token(access_token=token)


@router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    token = create_access_token(user.id)
    return schemas.Token(access_token=token)


@router.get("/me", response_model=schemas.UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return schemas.UserRead.model_validate(current_user).model_copy(
        update={"telegram_connected": current_user.telegram_chat_id is not None}
    )


@router.patch("/me", response_model=schemas.UserRead)
def update_me(
    updates: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = crud.update_user(db, current_user, updates)
    return schemas.UserRead.model_validate(user).model_copy(
        update={"telegram_connected": user.telegram_chat_id is not None}
    )


@router.get("/me/stats", response_model=schemas.UserStats)
def read_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_user_stats(db, current_user.id)
