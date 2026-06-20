from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from app.common.auth import admin_required, login_required
from app.extensions import db
from app.forms import CsrfForm
from app.models import User
from app.services import accounts as service
from app.services.equipment import list_equipment


bp = Blueprint("accounts", __name__)


def _target(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    return user


def _detail(user, *, error=None, success=None):
    return render_template(
        "account/detail.html",
        user=user,
        assigned_equipment_list=list_equipment(user_id=user.id),
        form=CsrfForm(),
        error_message=error,
        password_error=None,
        password_success=success,
    )


def _role_error(target, requested_role):
    login_role = session["user"]["role"]
    if requested_role == "root" and target.role != "root":
        return "root権限を他のアカウントに付与することはできません。"
    if login_role == "admin" and target.role in {"root", "admin"}:
        return "このアカウントは編集できません。"
    if login_role == "admin" and requested_role != "engineer":
        return "このロールは指定できません。"
    return None


@bp.get("/accounts")
@admin_required
def list_get():
    return render_template("account/list.html", user_list=service.users())


@bp.get("/accounts/new")
@admin_required
def new_get():
    return render_template(
        "account/new.html",
        form=CsrfForm(),
        form_data=None,
        error_message=None,
    )


@bp.post("/accounts/new")
@admin_required
def new_post():
    values, error = service.parse_user(request.form)
    if not error:
        role = values["role"]
        if role == "root" or (session["user"]["role"] == "admin" and role != "engineer"):
            error = "このロールは指定できません。"
    if not error:
        error = service.duplicate_error(values)
    if error:
        return render_template(
            "account/new.html",
            form=CsrfForm(),
            form_data=request.form,
            error_message=error,
        )
    service.create_user(values)
    return redirect(url_for("accounts.list_get"))


@bp.get("/accounts/<int:user_id>")
@admin_required
def detail_get(user_id):
    return _detail(_target(user_id))


@bp.post("/accounts/<int:user_id>")
@admin_required
def detail_post(user_id):
    user = _target(user_id)
    values, error = service.parse_user(request.form, editing=True)
    if not error:
        error = _role_error(user, values["role"])
    if not error:
        error = service.duplicate_error(values, exclude_id=user_id)
    if error:
        return _detail(user, error=error)
    service.update_user(user, values)
    return redirect(url_for("accounts.list_get"))


@bp.post("/accounts/<int:user_id>/password")
@admin_required
def password_post(user_id):
    user = _target(user_id)
    if session["user"]["role"] == "admin" and user.role == "root":
        return _detail(user, error="rootのパスワードは変更できません。")
    current = request.form.get("current_password", "").strip()
    new = request.form.get("new_password", "").strip()
    confirm = request.form.get("confirm_password", "").strip()
    if not new or not confirm:
        return _detail(user, error="新しいパスワードを2回入力してください。")
    if new != confirm:
        return _detail(user, error="新しいパスワードが一致しません。")
    if session["user"]["id"] == user_id:
        if not current:
            return _detail(user, error="現在のパスワードを入力してください。")
        if not check_password_hash(user.password, current):
            return _detail(user, error="現在のパスワードが正しくありません。")
    service.change_password(user, new)
    return _detail(user, success="パスワードを変更しました。")


@bp.post("/accounts/<int:user_id>/delete")
@admin_required
def delete_post(user_id):
    user = _target(user_id)
    if session["user"]["role"] == "admin" and user.role != "engineer":
        return redirect(url_for("accounts.list_get"))
    count = service.inspection_count(user_id)
    if count:
        return _detail(
            user,
            error=(
                f"このアカウントには点検記録が {count} 件あるため削除できません。"
                "先に点検記録を削除してください。"
            ),
        )
    service.delete_user(user)
    return redirect(url_for("accounts.list_get"))


@bp.get("/my/password")
@login_required
def my_password_get():
    return render_template(
        "account/my_password.html",
        form=CsrfForm(),
        error_message=None,
        success_message=None,
    )


@bp.post("/my/password")
@login_required
def my_password_post():
    user = db.session.get(User, session["user"]["id"])
    if user is None:
        return redirect(url_for("auth.login_get"))
    current = request.form.get("current_password", "").strip()
    new = request.form.get("new_password", "").strip()
    confirm = request.form.get("confirm_password", "").strip()
    error = None
    if not current:
        error = "現在のパスワードを入力してください。"
    elif not new or not confirm:
        error = "新しいパスワードを2回入力してください。"
    elif new != confirm:
        error = "新しいパスワードが一致しません。"
    elif not check_password_hash(user.password, current):
        error = "現在のパスワードが正しくありません。"
    if error:
        return render_template(
            "account/my_password.html",
            form=CsrfForm(),
            error_message=error,
            success_message=None,
        )
    service.change_password(user, new)
    return render_template(
        "account/my_password.html",
        form=CsrfForm(),
        error_message=None,
        success_message="パスワードを変更しました。",
    )

