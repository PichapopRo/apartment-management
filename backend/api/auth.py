from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api.schemas.auth import Token, UserCreate, UserOut, UserRoleUpdate
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

    # First user must be admin. After that, default all registrations to resident.
    if service.users_count() == 0:
        if payload.role != UserRole.ADMIN:
            raise HTTPException(status_code=400, detail="First user must be admin")
        role = UserRole.ADMIN
    else:
        role = UserRole.RESIDENT

    return service.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=role,
    )


@router.get("/me", response_model=UserOut)
def me(user=Depends(get_current_user)):
    return user


@router.get("/bootstrap")
def bootstrap_status(db: Session = Depends(get_db)):
    service = UserService(db)
    return {"admin_exists": service.users_count() > 0}


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


@router.get("/users", response_model=list[UserOut], dependencies=[Depends(require_roles(UserRole.ADMIN))])
def list_users(db: Session = Depends(get_db)):
    return UserService(db).list_users()


@router.patch("/users/{user_id}/role", response_model=UserOut, dependencies=[Depends(require_roles(UserRole.ADMIN))])
def update_user_role(user_id: int, payload: UserRoleUpdate, db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == 1 and payload.role != UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="First user must remain admin")
    return service.update_role(user, payload.role)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles(UserRole.ADMIN))])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == 1:
        raise HTTPException(status_code=400, detail="Cannot delete the first admin user")
    service.repo.delete(user)
    return None
