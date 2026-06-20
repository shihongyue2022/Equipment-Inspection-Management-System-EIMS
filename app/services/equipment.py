from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Equipment, Inspection, Maintenance, User


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


def paginate_equipment(
    *,
    page=1,
    per_page=50,
    user_id=None,
    base=None,
    equipment_type=None,
    manufacturer=None,
    engineer_id=None,
):
    statement = select(Equipment).options(
        selectinload(Equipment.assigned_user),
        selectinload(Equipment.inspections),
    )
    if user_id is not None:
        statement = statement.where(Equipment.assigned_user_id == user_id)
    if base:
        statement = statement.join(Equipment.assigned_user).where(User.base == base)
    if equipment_type:
        statement = statement.where(Equipment.equipment_type == equipment_type)
    if manufacturer:
        statement = statement.where(Equipment.manufacturer == manufacturer)
    if engineer_id is not None:
        statement = statement.where(Equipment.assigned_user_id == engineer_id)
    statement = statement.order_by(
        Equipment.next_inspection_date.is_(None),
        Equipment.next_inspection_date,
        Equipment.id,
    )
    return db.paginate(
        statement,
        page=max(page, 1),
        per_page=per_page,
        max_per_page=100,
        error_out=False,
    )


def dashboard_filter_options(
    *,
    user_id=None,
    base=None,
    equipment_type=None,
    manufacturer=None,
    engineer_id=None,
):
    filters = {
        "base": base,
        "equipment_type": equipment_type,
        "manufacturer": manufacturer,
        "engineer_id": engineer_id,
    }

    def apply_facets(statement, *, exclude):
        statement = statement.select_from(Equipment).join(
            User, User.id == Equipment.assigned_user_id
        )
        if user_id is not None:
            statement = statement.where(Equipment.assigned_user_id == user_id)
        if filters["base"] and exclude != "base":
            statement = statement.where(User.base == filters["base"])
        if filters["equipment_type"] and exclude != "equipment_type":
            statement = statement.where(
                Equipment.equipment_type == filters["equipment_type"]
            )
        if filters["manufacturer"] and exclude != "manufacturer":
            statement = statement.where(
                Equipment.manufacturer == filters["manufacturer"]
            )
        if filters["engineer_id"] is not None and exclude != "engineer_id":
            statement = statement.where(
                Equipment.assigned_user_id == filters["engineer_id"]
            )
        return statement

    def counted_values(column, *, exclude):
        statement = apply_facets(
            select(column.label("value"), func.count(Equipment.id).label("count")),
            exclude=exclude,
        )
        statement = (
            statement.where(column.is_not(None))
            .group_by(column)
            .order_by(column)
        )
        return [
            {"value": row.value, "count": int(row.count)}
            for row in db.session.execute(statement)
        ]

    engineer_statement = apply_facets(
        select(
            User.id,
            User.last_name,
            User.first_name,
            func.count(Equipment.id).label("count"),
        ),
        exclude="engineer_id",
    )
    engineer_statement = (
        engineer_statement.where(User.role == "engineer")
        .group_by(User.id, User.last_name, User.first_name)
        .order_by(User.last_name, User.first_name, User.id)
    )
    engineers = [
        {
            "id": row.id,
            "name": f"{row.last_name}{row.first_name}",
            "count": int(row.count),
        }
        for row in db.session.execute(engineer_statement)
    ]
    return {
        "bases": counted_values(User.base, exclude="base"),
        "equipment_types": counted_values(
            Equipment.equipment_type, exclude="equipment_type"
        ),
        "manufacturers": counted_values(
            Equipment.manufacturer, exclude="manufacturer"
        ),
        "engineers": engineers,
    }


def get_equipment(equipment_id):
    statement = (
        select(Equipment)
        .where(Equipment.id == equipment_id)
        .options(
            selectinload(Equipment.assigned_user),
            selectinload(Equipment.inspections).selectinload(Inspection.engineer),
            selectinload(Equipment.inspections).selectinload(
                Inspection.maintenance_records
            ),
            selectinload(Equipment.maintenance_records).selectinload(
                Maintenance.engineer
            ),
            selectinload(Equipment.maintenance_records).selectinload(
                Maintenance.source_inspection
            ),
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
