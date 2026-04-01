from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func

from database import Base


class RoomDocumentType(str, Enum):
    CITIZEN_ID = "citizen_id"
    CONTRACT = "contract"


class RoomDocument(Base):
    __tablename__ = "room_documents"
    __table_args__ = (
        UniqueConstraint("room_id", "doc_type", name="uq_room_doc_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    doc_type = Column(String(30), nullable=False)
    file_path = Column(String(512), nullable=False)
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
