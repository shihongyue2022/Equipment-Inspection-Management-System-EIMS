from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Equipment, Inspection, User


REQUIRED_FIELDS = (
    "name",
    "location",
    "equipment_type",
    "manufacturer",
    "model_number",
    "installed_at",
    "inspection_interval_months",
)


def list_equipment(*, user_id=None, base=None):
    statement = select(Equipment).options(
        selectinload(Equipment.assigned_user),
        selectinload(Equipment.inspections),
    )
    if user_id is not None:
        statement = statement.where(Equipment.assigned_user_id == user_id)
    if base:
        statement = statement.join(Equipment.assigned_user).where(User.base == base)
    statement = statement.order_by(
        Equipment.next_inspection_date.is_(None),
        Equipment.next_inspection_date,
        Equipment.id,
    )
    return db.session.scalars(statement).all()


def get_equipment(equipment_id):
    statement = (
        select(Equipment)
        .where(Equipment.id == equipment_id)
        .options(
            selectinload(Equipment.assigned_user),
            selectinload(Equipment.inspections).selectinload(Inspection.engineer),
        )
    )
    return db.session.scalar(statement)


def engineers():
    return db.session.scalars(
        select(User).where(User.role == "engineer").order_by(User.id)
    ).all()


def parse_equipment(form):
    values = {field: form.get(field, "").strip() for field in REQUIRED_FIELDS}
    if not all(values.values()):
        return None, "必須項目をすべて入力してください。"
    try:
        values["installed_at"] = date.fromisoformat(values["installed_at"])
        values["inspection_interval_months"] = int(
            values["inspection_interval_months"]
        )
        if not 1 <= values["inspection_interval_months"] <= 12:
            raise ValueError
        assigned_id = form.get("assigned_user_id", "").strip()
        values["assigned_user_id"] = int(assigned_id) if assigned_id else None
    except (TypeError, ValueError):
        return None, "日付または点検間隔（1〜12か月）が正しくありません。"
    return values, None


def create_equipment(values):
    equipment = Equipment(**values)
    db.session.add(equipment)
    db.session.commit()
    return equipment


def update_equipment(equipment, values):
    for field, value in values.items():
        setattr(equipment, field, value)
    db.session.commit()
    return equipment


def assign_equipment(equipment, assigned_user_id):
    equipment.assigned_user_id = assigned_user_id
    db.session.commit()


def delete_equipment(equipment):
    db.session.delete(equipment)
    db.session.commit()
