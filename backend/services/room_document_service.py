from sqlalchemy.orm import Session

from model.room_document import RoomDocument, RoomDocumentType
from repository.room_document_repository import RoomDocumentRepository


class RoomDocumentService:
    def __init__(self, db: Session) -> None:
        self.repo = RoomDocumentRepository(db)

    def upsert_document(
        self,
        room_id: int,
        doc_type: RoomDocumentType,
        file_path: str,
        uploaded_by_user_id: int | None,
    ) -> RoomDocument:
        existing = self.repo.get_by_room_type(room_id=room_id, doc_type=doc_type.value)
        if existing:
            existing.file_path = file_path
            existing.uploaded_by_user_id = uploaded_by_user_id
            return self.repo.update(existing)

        doc = RoomDocument(
            room_id=room_id,
            doc_type=doc_type.value,
            file_path=file_path,
            uploaded_by_user_id=uploaded_by_user_id,
        )
        return self.repo.create(doc)
