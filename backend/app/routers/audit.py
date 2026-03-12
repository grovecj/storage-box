from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit import AuditLog

router = APIRouter(prefix="/boxes/{box_id}/audit-log", tags=["audit"])


@router.get("")
async def get_audit_log(
    box_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.box_id == box_id)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.box_id == box_id)
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = result.scalars().all()

    return {
        "logs": [
            {
                "id": log.id,
                "action": log.action,
                "details": log.details,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
