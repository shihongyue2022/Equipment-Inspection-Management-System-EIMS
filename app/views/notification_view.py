"""
通知API用ビュー
URLルール: /api/notifications
"""
from datetime import datetime

from flask import jsonify, session

from app.dao.equipment_dao import EquipmentDao
from app.utils import get_deadline_status


def notifications_get():
    """
    通知データをJSON形式で返す（GET /api/notifications）
    - 緊急対応リスト（期限超過・要修理）の件数と一覧を返す
    - FEは担当設備のみ、管理者は全設備対象
    """
    # ログインチェック
    user = session.get("user")
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    user_id = user["id"]
    role = user["role"]

    # ロールに応じて設備一覧を取得する
    dao = EquipmentDao()
    if role in ["root", "admin"]:
        equipment_list = dao.find_all()
    else:
        equipment_list = dao.find_by_user_id(user_id)
    dao.close()

    # 各設備の期限ステータスを計算する
    for eq in equipment_list:
        eq.deadline_status = get_deadline_status(eq.next_inspection_date)

    # 各カテゴリの件数を算出する
    overdue_count = sum(1 for eq in equipment_list if eq.deadline_status == "overdue")
    soon_count    = sum(1 for eq in equipment_list if eq.deadline_status == "soon")
    repair_count  = sum(1 for eq in equipment_list if eq.latest_inspection_status == "repair")

    # 緊急対応リスト（期限超過 or 要修理）を優先度順に最大10件取得する
    urgent_candidates = [
        eq for eq in equipment_list
        if eq.deadline_status == "overdue" or eq.latest_inspection_status == "repair"
    ]
    urgent_list = sorted(
        urgent_candidates,
        key=lambda eq: (
            0 if eq.deadline_status == "overdue" else 1,
            eq.next_inspection_date or datetime.max.date(),
        )
    )[:10]

    # 通知データをJSON形式で組み立てて返す
    return jsonify({
        "overdue_count": overdue_count,
        "soon_count":    soon_count,
        "repair_count":  repair_count,
        "total_urgent":  overdue_count + repair_count,
        "urgent_items": [
            {
                "id":                       eq.id,
                "name":                     eq.name,
                "location":                 eq.location,
                "deadline_status":          eq.deadline_status,
                "latest_inspection_status": eq.latest_inspection_status,
                "next_inspection_date": (
                    eq.next_inspection_date.strftime("%Y-%m-%d")
                    if eq.next_inspection_date else None
                ),
            }
            for eq in urgent_list
        ],
    })
