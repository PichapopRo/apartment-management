from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from model.bill import Bill
from model.meter_reading import MeterReading
from model.room import Room
from repository.bill_repository import BillRepository
from repository.billing_config_repository import BillingConfigRepository
from repository.meter_reading_repository import MeterReadingRepository
from repository.room_repository import RoomRepository
from utils.errors import BadRequestError, ConflictError, NotFoundError


@dataclass
class BillCalculation:
    rent_amount: Decimal
    water_units: Decimal
    water_amount: Decimal
    electric_units: Decimal
    electric_amount: Decimal
    garbage_fee: Decimal
    late_fee: Decimal
    total_amount: Decimal


class BillingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.rooms = RoomRepository(db)
        self.readings = MeterReadingRepository(db)
        self.bills = BillRepository(db)
        self.configs = BillingConfigRepository(db)

    def calculate_bill(
        self,
        room: Room,
        current: MeterReading,
        previous: MeterReading | None,
        late_fee_applied: bool,
        water_rate: Decimal,
        electric_rate: Decimal,
        garbage_fee: Decimal,
        late_fee_amount: Decimal,
        water_units_override: Decimal | None = None,
        electric_units_override: Decimal | None = None,
    ) -> BillCalculation:
        water_units_calc = Decimal(current.water_value) - Decimal(
            previous.water_value if previous else 0
        )
        electric_units_calc = Decimal(current.electric_value) - Decimal(
            previous.electric_value if previous else 0
        )

        water_units = water_units_override if water_units_override is not None else water_units_calc
        electric_units = (
            electric_units_override if electric_units_override is not None else electric_units_calc
        )

        if water_units < 0 or electric_units < 0:
            raise BadRequestError("Meter reading cannot be less than previous month")

        water_amount = water_units * Decimal(water_rate)
        electric_amount = electric_units * Decimal(electric_rate)
        rent_amount = Decimal(room.rent_rate)
        late_fee = late_fee_amount if late_fee_applied else Decimal("0.00")

        total = rent_amount + water_amount + electric_amount + garbage_fee + late_fee

        return BillCalculation(
            rent_amount=rent_amount,
            water_units=water_units,
            water_amount=water_amount,
            electric_units=electric_units,
            electric_amount=electric_amount,
            garbage_fee=garbage_fee,
            late_fee=late_fee,
            total_amount=total,
        )

    def create_bill_for_month(
        self,
        room_id: int,
        billing_month: str,
        late_fee_applied: bool,
        water_units_override: Decimal | None = None,
        electric_units_override: Decimal | None = None,
    ) -> Bill:
        room = self.rooms.get_by_id(room_id)
        if room is None:
            raise NotFoundError("Room not found")

        if self.bills.get_by_room_month(room_id, billing_month):
            raise ConflictError("Bill already exists for this month")

        current = self.readings.get_by_room_month(room_id, billing_month)
        if current is None:
            raise NotFoundError("Current month meter reading not found")

        # naive previous month key: YYYY-MM minus 1 month
        year, month = billing_month.split("-")
        y = int(year)
        m = int(month)
        if m == 1:
            prev_key = f"{y-1:04d}-12"
        else:
            prev_key = f"{y:04d}-{m-1:02d}"
        previous = self.readings.get_by_room_month(room_id, prev_key)

        config = self.configs.get_config()
        calc = self.calculate_bill(
            room,
            current,
            previous,
            late_fee_applied,
            water_rate=Decimal(config.water_rate),
            electric_rate=Decimal(config.electric_rate),
            garbage_fee=Decimal(config.garbage_fee),
            late_fee_amount=Decimal(config.late_fee),
            water_units_override=water_units_override,
            electric_units_override=electric_units_override,
        )

        bill = Bill(
            room_id=room_id,
            billing_month=billing_month,
            rent_amount=calc.rent_amount,
            water_units=calc.water_units,
            water_units_override=water_units_override,
            water_amount=calc.water_amount,
            electric_units=calc.electric_units,
            electric_units_override=electric_units_override,
            electric_amount=calc.electric_amount,
            garbage_fee=calc.garbage_fee,
            late_fee=calc.late_fee,
            late_fee_applied=late_fee_applied,
            total_amount=calc.total_amount,
            status="UNPAID",
        )
        return self.bills.create(bill)
