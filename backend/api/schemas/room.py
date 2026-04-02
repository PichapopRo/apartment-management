from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from model.room import RoomStatus


class RoomCreate(BaseModel):
    room_number: str = Field(min_length=1, max_length=50)
    floor: Optional[int] = None
    rent_rate: Decimal = Field(ge=0)
    water_rate: Decimal = Field(ge=0)
    electric_rate: Decimal = Field(ge=0)
    status: RoomStatus = RoomStatus.VACANT


class RoomUpdate(BaseModel):
    floor: Optional[int] = None
    rent_rate: Optional[Decimal] = Field(default=None, ge=0)
    water_rate: Optional[Decimal] = Field(default=None, ge=0)
    electric_rate: Optional[Decimal] = Field(default=None, ge=0)
    status: Optional[RoomStatus] = None


class RoomOut(BaseModel):
    id: int
    room_number: str
    floor: Optional[int]
    rent_rate: Decimal
    water_rate: Decimal
    electric_rate: Decimal
    status: RoomStatus
    current_resident_name: Optional[str] = None

    class Config:
        from_attributes = True


class RoomPublic(BaseModel):
    room_number: str
    status: RoomStatus
