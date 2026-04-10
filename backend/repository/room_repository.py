from sqlalchemy.orm import Session

from model.room import Room


class RoomRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, room_id: int) -> Room | None:
        return self.db.query(Room).filter(Room.id == room_id).first()

    def get_by_number(self, room_number: str) -> Room | None:
        return self.db.query(Room).filter(Room.room_number == room_number).first()

    def list_all(self) -> list[Room]:
        return self.db.query(Room).order_by(Room.room_number.asc()).all()

    def list_available(self) -> list[Room]:
        return (
            self.db.query(Room)
            .filter(Room.status == "vacant")
            .order_by(Room.room_number.asc())
            .all()
        )

    def create(self, room: Room) -> Room:
        self.db.add(room)
        self.db.commit()
        self.db.refresh(room)
        return room

    def update(self, room: Room) -> Room:
        self.db.commit()
        self.db.refresh(room)
        return room

    def delete(self, room: Room) -> None:
        self.db.delete(room)
        self.db.commit()
