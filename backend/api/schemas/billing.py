from decimal import Decimal
from pydantic import BaseModel, Field


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

    class Config:
        from_attributes = True


class BillCreate(BaseModel):
    room_id: int
    billing_month: str = Field(pattern=r"^\d{4}-\d{2}$")
    late_fee_applied: bool = False


class BillOut(BaseModel):
    id: int
    room_id: int
    billing_month: str
    rent_amount: Decimal
    water_units: Decimal
    water_amount: Decimal
    electric_units: Decimal
    electric_amount: Decimal
    garbage_fee: Decimal
    late_fee: Decimal
    late_fee_applied: bool
    total_amount: Decimal
    status: str

    class Config:
        from_attributes = True


class BillingConfigOut(BaseModel):
    water_rate: Decimal
    electric_rate: Decimal
    garbage_fee: Decimal
    late_fee: Decimal

    class Config:
        from_attributes = True


class BillingConfigUpdate(BaseModel):
    water_rate: Decimal = Field(ge=0)
    electric_rate: Decimal = Field(ge=0)
    garbage_fee: Decimal = Field(ge=0)
    late_fee: Decimal = Field(ge=0)
