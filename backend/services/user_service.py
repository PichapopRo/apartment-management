from sqlalchemy.orm import Session

from model.user import User, UserRole
from repository.user_repository import UserRepository
from utils.security import hash_password, verify_password


class UserService:
    def __init__(self, db: Session) -> None:
        self.repo = UserRepository(db)

    def authenticate(self, username: str, password: str) -> User | None:
        user = self.repo.get_by_username(username)
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str | None,
        role: UserRole,
    ) -> User:
        user = User(
            username=username.lower(),
            email=email.lower(),
            full_name=full_name,
            hashed_password=hash_password(password),
            role=role.value,
            is_active=True,
        )
        return self.repo.create(user)

    def users_count(self) -> int:
        return self.repo.count()

    def list_users(self) -> list[User]:
        return self.repo.list_all()

    def update_role(self, user: User, role: UserRole) -> User:
        user.role = role.value
        return self.repo.update(user)
