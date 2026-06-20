from datetime import date, timedelta

from sqlalchemy import and_, case, func, select

from app.extensions import db
from app.models import Equipment, Inspection, User


GROUP_OPTIONS = {
    "base": "拠点",
    "equipment_type": "設備種別",
    "manufacturer": "メーカー",
    "engineer": "担当者",
    "status": "最新点検ステータス",
}

SORT_OPTIONS = {
    "total": "設備数",
    "normal_rate": "正常率",
    "watch_rate": "要観察率",
    "repair_rate": "要修理率",
    "uninspected_rate": "未点検率",
    "overdue_rate": "点検超過率",
    "name": "名称",
}

SORT_ORDERS = {"desc": "降順", "asc": "昇順"}

STATUS_LABELS = {
    "normal": "正常",
    "watch": "要観察",
    "repair": "要修理",
    "uninspected": "未点検",
}


def _latest_inspection():
    ranked = select(
        Inspection.equipment_id.label("equipment_id"),
        Inspection.status.label("status"),
        func.row_number()
        .over(
            partition_by=Inspection.equipment_id,
            order_by=(Inspection.inspected_at.desc(), Inspection.id.desc()),
        )
        .label("row_number"),
    ).subquery()
    return (
        select(ranked.c.equipment_id, ranked.c.status)
        .where(ranked.c.row_number == 1)
        .subquery()
    )


def _metrics(latest):
    today = date.today()
    soon_until = today + timedelta(days=7)
    return (
        func.count(Equipment.id).label("total_count"),
        func.coalesce(
            func.sum(case((Equipment.next_inspection_date < today, 1), else_=0)),
            0,
        ).label("overdue_count"),
        func.coalesce(
            func.sum(
                case(
                    (
                        and_(
                            Equipment.next_inspection_date >= today,
                            Equipment.next_inspection_date <= soon_until,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("soon_count"),
        func.coalesce(
            func.sum(case((latest.c.status == "repair", 1), else_=0)), 0
        ).label("repair_count"),
    )


def _inspection_status_metrics(latest):
    return (
        func.coalesce(
            func.sum(case((latest.c.status == "normal", 1), else_=0)), 0
        ).label("normal_count"),
        func.coalesce(
            func.sum(case((latest.c.status == "watch", 1), else_=0)), 0
        ).label("watch_count"),
        func.coalesce(
            func.sum(case((latest.c.status == "repair", 1), else_=0)), 0
        ).label("repair_status_count"),
        func.coalesce(
            func.sum(case((latest.c.status.is_(None), 1), else_=0)), 0
        ).label("uninspected_count"),
    )


def _scoped_statement(
    columns,
    latest,
    *,
    user_id=None,
    base=None,
    equipment_type=None,
    manufacturer=None,
    engineer_id=None,
):
    statement = (
        select(*columns)
        .select_from(Equipment)
        .outerjoin(User, User.id == Equipment.assigned_user_id)
        .outerjoin(latest, latest.c.equipment_id == Equipment.id)
    )
    if user_id is not None:
        statement = statement.where(Equipment.assigned_user_id == user_id)
    if base:
        statement = statement.where(User.base == base)
    if equipment_type:
        statement = statement.where(Equipment.equipment_type == equipment_type)
    if manufacturer:
        statement = statement.where(Equipment.manufacturer == manufacturer)
    if engineer_id is not None:
        statement = statement.where(Equipment.assigned_user_id == engineer_id)
    return statement


def dashboard_summary(
    *, user_id=None, base=None, equipment_type=None, manufacturer=None, engineer_id=None
):
    latest = _latest_inspection()
    row = db.session.execute(
        _scoped_statement(
            _metrics(latest),
            latest,
            user_id=user_id,
            base=base,
            equipment_type=equipment_type,
            manufacturer=manufacturer,
            engineer_id=engineer_id,
        )
    ).one()
    return {
        "total_count": int(row.total_count or 0),
        "overdue_count": int(row.overdue_count or 0),
        "soon_count": int(row.soon_count or 0),
        "repair_count": int(row.repair_count or 0),
    }


def grouped_equipment_summary(
    group_by,
    *,
    sort_by="total",
    sort_order="desc",
    user_id=None,
    base=None,
    equipment_type=None,
    manufacturer=None,
    engineer_id=None,
):
    group_by = group_by if group_by in GROUP_OPTIONS else "base"
    sort_by = sort_by if sort_by in SORT_OPTIONS else "total"
    sort_order = sort_order if sort_order in SORT_ORDERS else "desc"
    latest = _latest_inspection()
    group_expression = {
        "base": func.coalesce(User.base, "未設定"),
        "equipment_type": Equipment.equipment_type,
        "manufacturer": Equipment.manufacturer,
        "engineer": case(
            (User.id.is_(None), "未割当"),
            else_=User.last_name + User.first_name,
        ),
        "status": func.coalesce(latest.c.status, "uninspected"),
    }[group_by]
    statement = _scoped_statement(
        (
            group_expression.label("group_name"),
            *_metrics(latest),
            *_inspection_status_metrics(latest),
        ),
        latest,
        user_id=user_id,
        base=base,
        equipment_type=equipment_type,
        manufacturer=manufacturer,
        engineer_id=engineer_id,
    ).group_by(group_expression)
    today = date.today()
    total = func.count(Equipment.id)
    sort_expression = {
        "total": total,
        "normal_rate": func.sum(case((latest.c.status == "normal", 1), else_=0))
        / func.nullif(total, 0),
        "watch_rate": func.sum(case((latest.c.status == "watch", 1), else_=0))
        / func.nullif(total, 0),
        "repair_rate": func.sum(case((latest.c.status == "repair", 1), else_=0))
        / func.nullif(total, 0),
        "uninspected_rate": func.sum(
            case((latest.c.status.is_(None), 1), else_=0)
        )
        / func.nullif(total, 0),
        "overdue_rate": func.sum(
            case((Equipment.next_inspection_date < today, 1), else_=0)
        )
        / func.nullif(total, 0),
        "name": group_expression,
    }[sort_by]
    primary_order = (
        sort_expression.asc() if sort_order == "asc" else sort_expression.desc()
    )
    statement = statement.order_by(primary_order, total.desc(), group_expression.asc())

    rows = db.session.execute(statement).all()
    return [
        {
            "group_name": (
                STATUS_LABELS.get(row.group_name, row.group_name)
                if group_by == "status"
                else row.group_name
            ),
            "total_count": int(row.total_count or 0),
            "overdue_count": int(row.overdue_count or 0),
            "soon_count": int(row.soon_count or 0),
            "repair_count": int(row.repair_count or 0),
            "normal_count": int(row.normal_count or 0),
            "watch_count": int(row.watch_count or 0),
            "repair_status_count": int(row.repair_status_count or 0),
            "uninspected_count": int(row.uninspected_count or 0),
        }
        for row in rows
    ]
