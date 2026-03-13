from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.report import ReportRequest
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("")
async def generate_report(
    data: ReportRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.format == "html":
        html = await report_service.generate_html_report(db, data, user)
        return HTMLResponse(content=html)
    elif data.format == "pdf":
        pdf_bytes = await report_service.generate_pdf_report(db, data, user)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=inventory-report.pdf"},
        )
    elif data.format == "csv":
        csv_content = await report_service.generate_csv_report(db, data, user)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=inventory-report.csv"},
        )
    elif data.format == "text":
        text_content = await report_service.generate_text_report(db, data, user)
        return Response(
            content=text_content,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=inventory-report.txt"},
        )
