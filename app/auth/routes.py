from flask import Blueprint, redirect, render_template, request, session, url_for
from sqlalchemy import select
from werkzeug.security import check_password_hash

from app.extensions import db
from app.forms import CsrfForm
from app.models import User


bp = Blueprint("auth", __name__)


@bp.get("/login")
def login_get():
    session.clear()
    return render_template(
        "login.html",
        form=CsrfForm(),
        info_message="社員番号とパスワードを入力してください。",
    )


@bp.post("/login")
def login_post():
    employee_no = request.form.get("employee_no", "").strip()
    password = request.form.get("password", "").strip()
    if not employee_no or not password:
        return render_template(
            "login.html",
            form=CsrfForm(),
            error_message="入力情報に誤りがあります。",
        )
    user = db.session.scalar(select(User).where(User.employee_no == employee_no))
    if user is None or not check_password_hash(user.password, password):
        return render_template(
            "login.html",
            form=CsrfForm(),
            error_message="社員番号またはパスワードに誤りがあります。",
        )
    session.clear()
    session["user"] = {
        "id": user.id,
        "last_name": user.last_name,
        "first_name": user.first_name,
        "name": user.full_name,
        "role": user.role,
    }
    return redirect(url_for("dashboard.index"))


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login_get"))
