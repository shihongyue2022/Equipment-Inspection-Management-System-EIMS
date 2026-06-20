from datetime import date

from dateutil.relativedelta import relativedelta

from app.extensions import db
from app.models import Equipment, Inspection


VALID_STATUSES = {"normal", "watch", "repair"}


def parse_inspection(form):
    equipment_id = form.get("equipment_id", "").strip()
    inspected_at = form.get("inspected_at", "").strip()
    status = form.get("status", "").strip()
    if not equipment_id or not inspected_at or status not in VALID_STATUSES:
        return None, "入力情報に誤りがあります。必須項目をすべて入力してください。"
    try:
        values = {
            "equipment_id": int(equipment_id),
            "inspected_at": date.fromisoformat(inspected_at),
            "status": status,
            "note": form.get("note", "").strip() or None,
        }
    except ValueError:
        return None, "点検日または設備IDが正しくありません。"
    return values, None


def register_inspection(values, engineer_id):
    equipment = db.session.get(Equipment, values["equipment_id"])
    if equipment is None:
        raise LookupError("equipment not found")
    record = Inspection(engineer_id=engineer_id, **values)
    db.session.add(record)
    db.session.flush()
    latest_date = max(
        [values["inspected_at"], *(item.inspected_at for item in equipment.inspections)]
    )
    equipment.next_inspection_date = latest_date + relativedelta(
        months=equipment.inspection_interval_months
    )
    db.session.commit()
    return record
