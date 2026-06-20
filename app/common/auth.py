from functools import wraps

from flask import flash, redirect, session, url_for


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("auth.login_get"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = session.get("user")
        if not user:
            return redirect(url_for("auth.login_get"))
        if user["role"] not in {"root", "admin"}:
            flash("この操作は管理者のみ実行できます。", "danger")
            return redirect(url_for("dashboard.index"))
        return view(*args, **kwargs)

    return wrapped

