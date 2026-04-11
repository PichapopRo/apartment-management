import argparse
import re
import sys
from decimal import Decimal
from pathlib import Path
from typing import Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database import SessionLocal  # noqa: E402
from model.meter_reading import MeterReading  # noqa: E402
from model.room import Room, RoomStatus  # noqa: E402
from repository.meter_reading_repository import MeterReadingRepository  # noqa: E402
from repository.bill_repository import BillRepository  # noqa: E402
from model.bill import Bill  # noqa: E402
from repository.room_repository import RoomRepository  # noqa: E402


MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def parse_sheet_month(sheet: str) -> Optional[str]:
    name = sheet.strip().lower()
    if name in {"water", "electric"}:
        return None

    name = name.replace("_", " ")
    name = re.sub(r"\s+", " ", name)

    match = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*'?(\d{2})", name)
    if not match:
        return None

    month = MONTHS[match.group(1)]
    year = int(match.group(2))
    year += 2000 if year < 70 else 1900
    return f"{year:04d}-{month:02d}"


def extract_rates(cell: str) -> Optional[Decimal]:
    if not isinstance(cell, str):
        return None
    match = re.search(r"@\s*([0-9.]+)", cell)
    if match:
        return Decimal(match.group(1))
    return None


def find_header_rows(df: pd.DataFrame) -> Optional[int]:
    for i in range(min(6, len(df))):
        row = df.iloc[i]
        if any(str(cell).strip().lower() == "room" for cell in row.tolist()):
            return i
    return None


def get_col(df: pd.DataFrame, row_idx: int, col_idx: int) -> str:
    try:
        return str(df.iat[row_idx, col_idx]).strip()
    except Exception:
        return ""


def parse_month_sheet(df: pd.DataFrame):
    header_row = find_header_rows(df)
    if header_row is None:
        return None

    row1 = df.iloc[header_row]
    row2 = df.iloc[header_row + 1] if header_row + 1 < len(df) else None
    if row2 is None:
        return None

    water_rate = None
    electric_rate = None
    water_start_col = None
    water_end_col = None
    electric_start_col = None
    electric_end_col = None
    total_col = None
    total_cols: list[int] = []
    garbage_col = None

    for col_idx, cell in enumerate(row1.tolist()):
        text = str(cell).lower()
        if "water" in text and water_start_col is None:
            water_rate = extract_rates(str(cell))
            water_start_col = col_idx
            water_end_col = col_idx + 1
        if "electric" in text and electric_start_col is None:
            electric_rate = extract_rates(str(cell))
            electric_start_col = col_idx
            electric_end_col = col_idx + 1
        if "total" in text and total_col is None:
            total_cols.append(col_idx)
        if "garbage" in text and garbage_col is None:
            garbage_col = col_idx

    if total_cols:
        if garbage_col is not None:
            after_garbage = [col for col in total_cols if col > garbage_col]
            total_col = after_garbage[0] if after_garbage else total_cols[-1]
        else:
            total_col = total_cols[-1]

    data_start = header_row + 2

    return {
        "data_start": data_start,
        "water_rate": water_rate,
        "electric_rate": electric_rate,
        "water_start_col": water_start_col,
        "water_end_col": water_end_col,
        "electric_start_col": electric_start_col,
        "electric_end_col": electric_end_col,
        "total_col": total_col,
    }


