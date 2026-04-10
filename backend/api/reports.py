from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from model.user import UserRole
from services.report_service import ReportService
from utils.deps import get_db, require_roles

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/bills/export",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def export_bills(month: str, db: Session = Depends(get_db)):
    if len(month) != 7 or month[4] != "-":
        raise HTTPException(status_code=400, detail="month must be YYYY-MM")
    service = ReportService(db)
    content = service.export_bills(month)
    filename = f"bills-{month}.xlsx"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get(
    "/readings/export",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def export_readings(month: str, db: Session = Depends(get_db)):
    if len(month) != 7 or month[4] != "-":
        raise HTTPException(status_code=400, detail="month must be YYYY-MM")
    service = ReportService(db)
    content = service.export_readings(month)
    filename = f"readings-{month}.xlsx"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
