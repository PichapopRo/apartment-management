from datetime import date
from typing import Optional

from pydantic import BaseModel


class TenancyAssign(BaseModel):
    room_id: int
    resident_user_id: Optional[int] = None
    resident_name: Optional[str] = None
    move_in_date: date


class TenancyMoveOut(BaseModel):
    move_out_date: date


class TenancyOut(BaseModel):
    id: int
    room_id: int
    resident_user_id: Optional[int] = None
    resident_name: Optional[str] = None
    move_in_date: date
    move_out_date: Optional[date] = None
    is_active: bool

    class Config:
        from_attributes = True
