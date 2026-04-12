from decimal import Decimal

from model.meter_reading import MeterReading
from repository.meter_reading_repository import MeterReadingRepository


class MeterReadingService:
    def __init__(self, repo: MeterReadingRepository) -> None:
        self.repo = repo

    def create_reading(self, reading: MeterReading) -> MeterReading:
        if self.repo.get_by_room_month(reading.room_id, reading.billing_month):
            raise ValueError("Reading already exists for this month")

        previous = self.repo.get_previous_by_month(reading.room_id, reading.billing_month)
        if previous:
            if Decimal(reading.water_value) <= Decimal(previous.water_value):
                raise ValueError("Water value must be greater than previous month")
            if Decimal(reading.electric_value) <= Decimal(previous.electric_value):
                raise ValueError("Electric value must be greater than previous month")

        return self.repo.create(reading)
