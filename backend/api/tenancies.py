from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.schemas.tenancy import TenancyAssign, TenancyMoveOut, TenancyOut, TenancyUpdate
from model.user import UserRole
from services.tenancy_service import TenancyService
from utils.deps import get_db, require_roles

router = APIRouter(prefix="/tenancies", tags=["tenancies"])


@router.post(
    "/assign",
    response_model=TenancyOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def assign_tenancy(payload: TenancyAssign, db: Session = Depends(get_db)):
    service = TenancyService(db)
    tenancy = service.assign_resident(
        room_id=payload.room_id,
        resident_user_id=payload.resident_user_id,
        resident_name=payload.resident_name,
        tenant_phone=payload.tenant_phone,
        move_in=payload.move_in_date,
    )

    resident_name = tenancy.resident_name or (tenancy.resident.full_name if tenancy.resident else None)
    return TenancyOut(
        id=tenancy.id,
        room_id=tenancy.room_id,
        resident_user_id=tenancy.resident_user_id,
        resident_name=resident_name,
        tenant_phone=tenancy.tenant_phone,
        move_in_date=tenancy.move_in_date,
        move_out_date=tenancy.move_out_date,
        is_active=tenancy.is_active,
    )


@router.post(
    "/{tenancy_id}/move-out",
    response_model=TenancyOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def move_out(tenancy_id: int, payload: TenancyMoveOut, db: Session = Depends(get_db)):
    service = TenancyService(db)
    tenancy = service.move_out(tenancy_id=tenancy_id, move_out=payload.move_out_date)

    resident_name = tenancy.resident_name or (tenancy.resident.full_name if tenancy.resident else None)
    return TenancyOut(
        id=tenancy.id,
        room_id=tenancy.room_id,
        resident_user_id=tenancy.resident_user_id,
        resident_name=resident_name,
        tenant_phone=tenancy.tenant_phone,
        move_in_date=tenancy.move_in_date,
        move_out_date=tenancy.move_out_date,
        is_active=tenancy.is_active,
    )


@router.patch(
    "/room/{room_id}",
    response_model=TenancyOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def update_tenant(room_id: int, payload: TenancyUpdate, db: Session = Depends(get_db)):
    service = TenancyService(db)
    tenancy = service.update_active_tenancy(
        room_id=room_id,
        resident_name=payload.resident_name,
        tenant_phone=payload.tenant_phone,
    )

    resident_name = tenancy.resident_name or (tenancy.resident.full_name if tenancy.resident else None)
    return TenancyOut(
        id=tenancy.id,
        room_id=tenancy.room_id,
        resident_user_id=tenancy.resident_user_id,
        resident_name=resident_name,
        tenant_phone=tenancy.tenant_phone,
        move_in_date=tenancy.move_in_date,
        move_out_date=tenancy.move_out_date,
        is_active=tenancy.is_active,
    )
