"""
ダッシュボード画面用ビュー
URLルール: /dashboard
"""

import json
from datetime import datetime

from flask import render_template, session, request

from app.dao.equipment_dao import EquipmentDao
from app.dao.user_dao import UserDao
from app.utils import get_deadline_status, login_required
from app.constants import ADMIN_ROLES


def _fetch_equipment_list(role, user_id, selected_base):
    """ロールと拠点フィルタに応じて設備一覧をDBから取得して返す。"""
    dao = EquipmentDao()
    try:
        if role in ADMIN_ROLES:
            if selected_base:
                # 拠点フィルタが指定されている場合は絞り込む
                equipment_list = dao.find_all_by_base(selected_base)
            else:
                # 拠点フィルタがない場合は全設備を取得する
                equipment_list = dao.find_all()
        else:
            # FEの場合は担当設備のみを取得する
            equipment_list = dao.find_by_user_id(user_id)
    finally:
        dao.close()
    return equipment_list


def _calculate_summary_counts(equipment_list):
    """設備一覧から集計カード用の件数を算出して辞書で返す。
    フィルタ適用前の一覧を渡すこと。
    """
    return {
        "total":      len(equipment_list),
        "unassigned": sum(1 for eq in equipment_list if not eq.assigned_user_id),
        "overdue":    sum(1 for eq in equipment_list if eq.deadline_status == "overdue"),
        "soon":       sum(1 for eq in equipment_list if eq.deadline_status == "soon"),
        "repair":     sum(1 for eq in equipment_list if eq.latest_inspection_status == "repair"),
    }


def _apply_dashboard_filters(equipment_list, keyword, status_filter):
    """キーワードとステータスフィルタを設備一覧に適用して返す。"""
    result = equipment_list

    # キーワードフィルタ（設備名・設備IDで絞り込む）
    if keyword:
        keyword_lower = keyword.lower()
        result = [
            eq for eq in result
            if keyword_lower in eq.name.lower()
            or keyword_lower in "eq-{:04d}".format(eq.id)
        ]

    # ステータスフィルタを適用する
    if status_filter == "overdue":
        result = [eq for eq in result if eq.deadline_status == "overdue"]
    elif status_filter == "soon":
        result = [eq for eq in result if eq.deadline_status == "soon"]
    elif status_filter == "unassigned":
        result = [eq for eq in result if not eq.assigned_user_id]
    elif status_filter == "repair":
        result = [eq for eq in result if eq.latest_inspection_status == "repair"]

    return result


def _fetch_admin_analytics(selected_base, overdue_count, soon_count, unassigned_count, equipment_list):
    """管理者向け分析データ（拠点別統計・週次スケジュール・緊急リスト等）を取得して辞書で返す。"""
    dao = EquipmentDao()
    try:
        # 拠点選択時は週次スケジュール、未選択時は拠点別統計を取得する
        if selected_base:
            weekly_schedule = dao.find_weekly_schedule(base=selected_base)
            monthly_schedule_json = json.dumps(weekly_schedule, ensure_ascii=False)
            location_stats_json = "[]"
        else:
            location_stats = dao.find_stats_by_base()
            location_stats_json = json.dumps(location_stats, ensure_ascii=False)
            monthly_schedule_json = "[]"

        engineer_stats = dao.find_stats_by_engineer(base=selected_base)
        overdue_last_week    = dao.count_overdue_7days_ago(base=selected_base)
        soon_last_week       = dao.count_soon_7days_ago(base=selected_base)
        unassigned_last_week = dao.count_unassigned_7days_ago(base=selected_base)
    finally:
        dao.close()

    # 先週比を計算する（今の件数 - 7日前時点の件数）
    overdue_diff    = overdue_count    - overdue_last_week
    soon_diff       = soon_count       - soon_last_week
    unassigned_diff = unassigned_count - unassigned_last_week

    # 緊急対応リスト：期限超過または要修理の設備を優先度順に全件取得する
    urgent_candidates = [
        eq for eq in equipment_list
        if eq.deadline_status == "overdue" or eq.latest_inspection_status == "repair"
    ]
    # 期限超過を先頭に、次回点検日が古い順に並べる
    urgent_list = sorted(
        urgent_candidates,
        key=lambda eq: (
            0 if eq.deadline_status == "overdue" else 1,
            eq.next_inspection_date or datetime.max.date(),
        )
    )

    return {
        "location_stats_json":   location_stats_json,
        "monthly_schedule_json": monthly_schedule_json,
        "engineer_stats":        engineer_stats,
        "overdue_diff":          overdue_diff,
        "soon_diff":             soon_diff,
        "unassigned_diff":       unassigned_diff,
        "urgent_list":           urgent_list,
    }


