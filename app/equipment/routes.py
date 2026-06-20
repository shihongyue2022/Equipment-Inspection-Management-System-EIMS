from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from app.common.auth import admin_required, login_required
from app.forms import CsrfForm
from app.services import equipment as service
from app.services import maintenance as maintenance_service


bp = Blueprint("equipment", __name__, url_prefix="/equipment")


def _render_form(template, **context):
    return render_template(template, form=CsrfForm(), **context)


@bp.get("")
@admin_required
def list_get():
    keyword = request.args.get("q", "").strip() or None
    selected_base = request.args.get("base") or None
    selected_type = request.args.get("equipment_type") or None
    selected_manufacturer = request.args.get("manufacturer") or None
    selected_engineer = request.args.get("engineer_id", type=int)
    selected_deadline = request.args.get("deadline") or None
    selected_sort = request.args.get("sort_by", "next_inspection")
    if selected_sort not in service.MANAGEMENT_SORT_OPTIONS:
        selected_sort = "next_inspection"
    selected_order = request.args.get("sort_order", "asc")
    if selected_order not in {"asc", "desc"}:
        selected_order = "asc"

    def filters():
        return {
            "keyword": keyword,
            "base": selected_base,
            "equipment_type": selected_type,
            "manufacturer": selected_manufacturer,
            "engineer_id": selected_engineer,
            "deadline": selected_deadline,
        }

    filter_options = service.equipment_management_filter_options(**filters())
    valid = {
        "base": {item["value"] for item in filter_options["bases"]},
        "equipment_type": {
            item["value"] for item in filter_options["equipment_types"]
        },
        "manufacturer": {
            item["value"] for item in filter_options["manufacturers"]
        },
        "engineer_id": {item["id"] for item in filter_options["engineers"]},
        "deadline": {item["value"] for item in filter_options["deadlines"]},
    }
    normalized = False
    if selected_base is not None and selected_base not in valid["base"]:
        selected_base = None
        normalized = True
    if selected_type is not None and selected_type not in valid["equipment_type"]:
        selected_type = None
        normalized = True
    if (
        selected_manufacturer is not None
        and selected_manufacturer not in valid["manufacturer"]
    ):
        selected_manufacturer = None
        normalized = True
    if selected_engineer is not None and selected_engineer not in valid["engineer_id"]:
        selected_engineer = None
        normalized = True
    if selected_deadline is not None and selected_deadline not in valid["deadline"]:
        selected_deadline = None
        normalized = True
    if normalized:
        filter_options = service.equipment_management_filter_options(**filters())

    page = max(request.args.get("page", 1, type=int), 1)
    pagination = service.search_equipment(
        page=page,
        per_page=50,
        sort_by=selected_sort,
        sort_order=selected_order,
        **filters(),
    )
    return render_template(
        "equipment/list.html",
        equipment_list=pagination.items,
        pagination=pagination,
        engineer_list=service.engineers(),
        filter_options=filter_options,
        keyword=keyword,
        selected_base=selected_base,
        selected_type=selected_type,
        selected_manufacturer=selected_manufacturer,
        selected_engineer=selected_engineer,
        selected_deadline=selected_deadline,
        sort_options=service.MANAGEMENT_SORT_OPTIONS,
        selected_sort=selected_sort,
        selected_order=selected_order,
        active_filter_count=sum(
            value is not None
            for value in (
                keyword,
                selected_base,
                selected_type,
                selected_manufacturer,
                selected_engineer,
                selected_deadline,
            )
        ),
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
        timeline=maintenance_service.equipment_timeline(equipment),
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

