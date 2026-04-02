from sqlalchemy.orm import Session

from model.billing_config import BillingConfig


class BillingConfigRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_config(self) -> BillingConfig:
        config = self.db.query(BillingConfig).first()
        if config is None:
            config = BillingConfig()
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
        return config

    def update(self, config: BillingConfig) -> BillingConfig:
        self.db.commit()
        self.db.refresh(config)
        return config
