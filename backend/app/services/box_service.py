from geoalchemy2.functions import ST_X, ST_Y, ST_Distance, ST_GeogFromText
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.box import StorageBox, box_code_seq
from app.models.item import BoxItem
from app.models.user import User
from app.schemas.box import BoxCreate, BoxUpdate, BoxResponse, BoxListResponse
from app.utils.audit import log_action


def _make_point(lat: float, lng: float) -> str:
    return f"SRID=4326;POINT({lng} {lat})"


def _box_to_response(box: StorageBox, item_count: int = 0, lat: float | None = None, lng: float | None = None) -> BoxResponse:
    return BoxResponse(
        id=box.id,
        box_code=box.box_code,
        name=box.name,
        latitude=lat,
        longitude=lng,
        location_name=box.location_name,
        item_count=item_count,
        created_at=box.created_at,
        updated_at=box.updated_at,
        created_by=box.created_by,
        updated_by=box.updated_by,
    )


def _location_columns():
    """Return ST_Y (lat) and ST_X (lng) columns for the geography field."""
    geom = func.ST_GeomFromWKB(func.ST_AsBinary(StorageBox.location))
    return (
        ST_Y(geom).label("lat"),
        ST_X(geom).label("lng"),
    )


async def get_next_box_code(db: AsyncSession) -> str:
    result = await db.execute(text(f"SELECT nextval('{box_code_seq.name}')"))
    next_num = result.scalar()
    return f"BOX-{next_num:04d}"


async def create_box(db: AsyncSession, data: BoxCreate, user: User) -> BoxResponse:
    box_code = await get_next_box_code(db)
    location = None
    lat, lng = None, None
    if data.location:
        lat = data.location.latitude
        lng = data.location.longitude
        location = _make_point(lat, lng)

    box = StorageBox(
        box_code=box_code,
        name=data.name,
        location=location,
        location_name=data.location_name,
        owner_id=user.id,
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(box)
    await db.flush()
    await db.refresh(box)

    await log_action(db, box.id, "BOX_CREATED", {"box_code": box_code, "name": data.name, "user_id": user.id})
    await db.commit()

    return _box_to_response(box, item_count=0, lat=lat, lng=lng)


async def get_box(db: AsyncSession, box_id: int, user: User) -> BoxResponse | None:
    lat_col, lng_col = _location_columns()
    result = await db.execute(
        select(
            StorageBox,
            func.count(BoxItem.id).label("item_count"),
            lat_col,
            lng_col,
        )
        .outerjoin(BoxItem, BoxItem.box_id == StorageBox.id)
        .where(StorageBox.id == box_id)
        .where(StorageBox.owner_id == user.id)
        .group_by(StorageBox.id)
    )
    row = result.first()
    if not row or not row[0]:
        return None
    box, item_count, lat, lng = row
    return _box_to_response(box, item_count=item_count, lat=lat, lng=lng)


async def get_box_by_code(db: AsyncSession, box_code: str, user: User) -> BoxResponse | None:
    lat_col, lng_col = _location_columns()
    result = await db.execute(
        select(
            StorageBox,
            func.count(BoxItem.id).label("item_count"),
            lat_col,
            lng_col,
        )
        .outerjoin(BoxItem, BoxItem.box_id == StorageBox.id)
        .where(StorageBox.box_code == box_code)
        .where(StorageBox.owner_id == user.id)
        .group_by(StorageBox.id)
    )
    row = result.first()
    if not row or not row[0]:
        return None
    box, item_count, lat, lng = row
    return _box_to_response(box, item_count=item_count, lat=lat, lng=lng)


async def list_boxes(
    db: AsyncSession,
    user: User,
    page: int = 1,
    page_size: int = 20,
    sort: str = "recent",
    lat: float | None = None,
    lng: float | None = None,
) -> BoxListResponse:
    count_result = await db.execute(
        select(func.count(StorageBox.id)).where(StorageBox.owner_id == user.id)
    )
    total = count_result.scalar()

    lat_col, lng_col = _location_columns()
    query = (
        select(
            StorageBox,
            func.count(BoxItem.id).label("item_count"),
            lat_col,
            lng_col,
        )
        .outerjoin(BoxItem, BoxItem.box_id == StorageBox.id)
        .where(StorageBox.owner_id == user.id)
        .group_by(StorageBox.id)
    )

    if sort == "proximity" and lat is not None and lng is not None:
        user_point = ST_GeogFromText(f"SRID=4326;POINT({lng} {lat})")
        query = query.order_by(ST_Distance(StorageBox.location, user_point))
    else:
        query = query.order_by(StorageBox.updated_at.desc())

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)

    boxes = []
    for row in result.all():
        box, item_count, box_lat, box_lng = row
        boxes.append(_box_to_response(box, item_count=item_count, lat=box_lat, lng=box_lng))

    return BoxListResponse(boxes=boxes, total=total, page=page, page_size=page_size)


async def update_box(db: AsyncSession, box_id: int, data: BoxUpdate, user: User) -> BoxResponse | None:
    result = await db.execute(
        select(StorageBox)
        .where(StorageBox.id == box_id)
        .where(StorageBox.owner_id == user.id)
    )
    box = result.scalar_one_or_none()
    if not box:
        return None

    if data.name is not None:
        box.name = data.name
    if data.location is not None:
        box.location = _make_point(data.location.latitude, data.location.longitude)
    if data.location_name is not None:
        box.location_name = data.location_name

    box.updated_by = user.id

    await db.flush()
    await db.refresh(box)
    await log_action(db, box.id, "BOX_UPDATED", {"changes": data.model_dump(exclude_none=True), "user_id": user.id})
    await db.commit()

    return await get_box(db, box_id, user)


async def delete_box(db: AsyncSession, box_id: int, user: User) -> dict | None:
    result = await db.execute(
        select(StorageBox)
        .where(StorageBox.id == box_id)
        .where(StorageBox.owner_id == user.id)
    )
    box = result.scalar_one_or_none()
    if not box:
        return None

    item_count_result = await db.execute(
        select(func.count(BoxItem.id)).where(BoxItem.box_id == box_id)
    )
    item_count = item_count_result.scalar()

    await log_action(db, box.id, "BOX_DELETED", {
        "box_code": box.box_code,
        "name": box.name,
        "items_removed": item_count,
        "user_id": user.id,
    })

    await db.delete(box)
    await db.commit()

    return {"box_code": box.box_code, "items_removed": item_count}
