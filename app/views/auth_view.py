from datetime import datetime, timezone
from flask import request, render_template, redirect, url_for, session
from flask_wtf import FlaskForm
from werkzeug.security import check_password_hash
from app.dao.user_dao import UserDao


class LoginForm(FlaskForm):
    """ログインフォーム（CSRFトークン生成用）"""
    pass


def login_get():
    """ログイン画面を表示する（GET /login）"""
    # 既存のセッション情報を破棄する
    session.clear()
    form = LoginForm()
    return render_template(
        "login.html",
        form=form,
        info_message="社員番号とパスワードを入力してください。",
    )


def login_post():
    """ログイン処理を行う（POST /login）"""
    try:
        form = LoginForm()

        # リクエストパラメータを取得する
        employee_no = request.form.get("employee_no", "").strip()
        password = request.form.get("password", "").strip()

        # 未入力チェック
        if not employee_no or not password:
            return render_template(
                "login.html",
                form=form,
                error_message="入力情報に誤りがあります。",
            )

        # DBから社員番号でユーザーを検索する（with文でDB接続を確実にクローズする）
        with UserDao() as dao:
            user = dao.find_by_employee_no(employee_no)

        # ユーザーが存在しない場合
        if user is None:
            return render_template(
                "login.html",
                form=form,
                error_message="社員番号またはパスワードに誤りがあります。",
            )

        # パスワードが一致しない場合
        if not check_password_hash(user.password, password):
            return render_template(
                "login.html",
                form=form,
                error_message="社員番号またはパスワードに誤りがあります。",
            )

        # 認証成功：ユーザー情報をセッションに登録してダッシュボードへ遷移する
        session["user"] = {
            "id":         user.id,
            "last_name":  user.last_name,
            "first_name": user.first_name,
            "name":       user.full_name,
            "role":       user.role,
            "base":       user.base,
        }
        # 最終操作時刻を記録する（セッションタイムアウト判定に使用）
        session["last_active"] = datetime.now(timezone.utc).timestamp()
        session.permanent = True
        return redirect(url_for("dashboard_get"))

    except Exception:
        return render_template("errors/500.html"), 500


def logout_get():
    """ログアウト処理を行う（GET /logout）"""
    # セッションを破棄してログイン画面へリダイレクトする
    session.clear()
    return redirect(url_for("login_get"))
