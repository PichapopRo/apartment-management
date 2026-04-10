from io import BytesIO

import pandas as pd
from sqlalchemy.orm import Session

from model.bill import Bill
from model.meter_reading import MeterReading
from model.room import Room


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _to_xlsx(self, df: pd.DataFrame, sheet_name: str) -> bytes:
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        output.seek(0)
        return output.read()

    def export_bills(self, billing_month: str) -> bytes:
        rows = (
            self.db.query(Bill, Room)
            .join(Room, Room.id == Bill.room_id)
            .filter(Bill.billing_month == billing_month)
            .order_by(Room.room_number.asc())
            .all()
        )
        data = []
        for bill, room in rows:
            data.append(
                {
                    "room_number": room.room_number,
                    "billing_month": bill.billing_month,
                    "rent_amount": float(bill.rent_amount),
                    "water_units": float(bill.water_units),
                    "water_amount": float(bill.water_amount),
                    "electric_units": float(bill.electric_units),
                    "electric_amount": float(bill.electric_amount),
                    "garbage_fee": float(bill.garbage_fee),
                    "late_fee": float(bill.late_fee),
                    "late_fee_applied": bool(bill.late_fee_applied),
                    "total_amount": float(bill.total_amount),
                    "status": bill.status,
                    "is_paid": bool(bill.is_paid),
                    "paid_at": bill.paid_at.isoformat() if bill.paid_at else "",
                    "remark": bill.remark or "",
                }
            )
        df = pd.DataFrame(data)
        return self._to_xlsx(df, sheet_name="Bills")

    def export_readings(self, billing_month: str) -> bytes:
        rows = (
            self.db.query(MeterReading, Room)
            .join(Room, Room.id == MeterReading.room_id)
            .filter(MeterReading.billing_month == billing_month)
            .order_by(Room.room_number.asc())
            .all()
        )
        data = []
        for reading, room in rows:
            data.append(
                {
                    "room_number": room.room_number,
                    "billing_month": reading.billing_month,
                    "water_value": float(reading.water_value),
                    "electric_value": float(reading.electric_value),
                }
            )
        df = pd.DataFrame(data)
        return self._to_xlsx(df, sheet_name="Meter Readings")
