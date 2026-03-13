"""
Seed data for local development. Runs once on first startup when the database is empty.
"""

import random

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.box import StorageBox
from app.models.item import Item, BoxItem, BoxItemTag
from app.models.tag import Tag
from app.models.audit import AuditLog
from app.models.user import User

# Realistic locations with GPS coordinates
LOCATIONS = [
    ("Garage - Shelf A", 35.2271, -80.8431),
    ("Garage - Shelf B", 35.2271, -80.8431),
    ("Garage - Floor", 35.2271, -80.8432),
    ("Attic", 35.2272, -80.8430),
    ("Basement - North Wall", 35.2270, -80.8431),
    ("Basement - South Wall", 35.2270, -80.8432),
    ("Closet - Master Bedroom", 35.2273, -80.8429),
    ("Closet - Guest Room", 35.2273, -80.8428),
    ("Storage Unit #4 - Row A", 35.1950, -80.8312),
    ("Storage Unit #4 - Row B", 35.1950, -80.8313),
    ("Storage Unit #4 - Row C", 35.1951, -80.8312),
    ("Workshop Bench", 35.2271, -80.8433),
    ("Shed - Left Side", 35.2269, -80.8435),
    ("Shed - Right Side", 35.2269, -80.8434),
    ("Vacation House - Garage", 34.7254, -76.7260),
    ("Vacation House - Closet", 34.7255, -76.7259),
    (None, None, None),
    (None, None, None),
]

# (item_name, max_quantity)
ITEMS = [
    ("Passport", 1), ("Passport Holder", 2), ("Travel Adapter (EU)", 3),
    ("Travel Adapter (UK)", 2), ("TSA Lock", 4), ("Luggage Tags", 6),
    ("Packing Cubes", 3), ("Neck Pillow", 1), ("Eye Mask", 2),
    ("Phillips Screwdriver Set", 1), ("Flathead Screwdriver Set", 1),
    ("Allen Wrench Set", 1), ("Cordless Drill Bits", 15),
    ("Wood Screws - Assorted", 50), ("Drywall Anchors", 20),
    ("Picture Hanging Kit", 1), ("Duct Tape", 3), ("Electrical Tape", 4),
    ("WD-40", 1), ("Super Glue", 5),
    ("Extension Cord - 25ft", 2), ("Extension Cord - 50ft", 1),
    ("Power Strip", 3), ("USB-A to USB-C Cable", 5),
    ("Lightning Cable", 3), ("HDMI Cable - 6ft", 2),
    ("Ethernet Cable - 10ft", 3), ("Coax Cable", 2),
    ("Arduino Uno", 2), ("Raspberry Pi 4", 1), ("Breadboard", 3),
    ("Jumper Wires", 50), ("Soldering Iron", 1), ("Solder", 2),
    ("Resistor Kit", 1), ("LED Assortment", 30), ("PCB Blanks", 5),
    ("ESP32 Modules", 4), ("Servo Motors", 3), ("Stepper Motor", 1),
    ("Christmas Lights - White", 3), ("Christmas Lights - Multi", 2),
    ("Christmas Ornaments", 25), ("Wreath", 1),
    ("Halloween Decorations", 10), ("Easter Decorations", 5),
    ("Camping Tent", 1), ("Sleeping Bag", 2), ("Camp Stove", 1),
    ("Cooler - Large", 1), ("Folding Chairs", 4), ("Lantern", 2),
    ("Fishing Rod", 2), ("Tackle Box", 1),
    ("Winter Jacket - Spare", 1), ("Rain Jacket", 1),
    ("Hiking Boots", 1), ("Snow Boots", 1), ("Wetsuit", 1),
    ("Snorkel Set", 2), ("Beach Towels", 4), ("Sunscreen", 3),
    ("Paint Roller Set", 1), ("Paint Brushes - Assorted", 6),
    ("Drop Cloth", 2), ("Painter's Tape", 3), ("Sandpaper - Mixed", 10),
    ("Caulk Gun", 1), ("Caulk Tubes", 4),
    ("Spare Light Bulbs", 8), ("Smoke Detector Batteries", 6),
    ("Air Filters - HVAC", 3), ("Furnace Filters", 2),
    ("Garden Gloves", 2), ("Pruning Shears", 1), ("Plant Pots", 5),
    ("Potting Soil Bag", 2), ("Fertilizer", 1), ("Sprinkler Head", 3),
    ("Photo Albums", 3), ("Yearbooks", 4), ("Baby Clothes", 15),
    ("Board Games", 5), ("Puzzle - 1000pc", 3), ("Playing Cards", 4),
    ("Old Textbooks", 8), ("Tax Returns 2023", 1), ("Tax Returns 2022", 1),
    ("Warranty Documents", 10), ("Owners Manuals", 12),
]

