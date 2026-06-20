from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from app.common.auth import admin_required, login_required
from app.forms import CsrfForm
from app.services import equipment as service


bp = Blueprint("equipment", __name__, url_prefix="/equipment")


def _render_form(template, **context):
    return render_template(template, form=CsrfForm(), **context)


@bp.get("")
@admin_required
def list_get():
    return render_template(
        "equipment/list.html",
        equipment_list=service.list_equipment(),
        engineer_list=service.engineers(),
        form=CsrfForm(),
    )


@bp.get("/new")
@admin_required
def new_get():
    return _render_form(
        "equipment/new.html",
        engineer_list=service.engineers(),
        form_data=None,
        error_message=None,
    )


@bp.post("/new")
@admin_required
def new_post():
    values, error = service.parse_equipment(request.form)
    if error:
        return _render_form(
            "equipment/new.html",
            engineer_list=service.engineers(),
            form_data=request.form,
            error_message=error,
        )
    equipment = service.create_equipment(values)
    flash(f"設備「{equipment.name}」を登録しました。", "success")
    return redirect(url_for("equipment.list_get"))


@bp.get("/<int:equipment_id>")
@login_required
def detail_get(equipment_id):
    equipment = service.get_equipment(equipment_id)
    if equipment is None:
        abort(404)
    user = session["user"]
    if user["role"] == "engineer" and equipment.assigned_user_id != user["id"]:
        flash("担当外の設備にはアクセスできません。", "danger")
        return redirect(url_for("dashboard.index"))
    return render_template(
        "equipment/detail.html",
        equipment=equipment,
        inspection_records=equipment.inspections,
        back_url=request.referrer or url_for("dashboard.index"),
    )


@bp.get("/<int:equipment_id>/edit")
@admin_required
def edit_get(equipment_id):
    equipment = service.get_equipment(equipment_id)
    if equipment is None:
        abort(404)
    return _render_form(
        "equipment/edit.html",
        equipment=equipment,
        engineer_list=service.engineers(),
        error_message=None,
    )


@bp.post("/<int:equipment_id>/edit")
@admin_required
def edit_post(equipment_id):
    equipment = service.get_equipment(equipment_id)
    if equipment is None:
        abort(404)
    values, error = service.parse_equipment(request.form)
    if error:
        return _render_form(
            "equipment/edit.html",
            equipment=equipment,
            engineer_list=service.engineers(),
            error_message=error,
        )
    service.update_equipment(equipment, values)
    flash(f"設備「{equipment.name}」を更新しました。", "success")
    return redirect(url_for("equipment.list_get"))


@bp.post("/<int:equipment_id>/delete")
@admin_required
def delete_post(equipment_id):
    equipment = service.get_equipment(equipment_id)
    if equipment is None:
        abort(404)
    try:
        service.delete_equipment(equipment)
        flash(f"設備「{equipment.name}」を削除しました。", "success")
    except IntegrityError:
        service.db.session.rollback()
        flash("点検記録が登録されている設備は削除できません。", "danger")
    return redirect(url_for("equipment.list_get"))


@bp.post("/<int:equipment_id>/assign")
@admin_required
def assign_post(equipment_id):
    equipment = service.get_equipment(equipment_id)
    if equipment is None:
        abort(404)
    raw_id = request.form.get("assigned_user_id", "").strip()
    try:
        assigned_id = int(raw_id) if raw_id else None
    except ValueError:
        flash("担当者が正しくありません。", "danger")
        return redirect(url_for("equipment.list_get"))
    service.assign_equipment(equipment, assigned_id)
    flash("担当者を変更しました。", "success")
    return redirect(url_for("equipment.list_get"))

