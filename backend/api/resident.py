from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.schemas.resident import ResidentBillOut, ResidentRoomOut, ResidentSummaryOut
from model.tenancy import Tenancy
from model.user import UserRole
from repository.bill_repository import BillRepository
from repository.room_repository import RoomRepository
from utils.deps import get_current_user, get_db, require_roles

router = APIRouter(prefix="/resident", tags=["resident"])


@router.get(
    "/summary",
    response_model=ResidentSummaryOut,
    dependencies=[Depends(require_roles(UserRole.RESIDENT))],
)
def resident_summary(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    tenancy = (
        db.query(Tenancy)
        .filter(Tenancy.resident_user_id == current_user.id, Tenancy.is_active == True)  # noqa: E712
        .first()
    )
    if tenancy is None:
        return ResidentSummaryOut(room=None, latest_bill=None)

    room = RoomRepository(db).get_by_id(tenancy.room_id)
    latest_bill = BillRepository(db).get_latest_for_room(tenancy.room_id)

    room_out = None
    if room:
        room_out = ResidentRoomOut(
            room_number=room.room_number,
            rent_rate=float(room.rent_rate or 0),
            status=room.status,
        )

    bill_out = None
    if latest_bill:
        bill_out = ResidentBillOut(
            billing_month=latest_bill.billing_month,
            total_amount=float(latest_bill.total_amount or 0),
            status=latest_bill.status,
            is_paid=bool(latest_bill.is_paid),
        )

    return ResidentSummaryOut(room=room_out, latest_bill=bill_out)
