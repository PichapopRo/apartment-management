from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from database import Base


class Tenancy(Base):
    __tablename__ = "tenancies"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    resident_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resident_name = Column(String(255), nullable=True)
    tenant_phone = Column(String(50), nullable=True)
    move_in_date = Column(Date, nullable=False)
    move_out_date = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    room = relationship("Room")
    resident = relationship("User")
