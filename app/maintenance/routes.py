from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from app.common.auth import login_required
from app.extensions import db
from app.forms import CsrfForm
from app.models import Equipment, Inspection
from app.services import maintenance as service


bp = Blueprint("maintenance", __name__, url_prefix="/maintenance")


def _allowed(equipment):
    user = session["user"]
    return user["role"] in {"root", "admin"} or equipment.assigned_user_id == user["id"]


def _equipment_or_redirect(equipment_id):
    equipment = db.session.get(Equipment, equipment_id)
    if equipment is None:
        abort(404)
    if not _allowed(equipment):
        flash("担当外の設備には修理対応を登録できません。", "danger")
        return None
    return equipment


def _render(equipment, *, maintenance=None, source_inspection=None, form_data=None, error=None):
    return render_template(
        "maintenance/form.html",
        form=CsrfForm(),
        equipment=equipment,
        maintenance=maintenance,
        source_inspection=source_inspection,
        form_data=form_data,
        error_message=error,
    )


@bp.get("/new")
@login_required
def new_get():
    equipment_id = request.args.get("equipment_id", type=int)
    if equipment_id is None:
        abort(404)
    equipment = _equipment_or_redirect(equipment_id)
    if equipment is None:
        return redirect(url_for("dashboard.index"))
    source_id = request.args.get("inspection_id", type=int)
    source = db.session.get(Inspection, source_id) if source_id else None
    if source and source.equipment_id != equipment.id:
        source = None
    return _render(equipment, source_inspection=source)


@bp.post("/new")
@login_required
def new_post():
    values, error = service.parse_maintenance(request.form)
    equipment_id = request.form.get("equipment_id", type=int)
    equipment = _equipment_or_redirect(equipment_id) if equipment_id else None
    if equipment is None:
        return redirect(url_for("dashboard.index"))
    error = error or service.validate_source(values)
    if error:
        source = (
            db.session.get(Inspection, values["source_inspection_id"])
            if values and values["source_inspection_id"]
            else None
        )
        return _render(
            equipment,
            source_inspection=source,
            form_data=request.form,
            error=error,
        )
    maintenance = service.save_maintenance(values, session["user"]["id"])
    flash(f"修理対応「{maintenance.action}」を登録しました。", "success")
    return redirect(url_for("equipment.detail_get", equipment_id=equipment.id))


@bp.get("/<int:maintenance_id>/edit")
@login_required
def edit_get(maintenance_id):
    maintenance = service.get_maintenance(maintenance_id)
    if maintenance is None:
        abort(404)
    if not _allowed(maintenance.equipment):
        return redirect(url_for("dashboard.index"))
    return _render(
        maintenance.equipment,
        maintenance=maintenance,
        source_inspection=maintenance.source_inspection,
    )


@bp.post("/<int:maintenance_id>/edit")
@login_required
def edit_post(maintenance_id):
    maintenance = service.get_maintenance(maintenance_id)
    if maintenance is None:
        abort(404)
    if not _allowed(maintenance.equipment):
        return redirect(url_for("dashboard.index"))
    values, error = service.parse_maintenance(request.form)
    error = error or service.validate_source(values, current_id=maintenance.id)
    if error:
        return _render(
            maintenance.equipment,
            maintenance=maintenance,
            source_inspection=maintenance.source_inspection,
            form_data=request.form,
            error=error,
        )
    service.save_maintenance(values, session["user"]["id"], maintenance)
    flash("修理対応を更新しました。", "success")
    return redirect(
        url_for("equipment.detail_get", equipment_id=maintenance.equipment_id)
    )
