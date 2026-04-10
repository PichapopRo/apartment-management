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


@router.get(
    "/bills/export-all",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def export_bills_all(db: Session = Depends(get_db)):
    service = ReportService(db)
    content = service.export_bills_all()
    filename = "bills-all.xlsx"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get(
    "/readings/export-all",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def export_readings_all(db: Session = Depends(get_db)):
    service = ReportService(db)
    content = service.export_readings_all()
    filename = "readings-all.xlsx"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get(
    "/export-all",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def export_all(db: Session = Depends(get_db)):
    service = ReportService(db)
    content = service.export_all()
    filename = "apartment-export.xlsx"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
