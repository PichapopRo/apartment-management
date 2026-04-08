from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class MeterReadingCreate(BaseModel):
    room_id: int
    billing_month: str = Field(pattern=r"^\d{4}-\d{2}$")
    water_value: Decimal = Field(ge=0)
    electric_value: Decimal = Field(ge=0)


class MeterReadingOut(BaseModel):
    id: int
    room_id: int
    billing_month: str
    water_value: Decimal
    electric_value: Decimal
    model_config = ConfigDict(from_attributes=True)


class BillCreate(BaseModel):
    room_id: int
    billing_month: str = Field(pattern=r"^\d{4}-\d{2}$")
    late_fee_applied: bool = False
    water_units_override: Decimal | None = Field(default=None, ge=0)
    electric_units_override: Decimal | None = Field(default=None, ge=0)


class BillOut(BaseModel):
    id: int
    room_id: int
    billing_month: str
    rent_amount: Decimal
    water_units: Decimal
    water_units_override: Decimal | None = None
    water_amount: Decimal
    electric_units: Decimal
    electric_units_override: Decimal | None = None
    electric_amount: Decimal
    garbage_fee: Decimal
    late_fee: Decimal
    late_fee_applied: bool
    total_amount: Decimal
    status: str
    is_paid: bool
    paid_at: datetime | None = None
    remark: str | None = None
    model_config = ConfigDict(from_attributes=True)


class BillBulkCreate(BaseModel):
    items: list[BillCreate]


class BillBulkResult(BaseModel):
    created: list[BillOut]
    skipped: list[dict]


class BillingConfigOut(BaseModel):
    water_rate: Decimal
    electric_rate: Decimal
    garbage_fee: Decimal
    late_fee: Decimal
    model_config = ConfigDict(from_attributes=True)


class BillingConfigUpdate(BaseModel):
    water_rate: Decimal = Field(ge=0)
    electric_rate: Decimal = Field(ge=0)
    garbage_fee: Decimal = Field(ge=0)
    late_fee: Decimal = Field(ge=0)


class BillUpdate(BaseModel):
    is_paid: bool
    paid_at: datetime | None = None
    remark: str | None = None
