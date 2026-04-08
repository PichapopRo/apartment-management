from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ReceiptIssue(BaseModel):
    bill_id: int


class ReceiptVoid(BaseModel):
    reason: str


class ReceiptOut(BaseModel):
    id: int
    bill_id: int
    receipt_number: str
    issued_at: datetime
    status: str
    voided_at: datetime | None = None
    void_reason: str | None = None
    model_config = ConfigDict(from_attributes=True)


class ReceiptBulkPdf(BaseModel):
    bill_ids: list[int]
