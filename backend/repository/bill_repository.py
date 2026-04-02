from sqlalchemy.orm import Session

from model.bill import Bill


class BillRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_room_month(self, room_id: int, billing_month: str) -> Bill | None:
        return (
            self.db.query(Bill)
            .filter(Bill.room_id == room_id, Bill.billing_month == billing_month)
            .first()
        )

    def create(self, bill: Bill) -> Bill:
        self.db.add(bill)
        self.db.commit()
        self.db.refresh(bill)
        return bill
