from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def log_action(
    db: AsyncSession,
    box_id: int | None,
    action: str,
    details: dict,
) -> AuditLog:
    entry = AuditLog(box_id=box_id, action=action, details=details)
    db.add(entry)
    await db.flush()
    return entry
