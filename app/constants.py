# アプリ全体で使用する定数を一箇所にまとめたファイル。
# 文字列リテラルを直接書かず、ここで定義した定数を import して使うこと。

# ---- ロール定数 ----
ROLE_ROOT = "root"           # システム管理者（最上位権限）
ROLE_ADMIN = "admin"         # 管理者
ROLE_ENGINEER = "engineer"   # フィールドエンジニア（FE）

# 管理者以上のロール一覧（admin と root の両方を含む）
ADMIN_ROLES = [ROLE_ADMIN, ROLE_ROOT]

# ---- 点検ステータス定数 ----
STATUS_NORMAL = "normal"   # 異常なし
STATUS_WATCH = "watch"     # 要観察
STATUS_REPAIR = "repair"   # 要修理

# ---- 期限ステータス定数 ----
DEADLINE_OVERDUE = "overdue"  # 期限超過
DEADLINE_SOON = "soon"        # まもなく（7日以内）
DEADLINE_NORMAL = "normal"    # 正常（7日超）
