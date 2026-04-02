from enum import Enum

from sqlalchemy import Column, DateTime, Integer, Numeric, String, func

from database import Base


class RoomStatus(str, Enum):
    VACANT = "vacant"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String(50), unique=True, index=True, nullable=False)
    floor = Column(Integer, nullable=True)
    rent_rate = Column(Numeric(12, 2), nullable=False, default=0)
    water_rate = Column(Numeric(10, 2), nullable=False, default=0)
    electric_rate = Column(Numeric(10, 2), nullable=False, default=0)
    status = Column(String(20), nullable=False, default=RoomStatus.VACANT.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
