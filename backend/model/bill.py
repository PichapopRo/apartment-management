from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func

from database import Base


class Bill(Base):
    __tablename__ = "bills"
    __table_args__ = (UniqueConstraint("room_id", "billing_month", name="uq_bill_room_month"),)

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    billing_month = Column(String(7), nullable=False)  # YYYY-MM

    rent_amount = Column(Numeric(12, 2), nullable=False, default=0)
    water_units = Column(Numeric(12, 2), nullable=False, default=0)
    water_amount = Column(Numeric(12, 2), nullable=False, default=0)
    electric_units = Column(Numeric(12, 2), nullable=False, default=0)
    electric_amount = Column(Numeric(12, 2), nullable=False, default=0)
    garbage_fee = Column(Numeric(12, 2), nullable=False, default=30)
    late_fee = Column(Numeric(12, 2), nullable=False, default=0)
    late_fee_applied = Column(Boolean, nullable=False, default=False)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)

    status = Column(String(20), nullable=False, default="UNPAID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
