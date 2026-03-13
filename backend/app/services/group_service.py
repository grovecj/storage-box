from geoalchemy2.functions import ST_X, ST_Y
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.box import StorageBox
from app.models.group import BoxGroup
from app.models.user import User
from app.schemas.group import GroupCreate, GroupListResponse, GroupResponse, GroupUpdate


def _make_point(lat: float, lng: float) -> str:
    return f"SRID=4326;POINT({lng} {lat})"


def _location_columns():
    """Return ST_Y (lat) and ST_X (lng) columns for the geography field."""
    geom = func.ST_GeomFromWKB(func.ST_AsBinary(BoxGroup.location))
    return (
        ST_Y(geom).label("lat"),
        ST_X(geom).label("lng"),
    )


def _group_to_response(
    group: BoxGroup,
    box_count: int = 0,
    lat: float | None = None,
    lng: float | None = None,
) -> GroupResponse:
    return GroupResponse(
        id=group.id,
        name=group.name,
        latitude=lat,
        longitude=lng,
        box_count=box_count,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


async def create_group(db: AsyncSession, data: GroupCreate, user: User) -> GroupResponse:
    location = None
    lat, lng = None, None
    if data.latitude is not None and data.longitude is not None:
        lat = data.latitude
        lng = data.longitude
        location = _make_point(lat, lng)

    group = BoxGroup(
        name=data.name,
        location=location,
        owner_id=user.id,
    )
    db.add(group)
    await db.flush()
    await db.refresh(group)
    await db.commit()

    return _group_to_response(group, box_count=0, lat=lat, lng=lng)


async def list_groups(db: AsyncSession, user: User) -> GroupListResponse:
    lat_col, lng_col = _location_columns()

    # Query groups with box counts
    result = await db.execute(
        select(
            BoxGroup,
            func.count(StorageBox.id).label("box_count"),
            lat_col,
            lng_col,
        )
        .outerjoin(StorageBox, StorageBox.group_id == BoxGroup.id)
        .where(BoxGroup.owner_id == user.id)
        .group_by(BoxGroup.id)
        .order_by(BoxGroup.name)
    )

    groups = []
    for row in result.all():
        group, box_count, lat, lng = row
        groups.append(_group_to_response(group, box_count=box_count, lat=lat, lng=lng))

    # Add "Ungrouped" virtual group with boxes that have no group_id
    ungrouped_result = await db.execute(
        select(func.count(StorageBox.id))
        .where(StorageBox.owner_id == user.id)
        .where(StorageBox.group_id.is_(None))
    )
    ungrouped_count = ungrouped_result.scalar() or 0

    if ungrouped_count > 0:
        # Add virtual "Ungrouped" entry
        from datetime import datetime
        ungrouped = GroupResponse(
            id=-1,
            name="Ungrouped",
            latitude=None,
            longitude=None,
            box_count=ungrouped_count,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        groups.append(ungrouped)

    return GroupListResponse(groups=groups)


async def get_group(db: AsyncSession, group_id: int, user: User) -> GroupResponse | None:
    lat_col, lng_col = _location_columns()
    result = await db.execute(
        select(
            BoxGroup,
            func.count(StorageBox.id).label("box_count"),
            lat_col,
            lng_col,
        )
        .outerjoin(StorageBox, StorageBox.group_id == BoxGroup.id)
        .where(BoxGroup.id == group_id)
        .where(BoxGroup.owner_id == user.id)
        .group_by(BoxGroup.id)
    )
    row = result.first()
    if not row or not row[0]:
        return None
    group, box_count, lat, lng = row
    return _group_to_response(group, box_count=box_count, lat=lat, lng=lng)


async def update_group(
    db: AsyncSession, group_id: int, data: GroupUpdate, user: User,
) -> GroupResponse | None:
    result = await db.execute(
        select(BoxGroup)
        .where(BoxGroup.id == group_id)
        .where(BoxGroup.owner_id == user.id)
    )
    group = result.scalar_one_or_none()
    if not group:
        return None

    if data.name is not None:
        group.name = data.name
    if data.latitude is not None and data.longitude is not None:
        group.location = _make_point(data.latitude, data.longitude)
    elif data.latitude is None and data.longitude is None:
        # Both set to None explicitly, clear location
        group.location = None

    await db.flush()
    await db.refresh(group)
    await db.commit()

    return await get_group(db, group_id, user)


async def delete_group(db: AsyncSession, group_id: int, user: User) -> dict | None:
    result = await db.execute(
        select(BoxGroup)
        .where(BoxGroup.id == group_id)
        .where(BoxGroup.owner_id == user.id)
    )
    group = result.scalar_one_or_none()
    if not group:
        return None

    # Unassign boxes from this group (set group_id to NULL)
    await db.execute(
        select(StorageBox)
        .where(StorageBox.group_id == group_id)
    )
    boxes_result = await db.execute(
        select(StorageBox).where(StorageBox.group_id == group_id)
    )
    boxes = boxes_result.scalars().all()
    for box in boxes:
        box.group_id = None

    group_name = group.name
    await db.delete(group)
    await db.commit()

    return {"name": group_name, "boxes_unassigned": len(boxes)}
