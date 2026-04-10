from pydantic import BaseModel, ConfigDict


class ResidentRoomOut(BaseModel):
    room_number: str
    rent_rate: float
    status: str


class ResidentBillOut(BaseModel):
    billing_month: str
    total_amount: float
    status: str
    is_paid: bool


class ResidentSummaryOut(BaseModel):
    room: ResidentRoomOut | None = None
    latest_bill: ResidentBillOut | None = None
    model_config = ConfigDict(from_attributes=True)
