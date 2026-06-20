from flask import Blueprint, redirect, render_template, request, session, url_for

from app.common.auth import login_required
from app.forms import CsrfForm
from app.services import inspection as service
from app.services.equipment import list_equipment


bp = Blueprint("inspections", __name__, url_prefix="/inspection")


def _available_equipment():
    user = session["user"]
    return (
        list_equipment()
        if user["role"] in {"root", "admin"}
        else list_equipment(user_id=user["id"])
    )


@bp.get("/new")
@login_required
def new_get():
    selected = request.args.get("equipment_id", type=int)
    return render_template(
        "inspection/new.html",
        form=CsrfForm(),
        equipment_list=_available_equipment(),
        selected_equipment_id=selected,
        form_data=None,
        error_message=None,
    )


@bp.post("/new")
@login_required
def new_post():
    equipment_list = _available_equipment()
    values, error = service.parse_inspection(request.form)
    if not error and session["user"]["role"] == "engineer":
        allowed = {equipment.id for equipment in equipment_list}
        if values["equipment_id"] not in allowed:
            return redirect(url_for("dashboard.index"))
    if error:
        return render_template(
            "inspection/new.html",
            form=CsrfForm(),
            equipment_list=equipment_list,
            selected_equipment_id=request.form.get("equipment_id"),
            form_data=request.form,
            error_message=error,
        )
    service.register_inspection(values, session["user"]["id"])
    return redirect(url_for("dashboard.index"))