def safe_decimal(value) -> Optional[Decimal]:
    try:
        if pd.isna(value):
            return None
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="Migrate monthly meter readings from XLS.")
    parser.add_argument("--file", required=True, help="Path to XLS file")
    parser.add_argument("--apply", action="store_true", help="Write to database")
    parser.add_argument(
        "--create-rooms",
        action="store_true",
        help="Create rooms if missing (rent_rate=0, status=vacant)",
    )
    parser.add_argument(
        "--room-range",
        default="1-18",
        help="Room number range to import (default: 1-18)",
    )
    parser.add_argument(
        "--rent-sheet",
        default="Mar 26",
        help="Sheet name to load rent prices from (default: Mar 26)",
    )
    parser.add_argument(
        "--import-total",
        action="store_true",
        help="Import column L (Total) into bills table",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    xls = pd.ExcelFile(path)

    total_readings = 0
    sheets_used = 0
    rate_report = {}

    room_range = args.room_range.split("-")
    min_room = int(room_range[0])
    max_room = int(room_range[1]) if len(room_range) > 1 else min_room
    allowed_rooms = {f"{i:03d}" for i in range(min_room, max_room + 1)}

    db = SessionLocal()
    room_repo = RoomRepository(db)
    reading_repo = MeterReadingRepository(db)
    bill_repo = BillRepository(db)

    try:
        if args.create_rooms:
            for room_number in sorted(allowed_rooms):
                if room_repo.get_by_number(room_number) is None:
                    room_repo.create(
                        Room(
                            room_number=room_number,
                            rent_rate=Decimal("0.00"),
                            status=RoomStatus.VACANT.value,
                        )
                    )

        # update rent_rate from specified sheet (column J = index 9)
        if args.rent_sheet in xls.sheet_names:
            df_rent = pd.read_excel(xls, sheet_name=args.rent_sheet, header=None)
            header_row = find_header_rows(df_rent)
            if header_row is not None:
                data_start = header_row + 2
                for i in range(data_start, len(df_rent)):
                    row = df_rent.iloc[i]
                    room_val = row.iloc[0] if len(row) > 0 else None
                    if pd.isna(room_val):
                        continue
                    try:
                        room_int = int(str(room_val).strip())
                    except Exception:
                        continue
                    room_number = f"{room_int:03d}"
                    if room_number not in allowed_rooms:
                        continue
                    rent_val = row.iloc[9] if len(row) > 9 else None
                    rent_amount = safe_decimal(rent_val)
                    if rent_amount is None:
                        continue
                    room = room_repo.get_by_number(room_number)
                    if room is None:
                        continue
                    room.rent_rate = rent_amount
                db.commit()

        for sheet in xls.sheet_names:
            billing_month = parse_sheet_month(sheet)
            if not billing_month:
                continue

            df = pd.read_excel(xls, sheet_name=sheet, header=None)
            meta = parse_month_sheet(df)
            if not meta:
                continue

            sheets_used += 1
            if meta["water_rate"] or meta["electric_rate"]:
                rate_report[billing_month] = {
                    "water_rate": meta["water_rate"],
                    "electric_rate": meta["electric_rate"],
                }

            for i in range(meta["data_start"], len(df)):
                row = df.iloc[i]
                room_val = row.iloc[0] if len(row) > 0 else None
                if pd.isna(room_val):
                    continue

                try:
                    room_int = int(str(room_val).strip())
                except Exception:
                    continue

                room_number = f"{room_int:03d}"
                if room_number not in allowed_rooms:
                    continue

                water_end = None
                if meta["water_end_col"] is not None and meta["water_end_col"] < len(row):
                    water_end = safe_decimal(row.iloc[meta["water_end_col"]])
                if water_end is None and meta["water_start_col"] is not None:
                    water_end = safe_decimal(row.iloc[meta["water_start_col"]])

                electric_end = None
                if meta["electric_end_col"] is not None and meta["electric_end_col"] < len(row):
                    electric_end = safe_decimal(row.iloc[meta["electric_end_col"]])
                if electric_end is None and meta["electric_start_col"] is not None:
                    electric_end = safe_decimal(row.iloc[meta["electric_start_col"]])

                if water_end is None and electric_end is None:
                    continue

                if args.apply:
                    room = room_repo.get_by_number(room_number)
                    if room is None:
                        continue

                    if reading_repo.get_by_room_month(room.id, billing_month):
                        continue

                    reading = MeterReading(
                        room_id=room.id,
                        billing_month=billing_month,
                        water_value=water_end or Decimal("0.00"),
                        electric_value=electric_end or Decimal("0.00"),
                    )
                    reading_repo.create(reading)

                    if args.import_total:
                        total_col = meta.get("total_col")
                        if total_col is None:
                            total_col = 11
                        total_val = row.iloc[total_col] if total_col < len(row) else None
                        total_amount = safe_decimal(total_val)
                        if total_amount is not None:
                            existing_bill = bill_repo.get_by_room_month(room.id, billing_month)
                            if existing_bill is None:
                                bill = Bill(
                                    room_id=room.id,
                                    billing_month=billing_month,
                                    rent_amount=Decimal("0.00"),
                                    water_units=Decimal("0.00"),
                                    water_amount=Decimal("0.00"),
                                    electric_units=Decimal("0.00"),
                                    electric_amount=Decimal("0.00"),
                                    garbage_fee=Decimal("0.00"),
                                    late_fee=Decimal("0.00"),
                                    late_fee_applied=False,
                                    total_amount=total_amount,
                                    status="UNPAID",
                                )
                                bill_repo.create(bill)
                            else:
                                if existing_bill.total_amount is None or existing_bill.total_amount == Decimal("0.00"):
                                    existing_bill.total_amount = total_amount

                total_readings += 1
    finally:
        db.close()

    print(f"Sheets processed: {sheets_used}")
    print(f"Readings parsed: {total_readings}")
    if rate_report:
        print("Detected rate changes (from sheet headers):")
        for month, rates in sorted(rate_report.items()):
            print(f"  {month}: water={rates['water_rate']} electric={rates['electric_rate']}")
    else:
        print("No rate info found in headers.")

    if not args.apply:
        print("Dry run only. Use --apply to write to DB.")


if __name__ == "__main__":
    main()
