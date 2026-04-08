from datetime import datetime
from decimal import Decimal
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from model.bill import Bill
from model.receipt import Receipt
from repository.bill_repository import BillRepository
from repository.receipt_repository import ReceiptRepository
from repository.room_repository import RoomRepository


class ReceiptService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.bills = BillRepository(db)
        self.receipts = ReceiptRepository(db)
        self.rooms = RoomRepository(db)

    def _next_receipt_number(self) -> str:
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"RV{today}"
        last = self.receipts.get_last_for_date(prefix)
        if last is None:
            seq = 1
        else:
            try:
                seq = int(str(last.receipt_number).split("-")[-1]) + 1
            except Exception:
                seq = 1
        return f"{prefix}-{seq:04d}"

    def issue_receipt(self, bill_id: int) -> Receipt:
        bill = self.bills.get_by_id(bill_id)
        if bill is None:
            raise ValueError("Bill not found")

        existing = self.receipts.get_by_bill_id(bill_id)
        if existing and existing.status != "VOIDED":
            raise ValueError("Receipt already issued for this bill")

        receipt = Receipt(
            bill_id=bill_id,
            receipt_number=self._next_receipt_number(),
            status="ISSUED",
        )
        return self.receipts.create(receipt)

    def void_receipt(self, receipt_id: int, reason: str) -> Receipt:
        receipt = self.receipts.get_by_id(receipt_id)
        if receipt is None:
            raise ValueError("Receipt not found")
        if receipt.status == "VOIDED":
            return receipt
        receipt.status = "VOIDED"
        receipt.void_reason = reason
        receipt.voided_at = datetime.now()
        return self.receipts.update(receipt)

    def _draw_receipt(self, c: canvas.Canvas, receipt: Receipt, bill: Bill) -> None:
        room = self.rooms.get_by_id(bill.room_id)
        width, height = A4
        margin = 18 * mm
        y = height - margin

        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, y, "MK HOUSE")
        y -= 16
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "RECEIPT VOUCHER")
        y -= 20

        c.setFont("Helvetica", 11)
        c.drawString(margin, y, f"Receipt No: {receipt.receipt_number}")
        c.drawRightString(width - margin, y, f"Date: {receipt.issued_at.date().isoformat()}")
        y -= 16
        c.drawString(margin, y, f"Room: {room.room_number if room else bill.room_id}")
        y -= 20

        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "Qty")
        c.drawString(margin + 30 * mm, y, "Description")
        c.drawRightString(width - margin - 40 * mm, y, "Unit")
        c.drawRightString(width - margin, y, "Amount")
        y -= 12
        c.line(margin, y, width - margin, y)
        y -= 14

        def add_item(qty: Decimal, desc: str, unit_price: Decimal, amount: Decimal):
            nonlocal y
            c.setFont("Helvetica", 11)
            c.drawString(margin, y, f"{qty}")
            c.drawString(margin + 30 * mm, y, desc)
            c.drawRightString(width - margin - 40 * mm, y, f"{unit_price:.2f}")
            c.drawRightString(width - margin, y, f"{amount:.2f}")
            y -= 14

        billing_month = bill.billing_month
        add_item(Decimal("1"), f"Rent for {billing_month}", Decimal(bill.rent_amount), Decimal(bill.rent_amount))

        if bill.water_amount and bill.water_amount > 0:
            unit = (
                Decimal(bill.water_amount) / Decimal(bill.water_units)
                if bill.water_units
                else Decimal("0.00")
            )
            add_item(Decimal(bill.water_units), "Water", unit, Decimal(bill.water_amount))

        if bill.electric_amount and bill.electric_amount > 0:
            unit = (
                Decimal(bill.electric_amount) / Decimal(bill.electric_units)
                if bill.electric_units
                else Decimal("0.00")
            )
            add_item(Decimal(bill.electric_units), "Electric", unit, Decimal(bill.electric_amount))

        if bill.garbage_fee and bill.garbage_fee > 0:
            add_item(Decimal("1"), "Garbage fee", Decimal(bill.garbage_fee), Decimal(bill.garbage_fee))

        if bill.late_fee and bill.late_fee > 0:
            add_item(Decimal("1"), "Late fee", Decimal(bill.late_fee), Decimal(bill.late_fee))

        y -= 4
        c.line(margin, y, width - margin, y)
        y -= 16
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(width - margin, y, f"Total: {Decimal(bill.total_amount):.2f} THB")

        y -= 24
        c.setFont("Helvetica", 10)
        c.drawString(margin, y, "Payment received. Thank you.")

    def render_pdf(self, receipt_id: int) -> bytes:
        receipt = self.receipts.get_by_id(receipt_id)
        if receipt is None:
            raise ValueError("Receipt not found")
        bill = self.bills.get_by_id(receipt.bill_id)
        if bill is None:
            raise ValueError("Bill not found")

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        self._draw_receipt(c, receipt, bill)
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.read()

    def render_bulk_pdf(self, bill_ids: list[int]) -> bytes:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        for bill_id in bill_ids:
            receipt = self.receipts.get_by_bill_id(bill_id)
            if receipt is None:
                receipt = self.issue_receipt(bill_id)
            bill = self.bills.get_by_id(bill_id)
            if bill is None:
                continue
            self._draw_receipt(c, receipt, bill)
            c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.read()
