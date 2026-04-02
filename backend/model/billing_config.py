from sqlalchemy import Column, DateTime, Integer, Numeric, func

from database import Base


class BillingConfig(Base):
    __tablename__ = "billing_config"

    id = Column(Integer, primary_key=True, index=True)
    water_rate = Column(Numeric(10, 2), nullable=False, default=0)
    electric_rate = Column(Numeric(10, 2), nullable=False, default=0)
    garbage_fee = Column(Numeric(10, 2), nullable=False, default=30)
    late_fee = Column(Numeric(10, 2), nullable=False, default=300)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
