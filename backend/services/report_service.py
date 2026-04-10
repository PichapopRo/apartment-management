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

    def export_bills_all(self) -> bytes:
        rows = (
            self.db.query(Bill, Room)
            .join(Room, Room.id == Bill.room_id)
            .order_by(Room.room_number.asc(), Bill.billing_month.asc())
            .all()
        )
        data = []
        for bill, room in rows:
            data.append(
                {
                    "room_number": room.room_number,
                    "billing_month": bill.billing_month,
                    "total_amount": float(bill.total_amount),
                }
            )
        df = pd.DataFrame(data)
        pivot = df.pivot_table(
            index="room_number",
            columns="billing_month",
            values="total_amount",
            aggfunc="first",
        ).reset_index()
        return self._to_xlsx(pivot, sheet_name="Bills")

    def export_readings_all(self) -> bytes:
        rows = (
            self.db.query(MeterReading, Room)
            .join(Room, Room.id == MeterReading.room_id)
            .order_by(MeterReading.billing_month.asc(), Room.room_number.asc())
            .all()
        )
        water_data = []
        electric_data = []
        for reading, room in rows:
            water_data.append(
                {
                    "room_number": room.room_number,
                    "billing_month": reading.billing_month,
                    "water_value": float(reading.water_value),
                }
            )
            electric_data.append(
                {
                    "room_number": room.room_number,
                    "billing_month": reading.billing_month,
                    "electric_value": float(reading.electric_value),
                }
            )
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            water_df = pd.DataFrame(water_data)
            water_pivot = water_df.pivot_table(
                index="room_number",
                columns="billing_month",
                values="water_value",
                aggfunc="first",
            ).reset_index()
            electric_df = pd.DataFrame(electric_data)
            electric_pivot = electric_df.pivot_table(
                index="room_number",
                columns="billing_month",
                values="electric_value",
                aggfunc="first",
            ).reset_index()
            water_pivot.to_excel(writer, index=False, sheet_name="Water")
            electric_pivot.to_excel(writer, index=False, sheet_name="Electric")
        output.seek(0)
        return output.read()

    def export_all(self) -> bytes:
        bills = self.db.query(Bill, Room).join(Room, Room.id == Bill.room_id).order_by(
            Bill.billing_month.asc(), Room.room_number.asc()
        )
        readings = self.db.query(MeterReading, Room).join(
            Room, Room.id == MeterReading.room_id
        ).order_by(MeterReading.billing_month.asc(), Room.room_number.asc())

        bills_data = []
        for bill, room in bills:
            bills_data.append(
                {
                    "room_number": room.room_number,
                    "billing_month": bill.billing_month,
                    "total_amount": float(bill.total_amount),
                }
            )

        water_data = []
        electric_data = []
        for reading, room in readings:
            water_data.append(
                {
                    "room_number": room.room_number,
                    "billing_month": reading.billing_month,
                    "water_value": float(reading.water_value),
                }
            )
            electric_data.append(
                {
                    "room_number": room.room_number,
                    "billing_month": reading.billing_month,
                    "electric_value": float(reading.electric_value),
                }
            )

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            bills_df = pd.DataFrame(bills_data)
            bills_pivot = bills_df.pivot_table(
                index="room_number",
                columns="billing_month",
                values="total_amount",
                aggfunc="first",
            ).reset_index()
            water_df = pd.DataFrame(water_data)
            water_pivot = water_df.pivot_table(
                index="room_number",
                columns="billing_month",
                values="water_value",
                aggfunc="first",
            ).reset_index()
            electric_df = pd.DataFrame(electric_data)
            electric_pivot = electric_df.pivot_table(
                index="room_number",
                columns="billing_month",
                values="electric_value",
                aggfunc="first",
            ).reset_index()
            bills_pivot.to_excel(writer, index=False, sheet_name="Bills")
            water_pivot.to_excel(writer, index=False, sheet_name="Water")
            electric_pivot.to_excel(writer, index=False, sheet_name="Electric")
        output.seek(0)
        return output.read()