@login_required
def dashboard_get():
    """
    ダッシュボード画面を表示する（GET /dashboard）
    - 管理者：全設備または拠点・キーワード・ステータスフィルタ済み設備を表示
    - FE：担当設備のみ表示
    """
    try:
        # ログインユーザー情報をセッションから取得する
        user = session.get("user")
        user_id = user["id"]
        role = user["role"]

        # フィルタパラメータをGETパラメータから取得する
        keyword = request.args.get("keyword", "").strip()
        status_filter = request.args.get("status_filter", "")
        selected_base = None
        if role in ADMIN_ROLES:
            selected_base = request.args.get("base") or None

        # 設備一覧を取得し、各設備の期限ステータスを計算する
        equipment_list = _fetch_equipment_list(role, user_id, selected_base)
        for eq in equipment_list:
            eq.deadline_status = get_deadline_status(eq.next_inspection_date)

        # 集計カード用の件数を算出する（フィルタ適用前の数値）
        counts = _calculate_summary_counts(equipment_list)

        # キーワード・ステータスフィルタを適用して表示用リストを生成する
        display_list = _apply_dashboard_filters(equipment_list, keyword, status_filter)

        # 管理者の場合、拠点フィルタ用の拠点一覧を取得する
        bases = []
        if role in ADMIN_ROLES:
            dao_user = UserDao()
            bases = dao_user.find_distinct_bases()
            dao_user.close()

        # 天気表示に使う拠点名を決定する
        # FEは自分の拠点、管理者は選択中の拠点（未選択は東京）
        if role in ADMIN_ROLES:
            weather_location = selected_base if selected_base else "東京"
        else:
            weather_location = user.get("base") or "東京"

        # 画面ヘッダー表示用の現在日時を生成する
        current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 管理者向け分析データを取得する（FEの場合はデフォルト値を使用する）
        analytics = {
            "location_stats_json":   "[]",
            "monthly_schedule_json": "[]",
            "engineer_stats":        [],
            "overdue_diff":          0,
            "soon_diff":             0,
            "unassigned_diff":       0,
            "urgent_list":           [],
        }
        if role in ADMIN_ROLES:
            analytics = _fetch_admin_analytics(
                selected_base,
                counts["overdue"],
                counts["soon"],
                counts["unassigned"],
                equipment_list,
            )

        # ダッシュボード画面を表示する
        return render_template(
            "dashboard.html",
            equipment_list=display_list,
            total_count=counts["total"],
            unassigned_count=counts["unassigned"],
            overdue_count=counts["overdue"],
            soon_count=counts["soon"],
            repair_count=counts["repair"],
            bases=bases,
            selected_base=selected_base,
            keyword=keyword,
            status_filter=status_filter,
            current_date_time=current_date_time,
            weather_location=weather_location,
            engineer_stats=analytics["engineer_stats"],
            location_stats_json=analytics["location_stats_json"],
            monthly_schedule_json=analytics["monthly_schedule_json"],
            overdue_diff=analytics["overdue_diff"],
            soon_diff=analytics["soon_diff"],
            unassigned_diff=analytics["unassigned_diff"],
            urgent_list=analytics["urgent_list"],
        )

    except Exception as e:
        # 予期しないエラーが発生した場合は再スローする
        raise e
