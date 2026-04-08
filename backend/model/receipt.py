from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func

from database import Base


class Receipt(Base):
    __tablename__ = "receipts"
    __table_args__ = (UniqueConstraint("bill_id", name="uq_receipt_bill"),)

    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False, unique=True)
    receipt_number = Column(String(50), nullable=False, unique=True, index=True)
    issued_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(20), nullable=False, default="ISSUED")
    voided_at = Column(DateTime(timezone=True), nullable=True)
    void_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
