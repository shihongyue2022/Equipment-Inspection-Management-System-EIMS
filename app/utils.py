from datetime import date
from functools import wraps

from flask import session, redirect, url_for, flash

from app.constants import ADMIN_ROLES


def login_required(f):
    """ログイン必須デコレーター。
    未ログインのままアクセスした場合はログイン画面へリダイレクトする。
    使い方: ビュー関数の直上に @login_required を付ける。
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # セッションにユーザー情報がなければログイン画面へリダイレクトする
        if 'user' not in session:
            return redirect(url_for('login_get'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """管理者以上必須デコレーター。
    admin・root 以外のロールでアクセスした場合はダッシュボードへリダイレクトする。
    使い方: ビュー関数の直上に @admin_required を付ける。
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 未ログインの場合はログイン画面へリダイレクトする
        if 'user' not in session:
            return redirect(url_for('login_get'))
        # ロールが admin・root 以外の場合はダッシュボードへリダイレクトする
        if session['user']['role'] not in ADMIN_ROLES:
            flash('この操作は管理者のみ実行できます。', 'danger')
            return redirect(url_for('dashboard_get'))
        return f(*args, **kwargs)
    return decorated_function


def require_login():
    """未ログインの場合はリダイレクト先を返す。問題なければ None を返す。
    ※ 新規実装では @login_required デコレーターを使うこと。
    """
    if 'user' not in session:
        return redirect(url_for('login_get'))
    return None


def require_admin():
    """管理者以外の場合はリダイレクト先を返す。問題なければ None を返す。
    ※ 新規実装では @admin_required デコレーターを使うこと。
    """
    if 'user' not in session:
        return redirect(url_for('login_get'))
    if session['user']['role'] not in ADMIN_ROLES:
        flash('この操作は管理者のみ実行できます。', 'danger')
        return redirect(url_for('dashboard_get'))
    return None


def get_deadline_status(next_inspection_date):
    """次回点検日から期限ステータスを算出する。

    戻り値:
        'overdue' : 超過
        'soon'    : まもなく（7日以内）
        'normal'  : 正常
        None      : 未点検（next_inspection_date が NULL）
    """
    if next_inspection_date is None:
        return None
    remaining_days = (next_inspection_date - date.today()).days
    if remaining_days < 0:
        return "overdue"
    if remaining_days <= 7:
        return "soon"
    return "normal"


def is_valid_email(email):
    """メールアドレスの簡易形式チェック。@ が含まれていれば True を返す。"""
    return "@" in email
