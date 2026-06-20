from flask import Blueprint, render_template, request, session

from app.common.auth import login_required
from app.services.accounts import bases
from app.services.dashboard import (
    GROUP_OPTIONS,
    dashboard_summary,
    grouped_equipment_summary,
)
from app.services.equipment import paginate_equipment


bp = Blueprint("dashboard", __name__)


@bp.get("/dashboard")
@login_required
def index():
    user = session["user"]
    selected_base = request.args.get("base") or None
    selected_group = request.args.get("group_by", "base")
    if selected_group not in GROUP_OPTIONS:
        selected_group = "base"
    page = max(request.args.get("page", 1, type=int), 1)

    if user["role"] in {"root", "admin"}:
        scope = {"base": selected_base}
        base_list = bases()
    else:
        selected_base = None
        scope = {"user_id": user["id"]}
        base_list = []

    pagination = paginate_equipment(page=page, per_page=50, **scope)
    summary = dashboard_summary(**scope)
    grouped_summary = grouped_equipment_summary(selected_group, **scope)
    return render_template(
        "dashboard.html",
        equipment_list=pagination.items,
        pagination=pagination,
        grouped_summary=grouped_summary,
        group_options=GROUP_OPTIONS,
        selected_group=selected_group,
        bases=base_list,
        selected_base=selected_base,
        **summary,
    )

