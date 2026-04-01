from sqlalchemy.orm import Session

from model.tenancy import Tenancy


class TenancyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active_by_room(self, room_id: int) -> Tenancy | None:
        return (
            self.db.query(Tenancy)
            .filter(Tenancy.room_id == room_id, Tenancy.is_active.is_(True))
            .first()
        )

    def get_active_by_resident(self, resident_user_id: int) -> Tenancy | None:
        return (
            self.db.query(Tenancy)
            .filter(
                Tenancy.resident_user_id == resident_user_id, Tenancy.is_active.is_(True)
            )
            .first()
        )

    def get_by_id(self, tenancy_id: int) -> Tenancy | None:
        return self.db.query(Tenancy).filter(Tenancy.id == tenancy_id).first()

    def create(self, tenancy: Tenancy) -> Tenancy:
        self.db.add(tenancy)
        self.db.commit()
        self.db.refresh(tenancy)
        return tenancy

    def update(self, tenancy: Tenancy) -> Tenancy:
        self.db.commit()
        self.db.refresh(tenancy)
        return tenancy
