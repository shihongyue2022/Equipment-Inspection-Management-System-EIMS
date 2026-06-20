from flask import Blueprint, render_template, request, session

from app.common.auth import login_required
from app.services.dashboard import (
    GROUP_OPTIONS,
    SORT_OPTIONS,
    SORT_ORDERS,
    dashboard_summary,
    grouped_equipment_summary,
)
from app.services.equipment import dashboard_filter_options, paginate_equipment


bp = Blueprint("dashboard", __name__)


@bp.get("/dashboard")
@login_required
def index():
    user = session["user"]
    selected_base = request.args.get("base") or None
    selected_type = request.args.get("equipment_type") or None
    selected_manufacturer = request.args.get("manufacturer") or None
    selected_engineer = request.args.get("engineer_id", type=int)
    selected_group = request.args.get("group_by", "base")
    if selected_group not in GROUP_OPTIONS:
        selected_group = "base"
    selected_sort = request.args.get("sort_by", "total")
    if selected_sort not in SORT_OPTIONS:
        selected_sort = "total"
    selected_order = request.args.get("sort_order", "desc")
    if selected_order not in SORT_ORDERS:
        selected_order = "desc"
    page = max(request.args.get("page", 1, type=int), 1)

    permission_user_id = user["id"] if user["role"] == "engineer" else None
    if permission_user_id is not None:
        selected_base = None
        selected_engineer = None

    def load_filter_options():
        return dashboard_filter_options(
            user_id=permission_user_id,
            base=selected_base,
            equipment_type=selected_type,
            manufacturer=selected_manufacturer,
            engineer_id=selected_engineer,
        )

    filter_options = load_filter_options()
    valid_values = {
        "base": {item["value"] for item in filter_options["bases"]},
        "equipment_type": {
            item["value"] for item in filter_options["equipment_types"]
        },
        "manufacturer": {
            item["value"] for item in filter_options["manufacturers"]
        },
        "engineer_id": {item["id"] for item in filter_options["engineers"]},
    }
    normalized = False
    if selected_base is not None and selected_base not in valid_values["base"]:
        selected_base = None
        normalized = True
    if selected_type is not None and selected_type not in valid_values["equipment_type"]:
        selected_type = None
        normalized = True
    if (
        selected_manufacturer is not None
        and selected_manufacturer not in valid_values["manufacturer"]
    ):
        selected_manufacturer = None
        normalized = True
    if (
        selected_engineer is not None
        and selected_engineer not in valid_values["engineer_id"]
    ):
        selected_engineer = None
        normalized = True
    if normalized:
        filter_options = load_filter_options()

    scope = {
        "user_id": permission_user_id,
        "base": selected_base,
        "equipment_type": selected_type,
        "manufacturer": selected_manufacturer,
        "engineer_id": selected_engineer,
    }
    fixed_dimensions = {
        dimension
        for dimension, value in (
            ("base", selected_base),
            ("equipment_type", selected_type),
            ("manufacturer", selected_manufacturer),
            ("engineer", selected_engineer),
        )
        if value is not None
    }
    if selected_group in fixed_dimensions:
        selected_group = next(
            option for option in GROUP_OPTIONS if option not in fixed_dimensions
        )

    pagination = paginate_equipment(page=page, per_page=50, **scope)
    summary = dashboard_summary(**scope)
    grouped_summary = grouped_equipment_summary(
        selected_group,
        sort_by=selected_sort,
        sort_order=selected_order,
        **scope,
    )
    return render_template(
        "dashboard.html",
        equipment_list=pagination.items,
        pagination=pagination,
        grouped_summary=grouped_summary,
        group_max_count=max(
            (row["total_count"] for row in grouped_summary), default=0
        ),
        group_options=GROUP_OPTIONS,
        selected_group=selected_group,
        sort_options=SORT_OPTIONS,
        sort_orders=SORT_ORDERS,
        selected_sort=selected_sort,
        selected_order=selected_order,
        selected_base=selected_base,
        filter_options=filter_options,
        selected_type=selected_type,
        selected_manufacturer=selected_manufacturer,
        selected_engineer=selected_engineer,
        fixed_dimensions=fixed_dimensions,
        active_filter_count=len(fixed_dimensions),
        **summary,
    )

