from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.box import StorageBox


async def log_action(
    db: AsyncSession,
    box_id: int | None,
    action: str,
    details: dict,
) -> AuditLog:
    # Always include box_code so audit entries remain meaningful after box deletion
    if box_id is not None and "box_code" not in details:
        result = await db.execute(
            select(StorageBox.box_code).where(StorageBox.id == box_id)
        )
        box_code = result.scalar_one_or_none()
        if box_code:
            details = {"box_code": box_code, **details}

    entry = AuditLog(box_id=box_id, action=action, details=details)
    db.add(entry)
    await db.flush()
    return entry