TAG_RULES: dict[str, list[str]] = {
    "PCB": ["Arduino", "Raspberry", "Breadboard", "Jumper", "Solder", "Resistor",
            "LED", "PCB", "ESP32", "Servo", "Stepper"],
    "VACATION": ["Passport", "Travel Adapter", "TSA Lock", "Luggage", "Packing Cubes",
                 "Neck Pillow", "Eye Mask", "Snorkel", "Beach", "Wetsuit", "Sunscreen"],
    "LONG_TERM": ["Tax Returns", "Photo Albums", "Yearbooks", "Baby Clothes",
                  "Warranty", "Owners Manuals", "Old Textbooks"],
    "SEASONAL": ["Christmas", "Halloween", "Easter", "Winter Jacket", "Snow Boots"],
    "CAMPING": ["Camping Tent", "Sleeping Bag", "Camp Stove", "Cooler", "Folding Chairs",
                "Lantern", "Fishing"],
    "TOOLS": ["Screwdriver", "Allen Wrench", "Drill", "Screws", "Anchors", "Duct Tape",
              "Electrical Tape", "WD-40", "Super Glue", "Caulk", "Paint", "Sandpaper",
              "Pruning"],
    "CABLES": ["Extension Cord", "Power Strip", "USB", "Lightning", "HDMI",
               "Ethernet", "Coax"],
    "HOME_MAINTENANCE": ["Light Bulbs", "Smoke Detector", "Air Filters", "Furnace",
                         "Sprinkler"],
}

BOX_NAMES = [
    "Electronics & PCBs", "Travel Essentials", "Holiday Decorations",
    "Camping Gear", "Hand Tools", "Power Tools & Hardware",
    "Cables & Adapters", "Paint Supplies", "Plumbing Supplies",
    "Outdoor Equipment", "Winter Gear", "Summer Gear",
    "Keepsakes & Memories", "Important Documents", "Kids Stuff",
    "Board Games & Puzzles", "Kitchen Overflow", "Spare Parts",
    "Bathroom Supplies", "Office Supplies", "Garden Supplies",
    "Fishing Equipment", "Beach Supplies", "Guest Room Extras",
    "Workshop Overflow", "Seasonal Rotation A", "Seasonal Rotation B",
    "Fragile Items", "Heavy Hardware", "Miscellaneous",
]

NUM_BOXES = 30


def _get_tags_for_item(item_name: str) -> list[str]:
    tags = []
    for tag, keywords in TAG_RULES.items():
        if any(kw.lower() in item_name.lower() for kw in keywords):
            tags.append(tag)
    return tags


async def seed_if_empty(db: AsyncSession) -> None:
    """Seed the database with sample data if no boxes exist. Idempotent."""
    result = await db.execute(select(func.count(StorageBox.id)))
    if result.scalar() > 0:
        return

    # Create or get dev user
    user_result = await db.execute(select(User).where(User.google_id == "dev-user"))
    dev_user = user_result.scalar_one_or_none()
    if not dev_user:
        dev_user = User(
            google_id="dev-user",
            email="dev@localhost",
            name="Dev User",
            picture_url=None,
        )
        db.add(dev_user)
        await db.flush()

    # Ensure all tags exist
    all_tag_names = ["PCB", "VACATION", "LONG_TERM", "SEASONAL", "CAMPING",
                     "TOOLS", "CABLES", "HOME_MAINTENANCE"]
    for tag_name in all_tag_names:
        await db.execute(
            text("INSERT INTO tags (name, created_by, updated_by) VALUES (:name, :user_id, :user_id) ON CONFLICT (name) DO NOTHING"),
            {"name": tag_name, "user_id": dev_user.id},
        )
    await db.flush()

    tag_result = await db.execute(select(Tag))
    tags_by_name = {t.name: t for t in tag_result.scalars().all()}

    # Create boxes
    random.seed(42)  # Deterministic for reproducibility
    boxes = []
    for i in range(NUM_BOXES):
        loc = LOCATIONS[i % len(LOCATIONS)]
        location_name, lat, lng = loc
        box_code = f"BOX-{i + 1:04d}"
        name = BOX_NAMES[i % len(BOX_NAMES)]

        location_wkt = f"SRID=4326;POINT({lng} {lat})" if lat and lng else None
        box = StorageBox(
            box_code=box_code,
            name=name,
            location=location_wkt,
            location_name=location_name,
            owner_id=dev_user.id,
            created_by=dev_user.id,
            updated_by=dev_user.id,
        )
        db.add(box)
        await db.flush()
        boxes.append(box)

    # Create items and distribute across boxes
    item_objects: dict[str, Item] = {}

    for box in boxes:
        num_items = random.randint(3, 12)
        chosen_items = random.sample(ITEMS, min(num_items, len(ITEMS)))

        for item_name, max_qty in chosen_items:
            if item_name not in item_objects:
                item_obj = Item(name=item_name, created_by=dev_user.id, updated_by=dev_user.id)
                db.add(item_obj)
                await db.flush()
                item_objects[item_name] = item_obj
            else:
                item_obj = item_objects[item_name]

            # Skip if already in this box
            existing = await db.execute(
                select(BoxItem).where(
                    BoxItem.box_id == box.id,
                    BoxItem.item_id == item_obj.id,
                )
            )
            if existing.scalar_one_or_none():
                continue

            quantity = random.randint(1, max_qty)
            box_item = BoxItem(
                box_id=box.id,
                item_id=item_obj.id,
                quantity=quantity,
                created_by=dev_user.id,
                updated_by=dev_user.id,
            )
            db.add(box_item)
            await db.flush()

            for tag_name in _get_tags_for_item(item_name):
                if tag_name in tags_by_name:
                    db.add(BoxItemTag(box_item_id=box_item.id, tag_id=tags_by_name[tag_name].id))

    # Audit entries
    for box in boxes:
        db.add(AuditLog(
            box_id=box.id,
            action="BOX_CREATED",
            details={"box_code": box.box_code, "name": box.name, "user_id": dev_user.id},
        ))

    await db.commit()
