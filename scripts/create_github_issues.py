#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_github_issues.py

GitHub Enterprise に課題管理表・バックログの Issue を一括作成するスクリプト。
ソースファイル（docs/）は変更しない。

使い方:
    python scripts/create_github_issues.py <PERSONAL_ACCESS_TOKEN>

事前準備:
    GitHub Enterprise の Settings > Developer settings > Personal access tokens で
    repo スコープのトークンを発行しておく。

注意:
    - 既存の Issue は変更しない（重複して作成されることに注意）
    - 一度実行してから再実行すると Issue が二重に作成される
    - 初回実行時のみ使用すること
"""

import sys
import json
import re
import os
import time
import urllib.request
import urllib.error

# ──────────────────────────────────────────────
# 設定
# ──────────────────────────────────────────────
GHE_BASE    = "https://akkodis-jp.ghe.com/api/v3"
REPO_OWNER  = "akkodis-seminar"
REPO_NAME   = "E_T.ECH"
DOCS_DIR    = os.path.join(os.path.dirname(__file__), "..", "docs")

# API リクエスト間の待機秒数（レートリミット対策）
SLEEP_SEC = 0.8


# ──────────────────────────────────────────────
# ラベル定義
# ──────────────────────────────────────────────
LABELS = [
    {"name": "bug",         "color": "d73a4a", "description": "バグ・不具合"},
    {"name": "enhancement", "color": "a2eeef", "description": "機能改善・新機能"},
    {"name": "テスト",       "color": "0075ca", "description": "pytestおよび手動テスト"},
    {"name": "ドキュメント",  "color": "e4e669", "description": "設計書・ドキュメント"},
    {"name": "環境",         "color": "d4c5f9", "description": "開発環境・インフラ設定"},
    {"name": "実装",         "color": "bfd4f2", "description": "機能実装タスク"},
    {"name": "sprint0",     "color": "f9d0c4", "description": "Sprint 0（設計フェーズ）"},
    {"name": "sprint1",     "color": "fef2c0", "description": "Sprint 1（実装フェーズ①）"},
    {"name": "sprint2",     "color": "c2e0c6", "description": "Sprint 2（実装フェーズ②）"},
    {"name": "sprint3",     "color": "bfd4f2", "description": "Sprint 3（最終調整フェーズ）"},
    {"name": "対応済",       "color": "0e8a16", "description": "対応完了"},
    {"name": "未対応",       "color": "e11d48", "description": "未対応・要調査"},
]


# ──────────────────────────────────────────────
# マイルストーン定義
# ──────────────────────────────────────────────
MILESTONES = [
    {
        "title": "Sprint 0",
        "description": "設計フェーズ（2026-06-09 〜 06-12）",
        "due_on": "2026-06-12T23:59:59Z",
    },
    {
        "title": "Sprint 1",
        "description": "実装フェーズ①（2026-06-15 〜 06-18）",
        "due_on": "2026-06-18T23:59:59Z",
    },
    {
        "title": "Sprint 2",
        "description": "実装フェーズ②（2026-06-19 〜 06-24）",
        "due_on": "2026-06-24T23:59:59Z",
    },
    {
        "title": "Sprint 3",
        "description": "最終調整フェーズ（2026-06-25 〜 06-30）",
        "due_on": "2026-06-30T23:59:59Z",
    },
]


# ──────────────────────────────────────────────
# バックログ Issues（ハードコード）
# Sprint 0 〜 Sprint 3 の主要タスク
# ──────────────────────────────────────────────
BACKLOG_ISSUES = [

    # ── Sprint 0（設計フェーズ） ──
    {
        "title": "[D-00] 要件定義書の作成",
        "labels": ["ドキュメント", "sprint0", "対応済"],
        "milestone": "Sprint 0",
        "body": (
            "**スプリント：** Sprint 0（2026-06-09 〜 06-12）\n"
            "**種別：** ドキュメント\n"
            "**ファイル：** `docs/01_要件定義書.md`\n\n"
            "### タスク内容\n"
            "- 背景・課題・プロジェクト目的の整理\n"
            "- スコープIN/OUTの定義\n"
            "- 全体スケジュール・スプリント計画の策定\n"
            "- 機能一覧・非機能要件の定義\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/10_バックログ_Sprint0_Sprint1.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-11"
        ),
    },
    {
        "title": "[D-01] 基本設計書の作成",
        "labels": ["ドキュメント", "sprint0", "対応済"],
        "milestone": "Sprint 0",
        "body": (
            "**スプリント：** Sprint 0（2026-06-09 〜 06-12）\n"
            "**種別：** 設計\n"
            "**ファイル：** `docs/03_基本設計書.md`\n\n"
            "### タスク内容\n"
            "- 画面一覧の定義\n"
            "- 画面遷移フローの設計\n"
            "- URL設計（ルーティング定義）\n"
            "- ロール別アクセス制御の設計\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/10_バックログ_Sprint0_Sprint1.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-11"
        ),
    },
    {
        "title": "[D-02] 詳細設計書の作成",
        "labels": ["ドキュメント", "sprint0", "対応済"],
        "milestone": "Sprint 0",
        "body": (
            "**スプリント：** Sprint 0（2026-06-09 〜 06-12）\n"
            "**種別：** 設計\n"
            "**ファイル：** `docs/04_詳細設計書.md`\n\n"
            "### タスク内容\n"
            "- 各画面の入出力項目設計\n"
            "- View関数（エンドポイント）設計\n"
            "- DAOクラス設計\n"
            "- DTOクラス設計\n"
            "- バリデーション仕様の定義\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/10_バックログ_Sprint0_Sprint1.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-11"
        ),
    },
    {
        "title": "[D-03] データベース定義書の作成",
        "labels": ["ドキュメント", "sprint0", "対応済"],
        "milestone": "Sprint 0",
        "body": (
            "**スプリント：** Sprint 0（2026-06-09 〜 06-12）\n"
            "**種別：** 設計\n"
            "**ファイル：** `docs/05_データベース定義書.md`\n\n"
            "### タスク内容\n"
            "- `employee` テーブル定義\n"
            "- `equipment` テーブル定義\n"
            "- `inspection_records` テーブル定義\n"
            "- ER図の作成\n"
            "- インデックス設計\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/10_バックログ_Sprint0_Sprint1.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-11"
        ),
    },
    {
        "title": "[D-04] 開発環境のセットアップ",
        "labels": ["環境", "sprint0"],
        "milestone": "Sprint 0",
        "body": (
            "**スプリント：** Sprint 0（2026-06-09 〜 06-12）\n"
            "**種別：** 環境\n"
            "**参考：** `README.md`\n\n"
            "### タスク内容\n"
            "- Python仮想環境（venv）の構築\n"
            "- `requirements.txt` の作成・インストール\n"
            "- Flaskアプリの起動確認（`flask run`）\n"
            "- MySQLへの接続確認（`inspection_db`）\n"
            "- チーム全員の動作確認\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/10_バックログ_Sprint0_Sprint1.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-11"
        ),
    },
    {
        "title": "[D-05] GitHubリポジトリ・ブランチ戦略の整備",
        "labels": ["環境", "sprint0", "対応済"],
        "milestone": "Sprint 0",
        "body": (
            "**スプリント：** Sprint 0（2026-06-09 〜 06-12）\n"
            "**種別：** 環境\n"
            "**ファイル：** `CLAUDE.md` / `docs/Gitチーム規約.md`\n\n"
            "### タスク内容\n"
            "- リポジトリの作成・初期化\n"
            "- `main` / `develop` ブランチの整備\n"
            "- `CLAUDE.md` の作成\n"
            "- チームへのブランチルール共有\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/10_バックログ_Sprint0_Sprint1.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-11"
        ),
    },

    # ── Sprint 1（実装フェーズ①） ──
    {
        "title": "[F-01] ログイン・ログアウト機能の実装",
        "labels": ["実装", "sprint1", "対応済"],
        "milestone": "Sprint 1",
        "body": (
            "**スプリント：** Sprint 1（2026-06-15 〜 06-18）\n"
            "**機能ID：** F-01\n"
            "**担当ロール：** 全ユーザー\n\n"
            "### タスク内容\n"
            "- 社員番号＋パスワードによる認証\n"
            "- `werkzeug.security.check_password_hash` で照合\n"
            "- セッション管理（Flask server-side session）\n"
            "- ログアウト後のセッションクリア\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/10_バックログ_Sprint0_Sprint1.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-11"
        ),
    },
    {
        "title": "[F-02] ロール制御の実装",
        "labels": ["実装", "sprint1", "対応済"],
        "milestone": "Sprint 1",
        "body": (
            "**スプリント：** Sprint 1（2026-06-15 〜 06-18）\n"
            "**機能ID：** F-02\n"
            "**担当ロール：** 全ユーザー\n\n"
            "### タスク内容\n"
            "- admin / engineer / root のロール分岐\n"
            "- View関数でのアクセス制御（`@admin_required` デコレータ）\n"
            "- テンプレートでのロール別表示切り替え\n"
            "- FEは自分の担当設備のみアクセス可能\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/10_バックログ_Sprint0_Sprint1.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-11"
        ),
    },
    {
        "title": "[F-03] 点検記録登録機能の実装",
        "labels": ["実装", "sprint1", "対応済"],
        "milestone": "Sprint 1",
        "body": (
            "**スプリント：** Sprint 1（2026-06-15 〜 06-18）\n"
            "**機能ID：** F-03\n"
            "**担当ロール：** FE（engineer）\n\n"
            "### タスク内容\n"
            "- FEが担当設備の点検結果を登録するフォーム\n"
            "- ステータス選択（normal / watch / repair）\n"
            "- 点検日・備考の入力\n"
            "- 登録後に `next_inspection_date` を自動更新\n"
            "- CSRF対策（Flask-WTF）\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/10_バックログ_Sprint0_Sprint1.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-11"
        ),
    },
    {
        "title": "[F-04] ユーザー登録・管理機能の実装",
        "labels": ["実装", "sprint1", "対応済"],
        "milestone": "Sprint 1",
        "body": (
            "**スプリント：** Sprint 1（2026-06-15 〜 06-18）\n"
            "**機能ID：** F-04\n"
            "**担当ロール：** root・admin\n\n"
            "### タスク内容\n"
            "- アカウント一覧・詳細・登録・編集・削除\n"
            "- パスワードは `werkzeug.security.generate_password_hash` でハッシュ化\n"
            "- root は admin が操作できない（保護）\n"
            "- ロール選択から ROOT を除外\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/10_バックログ_Sprint0_Sprint1.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-11"
        ),
    },

    # ── Sprint 2（実装フェーズ②）── 手動テスト
    {
        "title": "[A-01] 手動テスト: ログイン・ログアウト",
        "labels": ["テスト", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** 手動テスト\n"
            "**担当：** 担当①\n\n"
            "### テスト内容\n"
            "- 正常ログイン（admin / engineer / root）\n"
            "- 不正ログイン（社員番号誤り / パスワード誤り）\n"
            "- ログアウト後のセッション無効確認\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[A-02] 手動テスト: ロール制御",
        "labels": ["テスト", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** 手動テスト\n"
            "**担当：** 担当①\n\n"
            "### テスト内容\n"
            "- admin が admin 専用画面にアクセスできること\n"
            "- engineer が admin 専用画面にアクセスできないこと\n"
            "- engineer が他FEの設備にアクセスできないこと\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[A-03] 手動テスト: ダッシュボード",
        "labels": ["テスト", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** 手動テスト\n"
            "**担当：** 担当①\n\n"
            "### テスト内容\n"
            "- 集計カード（超過・まもなく・要修理・未割当）の件数確認\n"
            "- 拠点フィルタの動作確認\n"
            "- 担当者別負荷テーブルの表示確認\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[A-04] 手動テスト: 設備CRUD",
        "labels": ["テスト", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** 手動テスト\n"
            "**担当：** 担当①\n\n"
            "### テスト内容\n"
            "- 設備一覧表示・検索・フィルター\n"
            "- 設備登録・編集・削除\n"
            "- 担当エンジニア割り当て\n"
            "- 削除後のゴミ箱移動確認\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[A-05] 手動テスト: 設備詳細・点検記録",
        "labels": ["テスト", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** 手動テスト\n"
            "**担当：** 担当①\n\n"
            "### テスト内容\n"
            "- 設備詳細画面のチャート・指標カード表示\n"
            "- 点検記録一覧のフィルター・ソート・ページネーション\n"
            "- 点検記録の登録・次回点検日自動更新\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[A-06] 手動テスト: アカウント管理",
        "labels": ["テスト", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** 手動テスト\n"
            "**担当：** 担当①\n\n"
            "### テスト内容\n"
            "- アカウント一覧・詳細・登録・編集\n"
            "- 論理削除・ゴミ箱からの復元\n"
            "- root アカウントの操作禁止確認\n"
            "- 自己削除禁止確認\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[A-07] 手動テスト: パスワード変更",
        "labels": ["テスト", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** 手動テスト\n"
            "**担当：** 担当①\n\n"
            "### テスト内容\n"
            "- 全ロールからパスワード変更画面にアクセスできること\n"
            "- 現在のパスワード入力誤りで拒否されること\n"
            "- 新パスワードと確認用パスワードの不一致で拒否されること\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },

    # ── Sprint 2 ── pytest
    {
        "title": "[B-01] pytest: test_utils.py 境界値テスト",
        "labels": ["テスト", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** pytest\n"
            "**ファイル：** `tests/test_utils.py`\n"
            "**担当：** 担当④\n\n"
            "### テスト内容\n"
            "- `get_deadline_status()` の境界値テスト7件\n"
            "- overdue / soon / normal / None（未点検）の各ケース\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[B-02] pytest: test_auth_view.py 認証テスト",
        "labels": ["テスト", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** pytest\n"
            "**ファイル：** `tests/test_auth_view.py`\n"
            "**担当：** 担当②\n\n"
            "### テスト内容\n"
            "- ログイン成功・セッション設定確認（B-02-01〜04）\n"
            "- ログイン失敗ケース（社員番号誤り・パスワード誤り）（B-02-05〜11）\n"
            "- ログアウトのセッションクリア確認\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[B-03] pytest: test_equipment_view.py 設備テスト",
        "labels": ["テスト", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** pytest\n"
            "**ファイル：** `tests/test_equipment_view.py`\n"
            "**担当：** 担当③\n\n"
            "### テスト内容\n"
            "- 設備一覧表示・権限・フォーム表示（B-03-01〜03）\n"
            "- 正常登録・バリデーション（B-03-04〜09）\n"
            "- 編集・削除・FK制約（B-03-10〜14）\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[B-04] pytest: test_inspection_view.py 点検記録テスト",
        "labels": ["テスト", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** pytest\n"
            "**ファイル：** `tests/test_inspection_view.py`\n"
            "**担当：** 担当④\n\n"
            "### テスト内容\n"
            "- FE担当制御・正常登録（B-04-01〜04）\n"
            "- バリデーション・エラーケース（B-04-05〜07）\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[B-05] pytest: test_dashboard_view.py ダッシュボードテスト",
        "labels": ["テスト", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** pytest\n"
            "**ファイル：** `tests/test_dashboard_view.py`\n"
            "**担当：** 担当⑤\n\n"
            "### テスト内容\n"
            "- 未ログイン・ロール別アクセス（B-05-01〜03）\n"
            "- 拠点フィルタ・集計カウント（B-05-04〜08）\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[B-06] pytest: test_password_change_view.py パスワード変更テスト",
        "labels": ["テスト", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** pytest\n"
            "**ファイル：** `tests/test_password_change_view.py`\n"
            "**担当：** 担当②または⑤\n\n"
            "### テスト内容\n"
            "- 全ロールからアクセス可能確認\n"
            "- 現在パスワード誤りで拒否\n"
            "- 新パスワード不一致で拒否\n"
            "- 正常変更確認\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[B-07] 白箱テスト: DAO・DTO・ユーティリティ単体テスト",
        "labels": ["テスト", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** pytest（白箱テスト）\n"
            "**担当：** 担当③⑤\n\n"
            "### テスト内容\n"
            "- DAO層の各メソッド単体テスト\n"
            "- DTOクラスの `@property` / `@setter` 動作確認\n"
            "- `utils.py` のユーティリティ関数テスト\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },

    # ── Sprint 2 ── 設計書修正
    {
        "title": "[C-01] 設計書修正: 詳細設計書（04）の更新",
        "labels": ["ドキュメント", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** ドキュメント\n"
            "**ファイル：** `docs/04_詳細設計書.md`\n"
            "**担当：** 担当⑥\n\n"
            "### タスク内容\n"
            "- 設備一覧・追加・編集・削除 View 関数の設計追記\n"
            "- ダッシュボード View 関数の設計更新（拠点フィルタ・集計ロジック）\n"
            "- パスワード変更 View 関数の設計追記\n"
            "- DAO メソッド一覧を現コードに合わせて更新\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[C-02] 設計書修正: 基本設計書（03）の更新",
        "labels": ["ドキュメント", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** ドキュメント\n"
            "**ファイル：** `docs/03_基本設計書.md`\n"
            "**担当：** 担当⑥\n\n"
            "### タスク内容\n"
            "- 追加・変更された画面・URLのリスト更新\n"
            "- ロール別アクセス制御の最新化\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[C-03] 設計書修正: データベース定義書（05）の更新",
        "labels": ["ドキュメント", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** ドキュメント\n"
            "**ファイル：** `docs/05_データベース定義書.md`\n"
            "**担当：** 担当⑥\n\n"
            "### タスク内容\n"
            "- 追加されたカラム・インデックスの反映\n"
            "- audit_log テーブル等の追記\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[C-04] 設計書修正: 要件定義書（01）の更新",
        "labels": ["ドキュメント", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**種別：** ドキュメント\n"
            "**ファイル：** `docs/01_要件定義書.md`\n"
            "**担当：** 担当⑥\n\n"
            "### タスク内容\n"
            "- Sprint 2 で追加・変更された機能の反映\n"
            "- スコープ・スプリント計画のアップデート\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },

    # ── Sprint 2 ── 新機能実装
    {
        "title": "[F-05] 検索フィルター・絞り込み機能の実装",
        "labels": ["実装", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**機能ID：** F-05\n\n"
            "### タスク内容\n"
            "- 設備一覧に検索バーとフィルター機能を追加\n"
            "- 設備名・種別・担当者・拠点などで絞り込み可能にする\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[F-06] 未割当担当者のUIの改善（ダッシュボード）",
        "labels": ["実装", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**機能ID：** F-06\n\n"
            "### タスク内容\n"
            "- ダッシュボードの未割当担当者表示UI改善\n"
            "- 先週比バッジの追加\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[F-07] 社員番号の変更不可化",
        "labels": ["実装", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**機能ID：** F-07\n\n"
            "### タスク内容\n"
            "- 社員番号（ログインID）の編集権限を root のみに制限\n"
            "- 編集フォームで root 以外は社員番号フィールドを読み取り専用にする\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },
    {
        "title": "[F-08] ロール別の担当者入力方式の変更",
        "labels": ["実装", "sprint2", "対応済"],
        "milestone": "Sprint 2",
        "body": (
            "**スプリント：** Sprint 2（2026-06-19 〜 06-24）\n"
            "**機能ID：** F-08\n\n"
            "### タスク内容\n"
            "- 設備編集画面での担当エンジニア選択を拠点フィルターで絞り込み可能にする\n"
            "- ロール別に入力方式を切り替える\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/11_バックログ_Sprint2.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-19"
        ),
    },

    # ── Sprint 3（最終調整フェーズ） ──
    {
        "title": "[Sprint3-A] 手動テスト完了レポート（新機能016〜022）",
        "labels": ["テスト", "sprint3"],
        "milestone": "Sprint 3",
        "body": (
            "**スプリント：** Sprint 3（2026-06-25 〜 06-29）\n"
            "**種別：** 手動テスト\n"
            "**担当：** 担当①\n\n"
            "### テスト内容\n"
            "- Sprint 3 で追加された新機能（016〜022）の全39件の手動テスト\n"
            "- バグ発見時は `06_課題管理表.md` に記録する\n"
            "- バグ修正後の再テスト\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/12_バックログ_Sprint3.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-25"
        ),
    },
    {
        "title": "[B-08] pytest: test_utils.py 境界値テスト（Sprint 3追加分）",
        "labels": ["テスト", "sprint3"],
        "milestone": "Sprint 3",
        "body": (
            "**スプリント：** Sprint 3（2026-06-25 〜 06-29）\n"
            "**種別：** pytest\n"
            "**ファイル：** `tests/test_utils.py`\n"
            "**担当：** 担当②\n\n"
            "### テスト内容\n"
            "- `get_deadline_status()` 全件（B-08-01〜07）実装\n"
            "- 全件グリーン確認\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/12_バックログ_Sprint3.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-25"
        ),
    },
    {
        "title": "[B-09] pytest: test_password_change_view.py（Sprint 3追加分）",
        "labels": ["テスト", "sprint3"],
        "milestone": "Sprint 3",
        "body": (
            "**スプリント：** Sprint 3（2026-06-25 〜 06-29）\n"
            "**種別：** pytest\n"
            "**ファイル：** `tests/test_password_change_view.py`\n"
            "**担当：** 担当③\n\n"
            "### テスト内容\n"
            "- 全件（B-09-01〜07）実装・全件グリーン確認\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/12_バックログ_Sprint3.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-25"
        ),
    },
    {
        "title": "[B-10-01] pytest: test_employee_dto.py EmployeeDTO 単体テスト",
        "labels": ["テスト", "sprint3"],
        "milestone": "Sprint 3",
        "body": (
            "**スプリント：** Sprint 3（2026-06-25 〜 06-29）\n"
            "**種別：** pytest\n"
            "**ファイル：** `tests/test_employee_dto.py`\n"
            "**担当：** 担当④\n\n"
            "### テスト内容\n"
            "- EmployeeDTO の `@property` / `@setter` 動作確認（B-10-01 全6件）\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/12_バックログ_Sprint3.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-25"
        ),
    },
    {
        "title": "[B-10-02] pytest: test_equipment_dto.py EquipmentDTO 単体テスト",
        "labels": ["テスト", "sprint3"],
        "milestone": "Sprint 3",
        "body": (
            "**スプリント：** Sprint 3（2026-06-25 〜 06-29）\n"
            "**種別：** pytest\n"
            "**ファイル：** `tests/test_equipment_dto.py`\n"
            "**担当：** 担当④\n\n"
            "### テスト内容\n"
            "- EquipmentDTO の `@property` / `@setter` 動作確認（B-10-02 全4件）\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/12_バックログ_Sprint3.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-25"
        ),
    },
    {
        "title": "[B-10-03] pytest: test_inspection_dto.py InspectionDTO 単体テスト",
        "labels": ["テスト", "sprint3"],
        "milestone": "Sprint 3",
        "body": (
            "**スプリント：** Sprint 3（2026-06-25 〜 06-29）\n"
            "**種別：** pytest\n"
            "**ファイル：** `tests/test_inspection_dto.py`\n"
            "**担当：** 担当⑤\n\n"
            "### テスト内容\n"
            "- InspectionDTO の `@property` / `@setter` 動作確認\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/12_バックログ_Sprint3.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-25"
        ),
    },
    {
        "title": "[Sprint3-C] 設計書最終版（4種）の完成",
        "labels": ["ドキュメント", "sprint3"],
        "milestone": "Sprint 3",
        "body": (
            "**スプリント：** Sprint 3（2026-06-25 〜 06-29）\n"
            "**種別：** ドキュメント\n"
            "**対象ファイル：** `docs/01_`, `docs/03_`, `docs/04_`, `docs/05_`\n"
            "**担当：** 担当⑥\n\n"
            "### タスク内容\n"
            "- Sprint 3 で追加・変更された機能を全4設計書に反映する\n"
            "- 発表用の最終版として完成させる\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/12_バックログ_Sprint3.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-25"
        ),
    },
    {
        "title": "[Sprint3-D] 発表資料・カバレッジレポートの作成",
        "labels": ["ドキュメント", "sprint3"],
        "milestone": "Sprint 3",
        "body": (
            "**スプリント：** Sprint 3（2026-06-25 〜 06-29）\n"
            "**発表日：** 2026-06-30（火）成果報告会\n"
            "**担当：** 担当⑤⑥\n\n"
            "### タスク内容\n"
            "- `pytest --cov` でカバレッジ計測（C0: 80%以上、C1: 70%以上）\n"
            "- カバレッジレポートの確認・共有\n"
            "- 発表資料の作成\n"
            "- デモ準備（設備21件以上・点検記録複数件のデモデータ確認）\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/12_バックログ_Sprint3.md`）"
            "から2026-06-26に作成されました。元の記入日：2026-06-25"
        ),
    },
]


# ──────────────────────────────────────────────
# 記入日 → スプリントラベルの変換
# ──────────────────────────────────────────────
def date_to_sprint(date_str):
    """記入日（YYYY-MM-DD形式）からスプリントラベル名を返す"""
    if not date_str or date_str.strip() == "":
        return "sprint3"  # デフォルト
    # 日付文字列から月日を取得する
    m = re.match(r"\d{4}-(\d{2})-(\d{2})", date_str.strip())
    if not m:
        return "sprint3"
    month = int(m.group(1))
    day = int(m.group(2))
    if month != 6:
        return "sprint0"
    # 6月の日付でスプリントを判定する
    if day <= 14:
        return "sprint0"
    elif day <= 18:
        return "sprint1"
    elif day <= 24:
        return "sprint2"
    else:
        return "sprint3"


# ──────────────────────────────────────────────
# 課題管理表のパース
# ──────────────────────────────────────────────
def parse_kadai_table(file_path):
    """
    06_課題管理表.md のテーブル行をパースして Issue データのリストを返す。
    各行の形式: | No. | ステータス | 機能 | 画面 | 課題内容 | 対応方針 | 記入日 | 記入者 |
    """
    issues = []
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        # テーブルのデータ行のみ処理する（ヘッダーや区切り行は除外）
        if not line.startswith("|"):
            continue
        # 区切り行（---|---）はスキップする（"---" が含まれる行を除外）
        if "---" in line:
            continue

        # セルを分割する
        cells = [c.strip() for c in line.split("|")]
        # 空セルを除去（行の最初と最後の | による空文字列）
        cells = [c for c in cells if c != ""]

        # 必要な列数チェック（No. / ステータス / 機能 / 画面 / 課題内容 / 対応方針 / 記入日 / 記入者）
        if len(cells) < 6:
            continue

        no_col       = cells[0]
        status_col   = cells[1] if len(cells) > 1 else ""
        kino_col     = cells[2] if len(cells) > 2 else ""
        gamen_col    = cells[3] if len(cells) > 3 else ""
        kadai_col    = cells[4] if len(cells) > 4 else ""
        taiou_col    = cells[5] if len(cells) > 5 else ""
        date_col     = cells[6] if len(cells) > 6 else ""
        author_col   = cells[7] if len(cells) > 7 else ""

        # ヘッダー行をスキップする
        if no_col in ("No.", "No"):
            continue

        # No. の形式チェック（数字3桁または2桁）
        if not re.match(r"^\d{2,3}$", no_col.strip()):
            continue

        # No. をゼロパディングして統一する（例: 9 → 009）
        no_str = no_col.strip().zfill(3)

        # Issue タイトルを生成する（課題内容の最初の40文字を使う）
        short_title = kadai_col[:60] if len(kadai_col) > 60 else kadai_col
        title = f"[No.{no_str}] {short_title}"

        # ラベルを決定する
        labels = []
        if "テスト" in kino_col:
            labels.append("テスト")
        elif status_col == "未対応":
            labels.append("bug")
        else:
            labels.append("bug")

        # スプリントラベルを追加する
        sprint_label = date_to_sprint(date_col)
        labels.append(sprint_label)

        # 対応状況ラベルを追加する
        if "対応済" in status_col:
            labels.append("対応済")
        elif "未対応" in status_col:
            labels.append("未対応")

        # マイルストーンを決定する
        sprint_to_milestone = {
            "sprint0": "Sprint 0",
            "sprint1": "Sprint 1",
            "sprint2": "Sprint 2",
            "sprint3": "Sprint 3",
        }
        milestone = sprint_to_milestone.get(sprint_label, "Sprint 3")

        # Issue 本文を生成する
        body = (
            f"**No.** {no_str}\n"
            f"**ステータス：** {status_col}\n"
            f"**機能：** {kino_col}\n"
            f"**画面：** {gamen_col}\n\n"
            f"### 課題内容\n\n{kadai_col}\n\n"
            f"### 対応方針\n\n{taiou_col}\n\n"
            f"---\n\n"
            f"**記入日：** {date_col}  \n"
            f"**記入者：** {author_col}\n\n"
            "> ⚠️ このIssueは既存ドキュメント（`docs/06_課題管理表.md`）"
            "から2026-06-26に作成されました。"
        )

        issues.append({
            "title":     title,
            "labels":    labels,
            "milestone": milestone,
            "body":      body,
            "status":    status_col,
        })

    return issues


# ──────────────────────────────────────────────
# GitHub API ヘルパー関数
# ──────────────────────────────────────────────
def api_request(token, method, endpoint, data=None):
    """
    GitHub Enterprise API にリクエストを送信する。
    成功時はレスポンスの dict を返す。失敗時は None を返す。
    """
    url = f"{GHE_BASE}/{endpoint}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    body_bytes = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # 422 = already exists（ラベル・マイルストーン重複）は無視する
        if e.code == 422:
            return {"_already_exists": True}
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"  ❌ HTTP {e.code}: {url}")
        print(f"     {error_body[:200]}")
        return None
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        return None


def create_label(token, label):
    """ラベルを作成する（既存の場合はスキップ）"""
    result = api_request(token, "POST",
                         f"repos/{REPO_OWNER}/{REPO_NAME}/labels",
                         label)
    if result and result.get("_already_exists"):
        print(f"  ⚠️  ラベル既存スキップ: {label['name']}")
    elif result:
        print(f"  ✅ ラベル作成: {label['name']}")
    time.sleep(SLEEP_SEC)
    return result


def create_milestone(token, ms):
    """マイルストーンを作成する（既存の場合はスキップ）"""
    result = api_request(token, "POST",
                         f"repos/{REPO_OWNER}/{REPO_NAME}/milestones",
                         {"title": ms["title"],
                          "description": ms["description"],
                          "due_on": ms["due_on"]})
    if result and result.get("_already_exists"):
        print(f"  ⚠️  マイルストーン既存スキップ: {ms['title']}")
    elif result:
        print(f"  ✅ マイルストーン作成: {ms['title']} (#{result.get('number')})")
    time.sleep(SLEEP_SEC)
    return result


def get_milestone_numbers(token):
    """全マイルストーンのタイトル → number のマップを返す"""
    result = api_request(token, "GET",
                         f"repos/{REPO_OWNER}/{REPO_NAME}/milestones?per_page=50&state=all")
    if not result:
        return {}
    return {m["title"]: m["number"] for m in result}


def create_issue(token, issue_data, milestone_map):
    """
    Issue を作成する。
    issue_data は title / body / labels / milestone / status を持つ dict。
    """
    ms_number = milestone_map.get(issue_data.get("milestone"))
    payload = {
        "title":  issue_data["title"],
        "body":   issue_data["body"],
        "labels": issue_data.get("labels", []),
    }
    if ms_number:
        payload["milestone"] = ms_number

    result = api_request(token, "POST",
                         f"repos/{REPO_OWNER}/{REPO_NAME}/issues",
                         payload)
    if not result or result.get("_already_exists"):
        print(f"  ❌ Issue 作成失敗: {issue_data['title'][:50]}")
        time.sleep(SLEEP_SEC)
        return None

    issue_number = result.get("number")
    print(f"  ✅ Issue #{issue_number}: {issue_data['title'][:60]}")

    # 対応済みの Issue はクローズする
    if "対応済" in issue_data.get("labels", []):
        close_result = api_request(token, "PATCH",
                                   f"repos/{REPO_OWNER}/{REPO_NAME}/issues/{issue_number}",
                                   {"state": "closed"})
        if close_result:
            print(f"     → クローズしました")

    time.sleep(SLEEP_SEC)
    return result


# ──────────────────────────────────────────────
# メイン処理
# ──────────────────────────────────────────────
def main():
    # トークンを引数から取得する
    if len(sys.argv) < 2:
        print("使い方: python scripts/create_github_issues.py <PERSONAL_ACCESS_TOKEN>")
        print("例:     python scripts/create_github_issues.py ghp_xxxxxxxxxxxx")
        sys.exit(1)

    token = sys.argv[1].strip()

    # 接続テスト
    print("🔍 リポジトリへの接続確認中...")
    repo_info = api_request(token, "GET", f"repos/{REPO_OWNER}/{REPO_NAME}")
    if not repo_info or "id" not in repo_info:
        print("❌ リポジトリに接続できませんでした。トークンとURL設定を確認してください。")
        sys.exit(1)
    print(f"✅ リポジトリ確認: {repo_info.get('full_name')}")

    # ── Step 1: ラベル作成 ──
    print("\n📌 ラベルを作成中...")
    for label in LABELS:
        create_label(token, label)

    # ── Step 2: マイルストーン作成 ──
    print("\n🏁 マイルストーンを作成中...")
    for ms in MILESTONES:
        create_milestone(token, ms)

    # マイルストーン番号を取得する
    milestone_map = get_milestone_numbers(token)
    print(f"   マイルストーン取得: {list(milestone_map.keys())}")

    # ── Step 3: 課題管理表の Issue 作成 ──
    kadai_file = os.path.join(DOCS_DIR, "06_課題管理表.md")
    print(f"\n📋 課題管理表 Issues を作成中... ({kadai_file})")

    kadai_issues = parse_kadai_table(kadai_file)
    print(f"   {len(kadai_issues)}件 パース完了")

    for issue in kadai_issues:
        create_issue(token, issue, milestone_map)

    # ── Step 4: バックログ Issues 作成 ──
    print(f"\n📝 バックログ Issues を作成中... ({len(BACKLOG_ISSUES)}件)")
    for issue in BACKLOG_ISSUES:
        create_issue(token, issue, milestone_map)

    # ── 完了 ──
    total = len(kadai_issues) + len(BACKLOG_ISSUES)
    print(f"\n🎉 完了！ 合計 {total} 件の Issue 作成を試みました。")
    print(f"   リポジトリ: https://akkodis-jp.ghe.com/{REPO_OWNER}/{REPO_NAME}/issues")


if __name__ == "__main__":
    main()
