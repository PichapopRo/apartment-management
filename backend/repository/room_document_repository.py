from sqlalchemy.orm import Session

from model.room_document import RoomDocument


class RoomDocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_room_type(self, room_id: int, doc_type: str) -> RoomDocument | None:
        return (
            self.db.query(RoomDocument)
            .filter(RoomDocument.room_id == room_id, RoomDocument.doc_type == doc_type)
            .first()
        )

    def create(self, doc: RoomDocument) -> RoomDocument:
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def update(self, doc: RoomDocument) -> RoomDocument:
        self.db.commit()
        self.db.refresh(doc)
        return doc
