import os
from datetime import timedelta, datetime, timezone
from flask import Flask, render_template, redirect, url_for, session, request

# Flaskアプリを生成する
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

# セッションタイムアウト時間（無操作でログアウトするまでの分数）
# ※ 動作確認用に1分に設定している。本番では30程度に変更すること
SESSION_TIMEOUT_MINUTES = 30

app.config.update(
    WTF_CSRF_ENABLED=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
)

# ビュー関数をインポートしてルーティングを登録する
# （循環インポート回避のため app 生成後にインポートする）
from app.views import auth_view, dashboard_view, account_view, inspection_view, recycle_bin_view, notification_view
from app.views.equipment import register_routes as register_equipment_routes

app.add_url_rule("/login",     "login_get",     auth_view.login_get,          methods=["GET"])
app.add_url_rule("/login",     "login_post",    auth_view.login_post,         methods=["POST"])
app.add_url_rule("/logout",    "logout_get",    auth_view.logout_get,         methods=["GET"])
app.add_url_rule("/dashboard",          "dashboard_get",      dashboard_view.dashboard_get,         methods=["GET"])
app.add_url_rule("/api/notifications", "notifications_get",  notification_view.notifications_get,  methods=["GET"])

# 設備マスタのルートを登録する
register_equipment_routes(app)

# アカウント管理のルートを登録する
app.add_url_rule("/accounts",                "account_list_get",    account_view.account_list_get,    methods=["GET"])
app.add_url_rule("/accounts/new",            "account_new_get",     account_view.account_new_get,     methods=["GET"])
app.add_url_rule("/accounts/new",            "account_new_post",    account_view.account_new_post,    methods=["POST"])
app.add_url_rule("/accounts/<int:id>",       "account_detail_get",  account_view.account_detail_get,  methods=["GET"])
app.add_url_rule("/accounts/<int:id>",       "account_detail_post", account_view.account_detail_post, methods=["POST"])
app.add_url_rule("/accounts/<int:id>/delete",   "account_delete_post",   account_view.account_delete_post,   methods=["POST"])
app.add_url_rule("/accounts/<int:id>/password", "account_password_post", account_view.account_password_post, methods=["POST"])
# アカウント一括操作のルートを登録する
app.add_url_rule("/accounts/bulk-delete", "account_bulk_delete_post", account_view.account_bulk_delete_post, methods=["POST"])
app.add_url_rule("/accounts/bulk-edit",   "account_bulk_edit_post",   account_view.account_bulk_edit_post,   methods=["POST"])
app.add_url_rule("/accounts/bulk-revert", "account_bulk_revert_post", account_view.account_bulk_revert_post, methods=["POST"])

# 自分のパスワード変更（全ロール共通）
app.add_url_rule("/my/password", "my_password_get",  account_view.my_password_get,  methods=["GET"])
app.add_url_rule("/my/password", "my_password_post", account_view.my_password_post, methods=["POST"])

# 点検記録登録のルートを登録する
app.add_url_rule("/inspection/new", "inspection_new_get",  inspection_view.inspection_new_get,  methods=["GET"])
app.add_url_rule("/inspection/new", "inspection_new_post", inspection_view.inspection_new_post, methods=["POST"])

# ゴミ箱（データリサイクル）のルートを登録する
app.add_url_rule("/recycle-bin",                                  "recycle_bin_get",                          recycle_bin_view.recycle_bin_get,                          methods=["GET"])
app.add_url_rule("/recycle-bin/equipment/<int:id>/restore",       "recycle_bin_equipment_restore_post",       recycle_bin_view.recycle_bin_equipment_restore_post,       methods=["POST"])
app.add_url_rule("/recycle-bin/user/<int:id>/restore",            "recycle_bin_user_restore_post",            recycle_bin_view.recycle_bin_user_restore_post,            methods=["POST"])
# 物理削除（ROOT専用・取り消し不可）
app.add_url_rule("/recycle-bin/equipment/<int:id>/hard-delete",   "recycle_bin_equipment_hard_delete_post",   recycle_bin_view.recycle_bin_equipment_hard_delete_post,   methods=["POST"])
app.add_url_rule("/recycle-bin/user/<int:id>/hard-delete",        "recycle_bin_user_hard_delete_post",        recycle_bin_view.recycle_bin_user_hard_delete_post,        methods=["POST"])
# 一括操作（複数選択して一括復元・一括完全削除）
app.add_url_rule("/recycle-bin/equipment/bulk-restore",           "recycle_bin_equipment_bulk_restore_post",     recycle_bin_view.recycle_bin_equipment_bulk_restore_post,     methods=["POST"])
app.add_url_rule("/recycle-bin/user/bulk-restore",                "recycle_bin_user_bulk_restore_post",          recycle_bin_view.recycle_bin_user_bulk_restore_post,          methods=["POST"])
app.add_url_rule("/recycle-bin/equipment/bulk-hard-delete",       "recycle_bin_equipment_bulk_hard_delete_post", recycle_bin_view.recycle_bin_equipment_bulk_hard_delete_post, methods=["POST"])
app.add_url_rule("/recycle-bin/user/bulk-hard-delete",            "recycle_bin_user_bulk_hard_delete_post",      recycle_bin_view.recycle_bin_user_bulk_hard_delete_post,      methods=["POST"])

@app.before_request
def check_session_timeout():
    """リクエストのたびに無操作時間をチェックし、タイムアウトしていたらログアウトさせる"""
    # ログイン画面と静的ファイルはチェック不要
    if request.endpoint in ("login_get", "login_post", "static"):
        return

    # セッションにユーザー情報がなければログイン画面へ
    if "user" not in session:
        return redirect(url_for("login_get"))

    # 最終操作時刻を取得する
    last_active = session.get("last_active")
    if last_active:
        # 現在時刻との差分（秒）を計算する
        elapsed_seconds = datetime.now(timezone.utc).timestamp() - last_active
        if elapsed_seconds > SESSION_TIMEOUT_MINUTES * 60:
            # タイムアウト：セッションを破棄して中間ページを表示する
            session.clear()
            return render_template("session_timeout.html")

    # 最終操作時刻を更新する
    session["last_active"] = datetime.now(timezone.utc).timestamp()


# トップページ（/）にアクセスしたらログイン画面にリダイレクトする
@app.route("/")
def index():
    return redirect(url_for("login_get"))


@app.errorhandler(404)
def not_found(_error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def internal_error(_error):
    app.logger.error("500 error: %s", _error)
    return render_template("errors/500.html"), 500
