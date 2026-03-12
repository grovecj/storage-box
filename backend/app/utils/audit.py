from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.box import StorageBox


async def log_action(
    db: AsyncSession,
    box_id: int | None,
    action: str,
    details: dict,
    box_code: str | None = None,
) -> AuditLog:
    # Always include box_code so audit entries remain meaningful after box deletion.
    # Prefer using a caller-provided box_code to avoid an extra SELECT when possible.
    if "box_code" not in details:
        if box_code is not None:
            details = {"box_code": box_code, **details}
        elif box_id is not None:
            result = await db.execute(
                select(StorageBox.box_code).where(StorageBox.id == box_id)
            )
            fetched_box_code = result.scalar_one_or_none()
            if fetched_box_code:
                details = {"box_code": fetched_box_code, **details}

    entry = AuditLog(box_id=box_id, action=action, details=details)
    db.add(entry)
    await db.flush()
    return entry
