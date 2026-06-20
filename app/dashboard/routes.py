from flask import Blueprint, render_template, request, session

from app.common.auth import login_required
from app.services.accounts import bases
from app.services.equipment import list_equipment


bp = Blueprint("dashboard", __name__)


@bp.get("/dashboard")
@login_required
def index():
    user = session["user"]
    selected_base = request.args.get("base") or None
    if user["role"] in {"root", "admin"}:
        equipment_list = list_equipment(base=selected_base)
        base_list = bases()
    else:
        selected_base = None
        equipment_list = list_equipment(user_id=user["id"])
        base_list = []
    return render_template(
        "dashboard.html",
        equipment_list=equipment_list,
        total_count=len(equipment_list),
        overdue_count=sum(e.deadline_status == "overdue" for e in equipment_list),
        soon_count=sum(e.deadline_status == "soon" for e in equipment_list),
        repair_count=sum(e.latest_inspection_status == "repair" for e in equipment_list),
        bases=base_list,
        selected_base=selected_base,
    )

