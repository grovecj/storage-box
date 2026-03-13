import csv
import io
from datetime import datetime

from jinja2 import Template
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.box import StorageBox
from app.models.item import BoxItem, BoxItemTag
from app.models.tag import Tag
from app.models.user import User
from app.schemas.report import ReportRequest


REPORT_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Storage Box Inventory Report</title>
<style>
  @page { size: letter; margin: 0.75in; }
  body { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 11pt; color: #1a1a1a; }
  h1 { font-size: 18pt; border-bottom: 2px solid #333; padding-bottom: 8px; }
  h2 { font-size: 14pt; margin-top: 24px; color: #2a2a2a; }
  .box-header { display: flex; justify-content: space-between; align-items: baseline; }
  .box-meta { font-size: 9pt; color: #666; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; }
  th { background-color: #f5f5f5; font-weight: 600; }
  .tag { display: inline-block; background: #e0e7ff; color: #3730a3; padding: 1px 6px;
         border-radius: 3px; font-size: 9pt; margin-right: 4px; }
  .footer { margin-top: 32px; font-size: 9pt; color: #999; text-align: center; }
  .page-break { page-break-before: always; }
</style>
</head>
<body>
<h1>Storage Box Inventory Report</h1>
<p class="box-meta">Generated: {{ generated_at }}</p>

{% for box in boxes %}
{% if not loop.first %}<div class="page-break"></div>{% endif %}
<div class="box-header">
  <h2>{{ box.box_code }} &mdash; {{ box.name }}</h2>
</div>
<p class="box-meta">
  {% if box.location_name %}Location: {{ box.location_name }} | {% endif %}
  {% if box.latitude and box.longitude %}GPS: {{ box.latitude }}, {{ box.longitude }} | {% endif %}
  Items: {{ box["items"] | length }}
</p>
<table>
  <thead>
    <tr><th>Item</th><th>Qty</th><th>Tags</th></tr>
  </thead>
  <tbody>
  {% for item in box["items"] %}
    <tr>
      <td>{{ item.name }}</td>
      <td>{{ item.quantity }}</td>
      <td>{% for tag in item.tags %}<span class="tag">{{ tag }}</span>{% endfor %}</td>
    </tr>
  {% endfor %}
  {% if not box["items"] %}
    <tr><td colspan="3" style="text-align:center; color:#999;">No items</td></tr>
  {% endif %}
  </tbody>
</table>
{% endfor %}

<div class="footer">Storage Box Inventory Report &bull; {{ generated_at }}</div>
</body>
</html>
"""


async def _fetch_report_data(
    db: AsyncSession, request: ReportRequest, user: User
) -> list[dict]:
    query = (
        select(StorageBox)
        .where(StorageBox.owner_id == user.id)
        .options(
            selectinload(StorageBox.box_items)
            .selectinload(BoxItem.item),
            selectinload(StorageBox.box_items)
            .selectinload(BoxItem.tags)
            .selectinload(BoxItemTag.tag),
        )
        .order_by(StorageBox.box_code)
    )

    if request.box_ids:
        query = query.where(StorageBox.id.in_(request.box_ids))

    if request.location_filter:
        query = query.where(StorageBox.location_name.icontains(request.location_filter))

    result = await db.execute(query)
    boxes = result.scalars().unique().all()

    report_data = []
    for box in boxes:
        # Extract coordinates
        lat, lng = None, None
        if box.location:
            geom = func.ST_GeomFromWKB(func.ST_AsBinary(StorageBox.location))
            coord_result = await db.execute(
                select(
                    func.ST_Y(geom),
                    func.ST_X(geom),
                ).where(StorageBox.id == box.id)
            )
            coords = coord_result.first()
            if coords:
                lat, lng = coords

        items = []
        for bi in box.box_items:
            tags = [bit.tag.name for bit in bi.tags]
            # Filter by tag if specified
            if request.tag_filter:
                if not any(t in request.tag_filter for t in tags):
                    continue
            items.append({
                "name": bi.item.name,
                "quantity": bi.quantity,
                "tags": tags,
            })

        if request.tag_filter and not items:
            continue

        report_data.append({
            "box_code": box.box_code,
            "name": box.name,
            "latitude": lat,
            "longitude": lng,
            "location_name": box.location_name,
            "items": items,
        })

    return report_data


async def generate_html_report(db: AsyncSession, request: ReportRequest, user: User) -> str:
    data = await _fetch_report_data(db, request, user)
    template = Template(REPORT_HTML_TEMPLATE)
    return template.render(
        boxes=data,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )


async def generate_pdf_report(db: AsyncSession, request: ReportRequest, user: User) -> bytes:
    html = await generate_html_report(db, request, user)
    from weasyprint import HTML
    return HTML(string=html).write_pdf()


async def generate_text_report(db: AsyncSession, request: ReportRequest, user: User) -> str:
    data = await _fetch_report_data(db, request, user)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = []
    sep = "\u2550" * 43
    thin_sep = "\u2500" * 43

    lines.append(sep)
    lines.append("STORAGE BOX INVENTORY REPORT")
    lines.append(f"Generated: {generated_at}")
    lines.append(sep)
    lines.append("")

    total_boxes = len(data)
    grand_total_items = 0
    grand_total_qty = 0

    for box in data:
        lines.append(f"{box['box_code']} \u2014 {box['name']}")
        if box.get("location_name"):
            lines.append(f"Location: {box['location_name']}")
        elif box.get("latitude") and box.get("longitude"):
            lines.append(f"Location: {box['latitude']}, {box['longitude']}")
        lines.append(thin_sep)

        items = box["items"]
        box_qty = 0
        for i, item in enumerate(items, 1):
            tags_str = f"  [{', '.join(item['tags'])}]" if item["tags"] else ""
            qty = item["quantity"]
            box_qty += qty
            lines.append(f"  {i:>3}. {item['name']:<25} x{qty}{tags_str}")

        if not items:
            lines.append("  (no items)")

        lines.append(thin_sep)
        lines.append(f"  Items: {len(items)} | Total Qty: {box_qty}")
        lines.append("")

        grand_total_items += len(items)
        grand_total_qty += box_qty

    lines.append(sep)
    lines.append(f"Total: {total_boxes} boxes | {grand_total_items} items | {grand_total_qty} qty")
    lines.append(sep)

    return "\n".join(lines)


async def generate_csv_report(db: AsyncSession, request: ReportRequest, user: User) -> str:
    data = await _fetch_report_data(db, request, user)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Box Code", "Box Name", "Location", "Latitude", "Longitude", "Item", "Quantity", "Tags"])

    for box in data:
        if box["items"]:
            for item in box["items"]:
                writer.writerow([
                    box["box_code"],
                    box["name"],
                    box.get("location_name", ""),
                    box.get("latitude", ""),
                    box.get("longitude", ""),
                    item["name"],
                    item["quantity"],
                    "; ".join(item["tags"]),
                ])
        else:
            writer.writerow([
                box["box_code"],
                box["name"],
                box.get("location_name", ""),
                box.get("latitude", ""),
                box.get("longitude", ""),
                "", "", "",
            ])

    return output.getvalue()
