from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api.schemas.auth import Token, UserCreate, UserOut
from model.user import UserRole
from services.user_service import UserService
from utils.deps import get_current_user, get_db, require_roles
from utils.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = UserService(db).authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token)


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    service = UserService(db)
    if service.repo.get_by_username(payload.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    if service.repo.get_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Only allow registration for the very first user (bootstrap admin).
    if service.users_count() > 0:
        raise HTTPException(status_code=403, detail="Registration is closed")

    if payload.role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="First user must be admin")

    return service.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
    )


@router.get("/me", response_model=UserOut)
def me(user=Depends(get_current_user)):
    return user


@router.post("/users", response_model=UserOut, dependencies=[Depends(require_roles(UserRole.ADMIN))])
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    service = UserService(db)
    if service.repo.get_by_username(payload.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    if service.repo.get_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return service.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
    )
