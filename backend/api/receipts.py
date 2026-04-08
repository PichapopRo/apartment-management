from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from api.schemas.receipt import ReceiptBulkPdf, ReceiptIssue, ReceiptOut, ReceiptVoid
from model.user import UserRole
from repository.receipt_repository import ReceiptRepository
from services.receipt_service import ReceiptService
from utils.deps import get_db, require_roles

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.post(
    "/issue",
    response_model=ReceiptOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def issue_receipt(payload: ReceiptIssue, db: Session = Depends(get_db)):
    service = ReceiptService(db)
    try:
        return service.issue_receipt(payload.bill_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/{receipt_id}/void",
    response_model=ReceiptOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def void_receipt(receipt_id: int, payload: ReceiptVoid, db: Session = Depends(get_db)):
    service = ReceiptService(db)
    try:
        return service.void_receipt(receipt_id, payload.reason)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/{receipt_id}",
    response_model=ReceiptOut,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def get_receipt(receipt_id: int, db: Session = Depends(get_db)):
    receipt = ReceiptRepository(db).get_by_id(receipt_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


@router.get(
    "/{receipt_id}/pdf",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def get_receipt_pdf(receipt_id: int, db: Session = Depends(get_db)):
    service = ReceiptService(db)
    try:
        pdf_bytes = service.render_pdf(receipt_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.post(
    "/bulk/pdf",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.STAFF))],
)
def get_bulk_receipts_pdf(payload: ReceiptBulkPdf, db: Session = Depends(get_db)):
    service = ReceiptService(db)
    pdf_bytes = service.render_bulk_pdf(payload.bill_ids)
    return Response(content=pdf_bytes, media_type="application/pdf")
