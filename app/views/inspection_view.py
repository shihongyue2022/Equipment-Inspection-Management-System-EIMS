"""
点検記録登録用ビュー
URLルール: /inspection/*
"""

from flask import render_template, session, redirect, url_for, request, flash
from flask_wtf import FlaskForm
from datetime import date, timedelta

from app.dao.inspection_dao import InspectionDao
from app.dao.equipment_dao import EquipmentDao
from app.dto.inspection_dto import InspectionDto
from app.utils import login_required


class InspectionForm(FlaskForm):
    """点検記録フォーム（CSRFトークン生成用）"""
    pass


@login_required
def inspection_new_get():
    """
    点検記録登録画面を表示する（GET /inspection/new）
    - 管理者：全設備を選択リストに表示
    - FE：担当設備のみ表示
    URLパラメータ equipment_id が渡された場合は対象設備を初期選択する。
    """
    # セッションからログインユーザー情報を取得する
    user = session.get("user")
    user_id = user["id"]
    role = user["role"]

    # URLパラメータから対象設備IDを取得する（任意）
    # request.args.get() は文字列を返すため、整数に変換してDTOのidと型を合わせる
    equipment_id_param = request.args.get("equipment_id")
    equipment_id = int(equipment_id_param) if equipment_id_param else None

    # ロールに応じて設備選択リストを準備する
    dao_equipment = EquipmentDao()
    try:
        if role in ["root", "admin"]:
            # 管理者の場合は全設備を取得する
            equipment_list = dao_equipment.find_all()
        else:
            # FEの場合は担当設備のみを取得する
            equipment_list = dao_equipment.find_by_user_id(user_id)
    finally:
        dao_equipment.close()

    # CSRFトークンをテンプレートに渡すためフォームインスタンスを生成する
    form = InspectionForm()

    # back パラメータを引き継ぎ、キャンセル時は設備詳細に戻る（back を保持）
    back = request.args.get("back", "dashboard")
    if equipment_id:
        cancel_url = url_for("equipment_detail_get", id=equipment_id) + "?back=" + back
    else:
        cancel_url = url_for("equipment_list_get") if back == "list" else url_for("dashboard_get")

    return render_template(
        "inspection/new.html",
        equipment_list=equipment_list,
        selected_equipment_id=equipment_id,
        form=form,
        form_data=None,
        error_message=None,
        today=date.today().isoformat(),
        tomorrow=(date.today() + timedelta(days=1)).isoformat(),
        cancel_url=cancel_url,
        back=back,
    )


@login_required
def inspection_new_post():
    """
    点検記録登録処理を行う（POST /inspection/new）
    バリデーション → FE担当チェック → DB登録 → 次回点検日更新
    """
    # セッションからログインユーザー情報を取得する
    user = session.get("user")
    user_id = user["id"]
    role = user["role"]

    # CSRFトークン検証（不正リクエストはダッシュボードへリダイレクトする）
    form = InspectionForm()
    if not form.validate_on_submit():
        flash("不正なリクエストです。", "danger")
        return redirect(url_for("dashboard_get"))

    # リクエストパラメータを取得する
    equipment_id_str = request.form.get("equipment_id", "").strip()
    inspected_at     = request.form.get("inspected_at", "").strip()
    status           = request.form.get("status", "").strip()
    note             = request.form.get("note", "").strip()
    # 要修理の場合のみ使用する次回点検予定日
    repair_next_date = request.form.get("repair_next_date", "").strip()

    today_str    = date.today().isoformat()
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()

    # back パラメータを引き継ぎ、キャンセル時は設備詳細に戻る（back を保持）
    back = request.form.get("back", "dashboard")
    eq_id = equipment_id_str if equipment_id_str else None
    if eq_id:
        cancel_url = url_for("equipment_detail_get", id=eq_id) + "?back=" + back
    else:
        cancel_url = url_for("equipment_list_get") if back == "list" else url_for("dashboard_get")

    # 再表示用に設備リストを取得する（バリデーション前にDBを閉じてメモリに保持する）
    dao_equipment = EquipmentDao()
    try:
        if role in ["root", "admin"]:
            equipment_list = dao_equipment.find_all()
        else:
            equipment_list = dao_equipment.find_by_user_id(user_id)
    finally:
        dao_equipment.close()

    def render_error(message):
        """バリデーションエラー時にフォームを再表示するヘルパー。"""
        return render_template(
            "inspection/new.html",
            equipment_list=equipment_list,
            selected_equipment_id=equipment_id_str,
            form=form,
            form_data=request.form,
            error_message=message,
            today=today_str,
            tomorrow=tomorrow_str,
            cancel_url=cancel_url,
            back=back,
        )

    # 必須項目の入力チェックを行う（対象設備・実施日・点検ステータス）
    if not all([equipment_id_str, inspected_at, status]):
        return render_error("入力情報に誤りがあります。必須項目をすべて入力してください。")

    # 未来日付チェック（当日より後の日付は登録不可）
    if inspected_at > today_str:
        return render_error("点検実施日に未来の日付は登録できません。")

    # 要修理の場合、次回点検予定日と備考の入力チェックを行う
    if status == "repair":
        if not repair_next_date:
            return render_error("要修理の場合は次回点検予定日を入力してください。")
        # 次回点検予定日は点検実施日より後の日付が必要
        if repair_next_date <= inspected_at:
            return render_error("次回点検予定日は点検実施日より後の日付を選択してください。")
        # 備考は要修理の場合に必須
        if not note:
            return render_error("要修理の場合は備考に修理内容・対応方針を入力してください。")

    equipment_id = int(equipment_id_str)

    # FEの場合、担当設備かどうかを確認する
    if role == "engineer":
        assigned_ids = [eq.id for eq in equipment_list]
        if equipment_id not in assigned_ids:
            # 担当外の設備への登録はダッシュボードへリダイレクトする
            return redirect(url_for("dashboard_get"))

    # 点検登録時点の next_inspection_date を記録する（期限遵守履歴の追跡用）
    expected_date = next(
        (eq.next_inspection_date for eq in equipment_list if eq.id == equipment_id),
        None,
    )

    # InspectionDto を生成して DB に登録する
    dto = InspectionDto()
    dto.equipment_id = equipment_id
    dto.engineer_id  = user_id
    dto.inspected_at = inspected_at
    dto.expected_inspection_date = expected_date
    dto.status = status
    dto.note   = note if note else None

    dao_inspection = InspectionDao()
    try:
        dao_inspection.create(dto)
    finally:
        dao_inspection.close()

    # ステータスに応じて次回点検予定日を更新する
    dao_equipment = EquipmentDao()
    try:
        if status == "repair":
            # 要修理：ユーザーが選択した日付をそのまま設定する
            dao_equipment.set_next_inspection_date(equipment_id, repair_next_date)
        elif status == "watch":
            # 要観察：通常間隔の半分（最小1ヶ月）で次回点検日を設定する
            dao_equipment.update_next_inspection_date(equipment_id, half_interval=True)
        else:
            # 異常なし：通常の間隔で次回点検日を計算する
            dao_equipment.update_next_inspection_date(equipment_id)
    finally:
        dao_equipment.close()

    return redirect(url_for("dashboard_get"))
