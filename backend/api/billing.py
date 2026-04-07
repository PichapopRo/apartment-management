from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.schemas.billing import (
    BillCreate,
    BillBulkCreate,
    BillBulkResult,
    BillOut,
    BillUpdate,
    BillingConfigOut,
    BillingConfigUpdate,
    MeterReadingCreate,
    MeterReadingOut,
)
from model.meter_reading import MeterReading
from model.user import UserRole
from repository.meter_reading_repository import MeterReadingRepository
from services.billing_service import BillingService
from repository.bill_repository import BillRepository
from repository.billing_config_repository import BillingConfigRepository
from utils.deps import get_db, require_roles

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post(
    "/readings",
    response_model=MeterReadingCreate,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def create_reading(payload: MeterReadingCreate, db: Session = Depends(get_db)):
    repo = MeterReadingRepository(db)
    if repo.get_by_room_month(payload.room_id, payload.billing_month):
        raise HTTPException(status_code=400, detail="Reading already exists for this month")

    reading = MeterReading(
        room_id=payload.room_id,
        billing_month=payload.billing_month,
        water_value=payload.water_value,
        electric_value=payload.electric_value,
    )
    repo.create(reading)
    return payload


@router.get(
    "/readings",
    response_model=list[MeterReadingOut],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def list_readings(room_id: int, limit: int = 6, db: Session = Depends(get_db)):
    repo = MeterReadingRepository(db)
    return repo.list_by_room(room_id=room_id, limit=limit)


@router.get(
    "/readings/year",
    response_model=list[MeterReadingOut],
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def list_readings_by_year(room_id: int, year: int, db: Session = Depends(get_db)):
    repo = MeterReadingRepository(db)
    return repo.list_by_year(room_id=room_id, year=str(year))


@router.post(
    "/bills",
    response_model=BillOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def create_bill(payload: BillCreate, db: Session = Depends(get_db)):
    service = BillingService(db)
    try:
        bill = service.create_bill_for_month(
            room_id=payload.room_id,
            billing_month=payload.billing_month,
            late_fee_applied=payload.late_fee_applied,
            water_units_override=payload.water_units_override,
            electric_units_override=payload.electric_units_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return bill


@router.post(
    "/bills/bulk",
    response_model=BillBulkResult,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def create_bills_bulk(payload: BillBulkCreate, db: Session = Depends(get_db)):
    service = BillingService(db)
    created: list[BillOut] = []
    skipped: list[dict] = []
    for item in payload.items:
        try:
            bill = service.create_bill_for_month(
                room_id=item.room_id,
                billing_month=item.billing_month,
                late_fee_applied=item.late_fee_applied,
                water_units_override=item.water_units_override,
                electric_units_override=item.electric_units_override,
            )
            created.append(bill)
        except ValueError as exc:
            skipped.append(
                {
                    "room_id": item.room_id,
                    "billing_month": item.billing_month,
                    "reason": str(exc),
                }
            )
    return {"created": created, "skipped": skipped}


@router.patch(
    "/bills/{bill_id}",
    response_model=BillOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def update_bill(bill_id: int, payload: BillUpdate, db: Session = Depends(get_db)):
    repo = BillRepository(db)
    bill = repo.get_by_id(bill_id)
    if bill is None:
        raise HTTPException(status_code=404, detail="Bill not found")

    bill.is_paid = payload.is_paid
    bill.paid_at = payload.paid_at
    bill.remark = payload.remark
    if bill.is_paid:
        bill.status = "PAID"
    elif bill.status == "PAID":
        bill.status = "UNPAID"
    return repo.update(bill)


@router.get(
    "/bills",
    response_model=list[BillOut],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def list_bills(month: str, room_id: int | None = None, db: Session = Depends(get_db)):
    repo = BillRepository(db)
    return repo.list_by_month(billing_month=month, room_id=room_id)


@router.get(
    "/config",
    response_model=BillingConfigOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def get_config(db: Session = Depends(get_db)):
    config = BillingConfigRepository(db).get_config()
    return config


@router.put(
    "/config",
    response_model=BillingConfigOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def update_config(payload: BillingConfigUpdate, db: Session = Depends(get_db)):
    repo = BillingConfigRepository(db)
    config = repo.get_config()
    config.water_rate = payload.water_rate
    config.electric_rate = payload.electric_rate
    config.garbage_fee = payload.garbage_fee
    config.late_fee = payload.late_fee
    return repo.update(config)
