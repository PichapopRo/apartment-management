from sqlalchemy.orm import Session

from model.meter_reading import MeterReading


class MeterReadingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_room_month(self, room_id: int, billing_month: str) -> MeterReading | None:
        return (
            self.db.query(MeterReading)
            .filter(MeterReading.room_id == room_id, MeterReading.billing_month == billing_month)
            .first()
        )

    def create(self, reading: MeterReading) -> MeterReading:
        self.db.add(reading)
        self.db.commit()
        self.db.refresh(reading)
        return reading

    def list_by_room(self, room_id: int, limit: int = 6) -> list[MeterReading]:
        return (
            self.db.query(MeterReading)
            .filter(MeterReading.room_id == room_id)
            .order_by(MeterReading.billing_month.desc())
            .limit(limit)
            .all()
        )

    def list_by_year(self, room_id: int, year: str) -> list[MeterReading]:
        prefix = f"{year}-"
        return (
            self.db.query(MeterReading)
            .filter(MeterReading.room_id == room_id, MeterReading.billing_month.like(prefix + "%"))
            .order_by(MeterReading.billing_month.asc())
            .all()
        )

    def get_previous_by_month(self, room_id: int, billing_month: str) -> MeterReading | None:
        return (
            self.db.query(MeterReading)
            .filter(
                MeterReading.room_id == room_id,
                MeterReading.billing_month < billing_month,
            )
            .order_by(MeterReading.billing_month.desc())
            .first()
        )
