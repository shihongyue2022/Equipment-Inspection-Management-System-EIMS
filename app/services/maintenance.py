from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Equipment, Inspection, Maintenance


VALID_STATUSES = {"planned", "in_progress", "completed", "cancelled"}


def get_maintenance(maintenance_id):
    return db.session.scalar(
        select(Maintenance)
        .where(Maintenance.id == maintenance_id)
        .options(
            selectinload(Maintenance.equipment),
            selectinload(Maintenance.source_inspection),
        )
    )


def parse_maintenance(form):
    raw_equipment_id = form.get("equipment_id", "").strip()
    raw_source_id = form.get("source_inspection_id", "").strip()
    status = form.get("status", "").strip()
    action = form.get("action", "").strip()
    if not raw_equipment_id or status not in VALID_STATUSES or not action:
        return None, "設備、対応状況、作業内容は必須です。"

    try:
        values = {
            "equipment_id": int(raw_equipment_id),
            "source_inspection_id": int(raw_source_id) if raw_source_id else None,
            "status": status,
            "action": action,
            "started_at": _optional_date(form.get("started_at")),
            "completed_at": _optional_date(form.get("completed_at")),
            "result": form.get("result", "").strip() or None,
            "note": form.get("note", "").strip() or None,
        }
    except ValueError:
        return None, "日付またはIDが正しくありません。"

    if status in {"in_progress", "completed"} and not values["started_at"]:
        return None, "対応中または完了の場合は着手日を入力してください。"
    if status == "completed" and not values["completed_at"]:
        return None, "完了の場合は完了日を入力してください。"
    if (
        values["started_at"]
        and values["completed_at"]
        and values["completed_at"] < values["started_at"]
    ):
        return None, "完了日は着手日以降にしてください。"
    return values, None


def _optional_date(value):
    value = (value or "").strip()
    return date.fromisoformat(value) if value else None


def validate_source(values, *, current_id=None):
    equipment = db.session.get(Equipment, values["equipment_id"])
    if equipment is None:
        return "設備が見つかりません。"
    source_id = values["source_inspection_id"]
    if source_id is None:
        return None
    inspection = db.session.get(Inspection, source_id)
    if inspection is None or inspection.equipment_id != equipment.id:
        return "起点となる点検記録が正しくありません。"
    existing = db.session.scalar(
        select(Maintenance).where(Maintenance.source_inspection_id == source_id)
    )
    if existing and existing.id != current_id:
        return "この点検記録には既に修理対応が登録されています。"
    return None


def save_maintenance(values, engineer_id, maintenance=None):
    if maintenance is None:
        maintenance = Maintenance(engineer_id=engineer_id, **values)
        db.session.add(maintenance)
    else:
        for field, value in values.items():
            setattr(maintenance, field, value)
        maintenance.engineer_id = engineer_id
    db.session.commit()
    return maintenance


def equipment_timeline(equipment):
    events = []
    for inspection in equipment.inspections:
        events.append(
            {
                "date": inspection.inspected_at,
                "kind": "inspection",
                "status": inspection.status,
                "title": f"点検：{inspection.status_label}",
                "actor": inspection.engineer_name,
                "detail": inspection.note,
                "record": inspection,
            }
        )

    for maintenance in equipment.maintenance_records:
        if maintenance.status == "cancelled":
            event_date = (
                maintenance.completed_at
                or maintenance.started_at
                or (
                    maintenance.source_inspection.inspected_at
                    if maintenance.source_inspection
                    else maintenance.created_at.date()
                )
            )
            events.append(
                {
                    "date": event_date,
                    "kind": "maintenance_cancelled",
                    "status": maintenance.status,
                    "title": "修理対応を取消",
                    "actor": maintenance.engineer_name,
                    "detail": maintenance.note or maintenance.action,
                    "record": maintenance,
                }
            )
            continue
        if maintenance.started_at:
            events.append(
                {
                    "date": maintenance.started_at,
                    "kind": "maintenance_started",
                    "status": maintenance.status,
                    "title": "修理対応を開始",
                    "actor": maintenance.engineer_name,
                    "detail": maintenance.action,
                    "record": maintenance,
                }
            )
        if maintenance.completed_at:
            events.append(
                {
                    "date": maintenance.completed_at,
                    "kind": "maintenance_completed",
                    "status": maintenance.status,
                    "title": "修理対応が完了",
                    "actor": maintenance.engineer_name,
                    "detail": maintenance.result or maintenance.action,
                    "record": maintenance,
                }
            )
        elif not maintenance.started_at:
            event_date = (
                maintenance.source_inspection.inspected_at
                if maintenance.source_inspection
                else maintenance.created_at.date()
            )
            events.append(
                {
                    "date": event_date,
                    "kind": "maintenance_planned",
                    "status": maintenance.status,
                    "title": f"修理対応：{maintenance.status_label}",
                    "actor": maintenance.engineer_name,
                    "detail": maintenance.action,
                    "record": maintenance,
                }
            )

    return sorted(
        events,
        key=lambda event: (event["date"], event["kind"], event["record"].id),
        reverse=True,
    )
