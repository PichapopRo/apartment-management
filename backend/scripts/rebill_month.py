import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.billing_service import BillingService
from database import SessionLocal
from model.bill import Bill
from model.receipt import Receipt
from model.meter_reading import MeterReading

TARGET_MONTH = "2026-03"


def main() -> None:
    db = SessionLocal()
    try:
        bill_ids = [
            b.id for b in db.query(Bill.id).filter(Bill.billing_month == TARGET_MONTH).all()
        ]
        if bill_ids:
            db.query(Receipt).filter(Receipt.bill_id.in_(bill_ids)).delete(synchronize_session=False)
        deleted = db.query(Bill).filter(Bill.billing_month == TARGET_MONTH).delete(synchronize_session=False)
        db.commit()

        service = BillingService(db)
        room_ids = [
            r.room_id
            for r in db.query(MeterReading.room_id)
            .filter(MeterReading.billing_month == TARGET_MONTH)
            .distinct()
        ]

        created = 0
        skipped = 0
        for room_id in room_ids:
            try:
                service.create_bill_for_month(
                    room_id=room_id,
                    billing_month=TARGET_MONTH,
                    late_fee_applied=False,
                    water_units_override=None,
                    electric_units_override=None,
                )
                created += 1
            except Exception:
                skipped += 1

        db.commit()
        print(f"Deleted {deleted} bills. Created {created} bills. Skipped {skipped}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
