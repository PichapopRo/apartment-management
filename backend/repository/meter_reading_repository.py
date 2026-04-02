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
