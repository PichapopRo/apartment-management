from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from model.receipt import Receipt
from repository.bill_repository import BillRepository
from repository.receipt_repository import ReceiptRepository
from repository.room_repository import RoomRepository

FONT_REGISTERED = False
FONT_NAME = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


def _register_fonts() -> None:
    global FONT_REGISTERED, FONT_NAME, FONT_BOLD
    if FONT_REGISTERED:
        return
    regular = Path("C:/Windows/Fonts/tahoma.ttf")
    bold = Path("C:/Windows/Fonts/tahomabd.ttf")
    if regular.exists():
        pdfmetrics.registerFont(TTFont("Tahoma", str(regular)))
        FONT_NAME = "Tahoma"
    if bold.exists():
        pdfmetrics.registerFont(TTFont("TahomaBold", str(bold)))
        FONT_BOLD = "TahomaBold"
    FONT_REGISTERED = True


def _amount_to_words_en(amount: Decimal) -> str:
    """
    Simple English money-to-words converter for THB.
    Enough for receipts (up to millions). No external deps.
    Example: 2439.00 -> 'Two Thousand Four Hundred Thirty-Nine Baht Only'
    """
    n = int(amount)
    frac = int((amount - Decimal(n)) * 100)

    ones = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = [
        "Ten",
        "Eleven",
        "Twelve",
        "Thirteen",
        "Fourteen",
        "Fifteen",
        "Sixteen",
        "Seventeen",
        "Eighteen",
        "Nineteen",
    ]
    tens = [
        "",
        "",
        "Twenty",
        "Thirty",
        "Forty",
        "Fifty",
        "Sixty",
        "Seventy",
        "Eighty",
        "Ninety",
    ]

    def words_under_1000(x: int) -> str:
        parts = []
        h = x // 100
        r = x % 100
        if h:
            parts.append(ones[h] + " Hundred")
        if r:
            if r < 10:
                parts.append(ones[r])
            elif r < 20:
                parts.append(teens[r - 10])
            else:
                t = r // 10
                o = r % 10
                if o:
                    parts.append(f"{tens[t]}-{ones[o]}")
                else:
                    parts.append(tens[t])
        return " ".join(parts) if parts else "Zero"

    def words(x: int) -> str:
        if x == 0:
            return "Zero"
        parts = []
        millions = x // 1_000_000
        x %= 1_000_000
        thousands = x // 1_000
        x %= 1_000
        if millions:
            parts.append(words_under_1000(millions) + " Million")
        if thousands:
            parts.append(words_under_1000(thousands) + " Thousand")
        if x:
            parts.append(words_under_1000(x))
        return " ".join(parts)

    baht_words = words(n)
    if frac > 0:
        satang_words = words(frac)
        return f"{baht_words} Baht and {satang_words} Satang Only"
    return f"{baht_words} Baht Only"


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

    def _draw_receipt(
        self,
        c: canvas.Canvas,
        receipt,
        bill,
        y_top: float,
        is_copy: bool
    ) -> None:
        # ===== Page constants =====
        width, _ = A4
        left = 10 * mm
        right = 10 * mm
        usable_w = width - left - right
        row_h = 6 * mm

        # ===== Helpers =====
        def set_font(name: str, size: int):
            c.setFont(name, size)

        def text_left(x: float, y: float, text: str, size: int = 10, bold: bool = False):
            set_font(FONT_BOLD if bold else FONT_NAME, size)
            c.drawString(x, y, text)

        def text_right(x: float, y: float, text: str, size: int = 10, bold: bool = False):
            set_font(FONT_BOLD if bold else FONT_NAME, size)
            c.drawRightString(x, y, text)

        def text_center(x: float, y: float, text: str, size: int = 10, bold: bool = False):
            set_font(FONT_BOLD if bold else FONT_NAME, size)
            c.drawCentredString(x, y, text)

        def y(row: int) -> float:
            return y_top - row * row_h

        # ===== Header data =====
        room = self.rooms.get_by_id(bill.room_id)
        room_number = getattr(room, "room_number", None) or str(bill.room_id)

        issued_at = receipt.issued_at or datetime.now()
        date_text = issued_at.strftime("%d %B %Y")

        bill_year, bill_month = bill.billing_month.split("-")
        bill_month_name = datetime(int(bill_year), int(bill_month), 1).strftime("%B")

        total_amount = Decimal(bill.total_amount or 0)
        amount_words = _amount_to_words_en(total_amount)

        # Payment method text
        payment_method = "Cash"

        # ===== Title block =====
        text_left(left, y(0), "MK HOUSE", 14, bold=True)
        title = "RECEIPT VOUCHER - COPY" if is_copy else "RECEIPT VOUCHER"
        text_center(left + usable_w / 2, y(1), title, 12, bold=True)

        label_x = left + usable_w * 0.62
        value_x = left + usable_w

        text_left(label_x, y(3), "Room:", 10)
        text_right(value_x, y(3), room_number, 10)

        text_left(label_x, y(4), "Date:", 10)
        text_right(value_x, y(4), date_text, 10)

        # ===== Received from / Payment / Amount =====
        text_left(left, y(3), "Received from:", 10)
        text_left(left + 30 * mm, y(3), f"Room {room_number}", 10)

        text_left(left, y(4), "Payment method:", 10)
        text_left(left + 30 * mm, y(4), payment_method, 10)

        text_left(left, y(5), "Amount in words:", 10)
        text_left(left + 30 * mm, y(5), amount_words, 10)

        text_left(left, y(6), "Amount (THB):", 10)
        text_left(left + 30 * mm, y(6), f"{total_amount:,.2f}", 10)

        # ===== Table (fixed columns) =====
        # Columns: Qty | Description | Unit Price | Amount
        table_top_row = 8
        table_rows = 6
        table_top = y(table_top_row) + row_h * 0.6
        table_bottom = y(table_top_row + table_rows) - row_h * 0.2

        qty_w = usable_w * 0.12
        desc_w = usable_w * 0.55
        unit_w = usable_w * 0.16
        amt_w = usable_w * 0.17

        x_qty = left
        x_desc = x_qty + qty_w
        x_unit = x_desc + desc_w
        x_amt = x_unit + unit_w
        x_end = left + usable_w

        c.rect(left, table_bottom, usable_w, table_top - table_bottom, stroke=1, fill=0)
        c.line(x_desc, table_bottom, x_desc, table_top)
        c.line(x_unit, table_bottom, x_unit, table_top)
        c.line(x_amt, table_bottom, x_amt, table_top)

        header_y = y(table_top_row)
        c.line(left, header_y - row_h * 0.45, x_end, header_y - row_h * 0.45)

        pad = 2 * mm
        text_left(x_qty + pad, header_y, "Qty", 10, bold=True)
        text_left(x_desc + pad, header_y, "Description", 10, bold=True)
        text_right(x_unit + unit_w - pad, header_y, "Unit Price", 10, bold=True)
        text_right(x_amt + amt_w - pad, header_y, "Amount", 10, bold=True)

        # Add items
        items = []
        # Rent
        items.append((
            Decimal("1"),
            f"Room rent for {bill_month_name} {bill_year}",
            Decimal(bill.rent_amount or 0),
            Decimal(bill.rent_amount or 0),
        ))
        # Water
        if bill.water_amount and Decimal(bill.water_amount) > 0:
            wu = Decimal(bill.water_units or 0)
            wa = Decimal(bill.water_amount or 0)
            if wu > 0:
                unit_price = wa / wu
                items.append((wu, "Water", unit_price, wa))
            else:
                items.append((Decimal("1"), "Water", wa, wa))
        # Electric
        if bill.electric_amount and Decimal(bill.electric_amount) > 0:
            eu = Decimal(bill.electric_units or 0)
            ea = Decimal(bill.electric_amount or 0)
            unit_price = (ea / eu) if eu else Decimal("0.00")
            items.append((eu, "Electricity", unit_price, ea))
        # Garbage/Common
        if bill.garbage_fee and Decimal(bill.garbage_fee) > 0:
            gf = Decimal(bill.garbage_fee)
            items.append((Decimal("1"), "Common area / Garbage fee", gf, gf))
        # Late fee
        if bill.late_fee and Decimal(bill.late_fee) > 0:
            lf = Decimal(bill.late_fee)
            items.append((Decimal("1"), "Late payment fee", lf, lf))

        max_item_rows = 4
        start_row = table_top_row + 1
        for idx, (qty, desc, unit_price, amt) in enumerate(items[:max_item_rows]):
            ry = y(start_row + idx)
            text_left(x_qty + pad, ry, f"{qty}", 10)
            text_left(x_desc + pad, ry, desc, 10)
            text_right(x_unit + unit_w - pad, ry, f"{unit_price:,.2f}", 10)
            text_right(x_amt + amt_w - pad, ry, f"{amt:,.2f}", 10)

        # Total line
        total_y = y(table_top_row + table_rows)
        text_left(x_desc + pad, total_y, "TOTAL", 10, bold=True)
        text_right(x_amt + amt_w - pad, total_y, f"{total_amount:,.2f}", 10, bold=True)

        # ===== Payment terms (English version of sample text) =====
        terms_y = y(table_top_row + table_rows + 2)

        terms = [
            "Please pay the room rent by the 5th of each month.",
            "After the 5th, a late fee of THB 50 per day may apply.",
            "Bank transfer: Siam Commercial Bank (SCB) | Account Name: Malinee Kaewkam (example) | Account No.: 033-268283-7",
            "If payment is not received by the 15th, the landlord may lock the room immediately."
        ]
        set_font(FONT_NAME, 9)
        for i, line in enumerate(terms):
            c.drawString(left, terms_y - i * (4.2 * mm), line)

        # ===== Signature area =====
        sig_y_label = terms_y - len(terms) * (4.2 * mm) - 6 * mm
        text_left(left, sig_y_label, "Prepared by", 10)
        text_left(left + usable_w * 0.35, sig_y_label, "Checked by", 10)
        text_left(left + usable_w * 0.70, sig_y_label, "Received by", 10)

        line_y = sig_y_label - 7 * mm
        c.line(left + 5 * mm, line_y, left + usable_w * 0.25, line_y)
        c.line(left + usable_w * 0.35, line_y, left + usable_w * 0.60, line_y)
        c.line(left + usable_w * 0.70, line_y, left + usable_w * 0.95, line_y)

    def render_pdf(self, receipt_id: int) -> bytes:
        _register_fonts()
        receipt = self.receipts.get_by_id(receipt_id)
        if receipt is None:
            raise ValueError("Receipt not found")
        bill = self.bills.get_by_id(receipt.bill_id)
        if bill is None:
            raise ValueError("Bill not found")

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        page_height = A4[1]
        top_y = page_height - 18 * mm
        self._draw_receipt(c, receipt, bill, top_y, False)
        c.setDash(2, 2)
        cut_y = page_height / 2 - 6 * mm
        c.line(10 * mm, cut_y, A4[0] - 10 * mm, cut_y)
        c.setDash()
        c.drawString(10 * mm, cut_y - 4 * mm, "-")
        c.drawRightString(A4[0] - 10 * mm, cut_y - 4 * mm, "Cut line")
        copy_top = page_height / 2 - 12 * mm
        self._draw_receipt(c, receipt, bill, copy_top, True)
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.read()

    def render_bulk_pdf(self, bill_ids: list[int]) -> bytes:
        _register_fonts()
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        for bill_id in bill_ids:
            receipt = self.receipts.get_by_bill_id(bill_id)
            if receipt is None:
                receipt = self.issue_receipt(bill_id)
            bill = self.bills.get_by_id(bill_id)
            if bill is None:
                continue
            page_height = A4[1]
            top_y = page_height - 18 * mm
            self._draw_receipt(c, receipt, bill, top_y, False)
            c.setDash(2, 2)
            cut_y = page_height / 2 - 6 * mm
            c.line(10 * mm, cut_y, A4[0] - 10 * mm, cut_y)
            c.setDash()
            c.drawString(10 * mm, cut_y - 4 * mm, "-")
            c.drawRightString(A4[0] - 10 * mm, cut_y - 4 * mm, "Cut line")
            copy_top = page_height / 2 - 12 * mm
            self._draw_receipt(c, receipt, bill, copy_top, True)
            c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.read()
