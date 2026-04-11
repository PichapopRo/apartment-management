from sqlalchemy import desc
from sqlalchemy.orm import Session

from model.receipt import Receipt


class ReceiptRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, receipt_id: int) -> Receipt | None:
        return self.db.query(Receipt).filter(Receipt.id == receipt_id).first()

    def get_by_bill_id(self, bill_id: int) -> Receipt | None:
        return self.db.query(Receipt).filter(Receipt.bill_id == bill_id).first()

    def get_last_for_date(self, date_prefix: str) -> Receipt | None:
        return (
            self.db.query(Receipt)
            .filter(Receipt.receipt_number.like(f"{date_prefix}-%"))
            .order_by(desc(Receipt.receipt_number))
            .first()
        )

    def create(self, receipt: Receipt) -> Receipt:
        self.db.add(receipt)
        self.db.commit()
        self.db.refresh(receipt)
        return receipt

    def update(self, receipt: Receipt) -> Receipt:
        self.db.commit()
        self.db.refresh(receipt)
        return receipt
