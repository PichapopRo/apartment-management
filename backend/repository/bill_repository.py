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

    def get_by_id(self, bill_id: int) -> Bill | None:
        return self.db.query(Bill).filter(Bill.id == bill_id).first()

    def list_by_month(self, billing_month: str, room_id: int | None = None) -> list[Bill]:
        query = self.db.query(Bill).filter(Bill.billing_month == billing_month)
        if room_id is not None:
            query = query.filter(Bill.room_id == room_id)
        return query.order_by(Bill.room_id.asc()).all()

    def get_latest_for_room(self, room_id: int) -> Bill | None:
        return (
            self.db.query(Bill)
            .filter(Bill.room_id == room_id)
            .order_by(Bill.billing_month.desc())
            .first()
        )

    def create(self, bill: Bill) -> Bill:
        self.db.add(bill)
        self.db.commit()
        self.db.refresh(bill)
        return bill

    def update(self, bill: Bill) -> Bill:
        self.db.commit()
        self.db.refresh(bill)
        return bill
