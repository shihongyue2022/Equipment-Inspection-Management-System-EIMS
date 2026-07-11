import json
from datetime import date
from dateutil.relativedelta import relativedelta

from flask import render_template, request, redirect, url_for, session, flash
from flask_wtf import FlaskForm

from app.dao.equipment_dao import EquipmentDao
from app.dao.user_dao import UserDao
from app.dao.inspection_dao import InspectionDao
from app.dto.equipment_dto import EquipmentDto
from app.utils import get_deadline_status, login_required, admin_required


class EquipmentForm(FlaskForm):
    """CSRF対策トークンを生成するための最小限フォームクラス"""
    pass


def register_routes(app):
    """設備マスタ関連のルートをFlaskアプリに登録する"""

    # ----- 設備一覧 -----

    @app.route('/equipment')
    @admin_required
    def equipment_list_get():
        """設備一覧画面を表示する（管理者のみ）"""
        # GETパラメータで検索条件を受け取る
        search_name = request.args.get('name', '').strip()
        search_type = request.args.get('equipment_type', '').strip()
        search_status = request.args.get('deadline_status', '').strip()
        search_user_str = request.args.get('assigned_user_id', '').strip()
        search_user_id = int(search_user_str) if search_user_str else None

        dao_eq = EquipmentDao()
        dao_user = UserDao()
        try:
            # 検索条件をDAOに渡して絞り込む
            equipment_list = dao_eq.find_with_filter(
                name=search_name or None,
                equipment_type=search_type or None,
                assigned_user_id=search_user_id,
            )
            # 各設備の期限ステータスを計算する
            for eq in equipment_list:
                eq.deadline_status = get_deadline_status(eq.next_inspection_date)

            # 期限ステータスはDB非保存のため、Python側でフィルタリングする
            if search_status == 'none':
                # 「未点検」＝ deadline_status が None のもの
                equipment_list = [eq for eq in equipment_list if eq.deadline_status is None]
            elif search_status:
                equipment_list = [eq for eq in equipment_list if eq.deadline_status == search_status]

            # 担当者候補（エンジニア一覧）を取得する
            engineer_list = dao_user.find_by_role('engineer')
            # 一括編集モーダルのエリア選択用に拠点一覧を生成する
            base_list = sorted(set(u.base for u in engineer_list if u.base))
        finally:
            dao_eq.close()
            dao_user.close()

        # 現在の検索条件（フォームの入力値を保持するために渡す）
        search_params = {
            'name': search_name,
            'equipment_type': search_type,
            'deadline_status': search_status,
            'assigned_user_id': search_user_str,
        }

        form = EquipmentForm()
        return render_template(
            'equipment/list.html',
            equipment_list=equipment_list,
            engineer_list=engineer_list,
            base_list=base_list,
            form=form,
            search_params=search_params,
            today=date.today(),
        )

    # ----- 設備登録（新規） -----

    @app.route('/equipment/new', methods=['GET'])
    @admin_required
    def equipment_new_get():
        """設備登録フォームを表示する（管理者のみ）"""
        dao_user = UserDao()
        dao_eq = EquipmentDao()
        try:
            engineer_list = dao_user.find_by_role('engineer')
            # オートコンプリート用に登録済みlocation・manufacturerを取得する
            location_list = dao_eq.find_distinct_locations()
            manufacturer_list = dao_eq.find_distinct_manufacturers()
        finally:
            dao_user.close()
            dao_eq.close()

        # エリア選択肢：エンジニアの拠点一覧から重複なしで取得する
        base_list = sorted(set(u.base for u in engineer_list if u.base))

        form = EquipmentForm()
        return render_template(
            'equipment/new.html',
            form=form,
            engineer_list=engineer_list,
            location_list=location_list,
            manufacturer_list=manufacturer_list,
            base_list=base_list,
            form_data=None,
            error_message=None,
        )

    @app.route('/equipment/new', methods=['POST'])
    @admin_required
    def equipment_new_post():
        """設備を新規登録する（管理者のみ）"""
        form = EquipmentForm()

        # CSRFトークン検証
        if not form.validate_on_submit():
            flash('不正なリクエストです。', 'danger')
            return redirect(url_for('equipment_list_get'))

        dao_user = UserDao()
        dao_eq_loc = EquipmentDao()
        try:
            engineer_list = dao_user.find_by_role('engineer')
            # オートコンプリート用に登録済みlocation・manufacturerを取得する
            location_list = dao_eq_loc.find_distinct_locations()
            manufacturer_list = dao_eq_loc.find_distinct_manufacturers()
        finally:
            dao_user.close()
            dao_eq_loc.close()

        # エリア選択肢：エンジニアの拠点一覧から重複なしで取得する
        base_list = sorted(set(u.base for u in engineer_list if u.base))

        # フォーム値を取得する
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        equipment_type = request.form.get('equipment_type', '').strip()
        manufacturer = request.form.get('manufacturer', '').strip()
        model_number = request.form.get('model_number', '').strip()
        installed_at = request.form.get('installed_at', '').strip()
        interval_str = request.form.get('inspection_interval_months', '').strip()
        assigned_user_id_str = request.form.get('assigned_user_id', '').strip()
        area = request.form.get('area', '').strip() or None

        # 必須項目チェック
        if not all([name, location, equipment_type, manufacturer, model_number, installed_at, interval_str]):
            return render_template(
                'equipment/new.html',
                form=form,
                engineer_list=engineer_list,
                location_list=location_list,
                manufacturer_list=manufacturer_list,
                base_list=base_list,
                form_data=request.form,
                error_message='必須項目をすべて入力してください。',
            )

        # 点検間隔のバリデーション（1〜12の整数）
        try:
            interval = int(interval_str)
            if not (1 <= interval <= 12):
                raise ValueError()
        except ValueError:
            return render_template(
                'equipment/new.html',
                form=form,
                engineer_list=engineer_list,
                location_list=location_list,
                manufacturer_list=manufacturer_list,
                base_list=base_list,
                form_data=request.form,
                error_message='点検間隔は1〜12の整数を入力してください。',
            )

        # DTOに格納してDBへ登録する
        dto = EquipmentDto()
        dto.name = name
        dto.location = location
        dto.equipment_type = equipment_type
        dto.manufacturer = manufacturer
        dto.model_number = model_number
        dto.installed_at = installed_at
        dto.inspection_interval_months = interval
        dto.assigned_user_id = int(assigned_user_id_str) if assigned_user_id_str else None
        dto.area = area

        dao_eq = EquipmentDao()
        try:
            dao_eq.create(dto)
        finally:
            dao_eq.close()

        flash(f'設備「{name}」を登録しました。', 'success')
        return redirect(url_for('equipment_list_get'))

    # ----- 設備詳細 -----

    @app.route('/equipment/<int:id>')
    @login_required
    def equipment_detail_get(id):
        """設備詳細画面を表示する"""
        dao_eq = EquipmentDao()
        dao_ins = InspectionDao()
        try:
            equipment = dao_eq.find_by_id(id)
            if equipment is None:
                flash('指定された設備が見つかりません。', 'danger')
                return redirect(url_for('dashboard_get'))

            # FEは自分の担当設備のみアクセス可能
            if session['user']['role'] == 'engineer':
                if equipment.assigned_user_id != session['user']['id']:
                    flash('担当外の設備にはアクセスできません。', 'danger')
                    return redirect(url_for('dashboard_get'))

            equipment.deadline_status = get_deadline_status(equipment.next_inspection_date)
            inspection_records = dao_ins.find_by_equipment_id(id)
        finally:
            dao_eq.close()
            dao_ins.close()

        # チャートデータと設備指標を計算する
        chart_data = _calculate_chart_data(equipment, inspection_records)
        metrics = _calculate_equipment_metrics(equipment, chart_data["formal_records"])

        # back パラメータで戻り先を決定する（'list' なら設備一覧、それ以外はダッシュボード）
        back = request.args.get('back', 'dashboard')
        back_url = url_for('equipment_list_get') if back == 'list' else url_for('dashboard_get')
        return render_template(
            'equipment/detail.html',
            equipment=equipment,
            inspection_records=inspection_records,
            back_url=back_url,
            metrics=metrics,
            # チャート用JSONデータ
            chart_labels_json             = json.dumps(chart_data["chart_labels"], ensure_ascii=False),
            interval_values_json          = json.dumps(chart_data["interval_values"]),
            interval_over_scheduled_json  = json.dumps(chart_data["interval_over_scheduled"]),
            scheduled_days                = chart_data["scheduled_days"],
        )

    # ----- 設備編集 -----

    @app.route('/equipment/<int:id>/edit', methods=['GET'])
    @admin_required
    def equipment_edit_get(id):
        """設備編集フォームを表示する（管理者のみ）"""
        dao_eq = EquipmentDao()
        dao_user = UserDao()
        try:
            equipment = dao_eq.find_by_id(id)
            if equipment is None:
                flash('指定された設備が見つかりません。', 'danger')
                return redirect(url_for('equipment_list_get'))
            engineer_list = dao_user.find_by_role('engineer')
            # 拠点フィルター用に重複なしの拠点一覧を取得する
            base_list = sorted(set(u.base for u in engineer_list if u.base))
        finally:
            dao_eq.close()
            dao_user.close()

        form = EquipmentForm()
        return render_template(
            'equipment/edit.html',
            form=form,
            equipment=equipment,
            engineer_list=engineer_list,
            base_list=base_list,
            error_message=None,
        )

    @app.route('/equipment/<int:id>/edit', methods=['POST'])
    @admin_required
    def equipment_edit_post(id):
        """設備情報を更新する（管理者のみ）"""
        form = EquipmentForm()

        # CSRFトークン検証
        if not form.validate_on_submit():
            flash('不正なリクエストです。', 'danger')
            return redirect(url_for('equipment_list_get'))

        dao_eq = EquipmentDao()
        dao_user = UserDao()
        try:
            equipment = dao_eq.find_by_id(id)
            if equipment is None:
                flash('指定された設備が見つかりません。', 'danger')
                return redirect(url_for('equipment_list_get'))
            engineer_list = dao_user.find_by_role('engineer')
            # 拠点フィルター用に重複なしの拠点一覧を取得する
            base_list = sorted(set(u.base for u in engineer_list if u.base))

            # フォーム値を取得する
            name = request.form.get('name', '').strip()
            location = request.form.get('location', '').strip()
            equipment_type = request.form.get('equipment_type', '').strip()
            manufacturer = request.form.get('manufacturer', '').strip()
            model_number = request.form.get('model_number', '').strip()
            installed_at = request.form.get('installed_at', '').strip()
            interval_str = request.form.get('inspection_interval_months', '').strip()
            assigned_user_id_str = request.form.get('assigned_user_id', '').strip()
            area = request.form.get('area', '').strip() or None

            # 必須項目チェック
            if not all([name, location, equipment_type, manufacturer, model_number, installed_at, interval_str]):
                return render_template(
                    'equipment/edit.html',
                    form=form,
                    equipment=equipment,
                    engineer_list=engineer_list,
                    base_list=base_list,
                    error_message='必須項目をすべて入力してください。',
                )

            # 点検間隔のバリデーション（1〜12の整数）
            try:
                interval = int(interval_str)
                if not (1 <= interval <= 12):
                    raise ValueError()
            except ValueError:
                return render_template(
                    'equipment/edit.html',
                    form=form,
                    equipment=equipment,
                    engineer_list=engineer_list,
                    base_list=base_list,
                    error_message='点検間隔は1〜12の整数を入力してください。',
                )

            # DTOを更新してDB反映する
            equipment.name = name
            equipment.location = location
            equipment.equipment_type = equipment_type
            equipment.manufacturer = manufacturer
            equipment.model_number = model_number
            equipment.installed_at = installed_at
            equipment.inspection_interval_months = interval
            equipment.assigned_user_id = int(assigned_user_id_str) if assigned_user_id_str else None
            equipment.area = area

            dao_eq.update(equipment)
        finally:
            dao_eq.close()
            dao_user.close()

        flash(f'設備「{name}」の情報を更新しました。', 'success')
        return redirect(url_for('equipment_list_get'))

    # ----- 設備削除 -----

    @app.route('/equipment/<int:id>/delete', methods=['POST'])
    @admin_required
    def equipment_delete_post(id):
        """設備を削除する（管理者のみ）"""
        form = EquipmentForm()
        if not form.validate_on_submit():
            flash('不正なリクエストです。', 'danger')
            return redirect(url_for('equipment_list_get'))

        dao_eq = EquipmentDao()
        try:
            equipment = dao_eq.find_by_id(id)
            if equipment is None:
                flash('指定された設備が見つかりません。', 'danger')
                return redirect(url_for('equipment_list_get'))
            # 操作者のIDを渡してソフトデリートする（関連する点検記録も同時に論理削除される）
            deleted_by = session['user']['id']
            dao_eq.delete(id, deleted_by)
            flash(f'設備「{equipment.name}」を削除しました。ゴミ箱から復元できます。', 'success')
        except Exception:
            # 外部キー制約などのDB例外が発生した場合はエラーメッセージを表示してリダイレクトする
            flash('設備の削除に失敗しました。', 'danger')
        finally:
            dao_eq.close()

        return redirect(url_for('equipment_list_get'))

    # ----- 一括編集 -----

    @app.route('/equipment/bulk_edit', methods=['POST'])
    @admin_required
    def equipment_bulk_edit_post():
        """複数の設備を一括編集する（管理者のみ）"""
        form = EquipmentForm()
        # CSRFトークン検証
        if not form.validate_on_submit():
            flash('不正なリクエストです。', 'danger')
            return redirect(url_for('equipment_list_get'))

        # チェックボックスで選択した設備IDをカンマ区切りで受け取る
        id_list_str = request.form.get('equipment_ids', '')
        equipment_ids = [int(i) for i in id_list_str.split(',') if i.strip().isdigit()]
        if not equipment_ids:
            flash('設備が選択されていません。', 'warning')
            return redirect(url_for('equipment_list_get'))

        # 超過設備のロックチェック
        dao_check = EquipmentDao()
        try:
            overdue_ids = dao_check.find_overdue_ids(equipment_ids)
        finally:
            dao_check.close()

        if overdue_ids:
            if session['user']['role'] != 'root':
                # admin：超過設備が含まれる場合は一括編集を完全に禁止する
                flash(
                    f'選択中に期限超過の設備が {len(overdue_ids)} 件含まれています。'
                    '超過設備の一括編集はrootのみ実行できます。対象を外してから再度お試しください。',
                    'danger'
                )
                return redirect(url_for('equipment_list_get'))
            else:
                # root：トグルがOFFの場合は超過設備を対象から除外して続行する
                include_overdue = request.form.get('include_overdue', '') == '1'
                if not include_overdue:
                    overdue_set = set(overdue_ids)
                    equipment_ids = [i for i in equipment_ids if i not in overdue_set]
                    if not equipment_ids:
                        flash('超過設備を除外した結果、対象設備が0件になりました。', 'warning')
                        return redirect(url_for('equipment_list_get'))
                    flash(
                        f'超過設備 {len(overdue_ids)} 件を除外して更新します。',
                        'info'
                    )

        # 一括更新するフィールドと値を取得する（空白は更新しない）
        ALLOWED_FIELDS = [
            'name', 'location', 'equipment_type', 'manufacturer',
            'model_number', 'inspection_interval_months', 'assigned_user_id', 'area'
        ]
        update_fields = {}
        for field in ALLOWED_FIELDS:
            val = request.form.get(f'bulk_{field}', '').strip()
            if val == '':
                # 空白は「変更なし」として無視する
                continue
            if field == 'inspection_interval_months':
                # 点検間隔は1〜12の整数に制限する
                try:
                    interval = int(val)
                    if 1 <= interval <= 12:
                        update_fields[field] = interval
                except ValueError:
                    flash('点検間隔は1〜12の整数を入力してください。', 'danger')
                    return redirect(url_for('equipment_list_get'))
            elif field == 'assigned_user_id':
                # 担当者はIDを整数に変換する（「0」は未割当を意味する）
                try:
                    uid = int(val)
                    update_fields[field] = uid if uid != 0 else None
                except ValueError:
                    pass
            else:
                update_fields[field] = val

        if not update_fields:
            flash('更新する項目が選択されていません。', 'warning')
            return redirect(url_for('equipment_list_get'))

        changed_by = session['user']['id']
        dao_eq = EquipmentDao()
        try:
            updated_count, batch_id = dao_eq.bulk_update(equipment_ids, update_fields, changed_by)
        finally:
            dao_eq.close()

        # 元に戻す機能のためにバッチIDと変更フィールドをセッションに保存する
        session['last_bulk_edit'] = {
            'batch_id': batch_id,
            'updated_fields': list(update_fields.keys()),
            'count': updated_count,
        }

        flash(f'{updated_count}件の設備を一括更新しました。', 'success')
        return redirect(url_for('equipment_list_get'))

    # ----- 一括編集の元に戻す -----

    @app.route('/equipment/bulk_revert', methods=['POST'])
    @admin_required
    def equipment_bulk_revert_post():
        """直前の一括編集を元に戻す（管理者のみ）"""
        form = EquipmentForm()
        if not form.validate_on_submit():
            flash('不正なリクエストです。', 'danger')
            return redirect(url_for('equipment_list_get'))

        # セッションから一括編集のバッチIDと変更フィールドを取得する
        last_bulk_edit = session.get('last_bulk_edit')
        if not last_bulk_edit or not last_bulk_edit.get('batch_id'):
            flash('元に戻すデータがありません。', 'warning')
            return redirect(url_for('equipment_list_get'))

        batch_id = last_bulk_edit['batch_id']
        updated_fields = last_bulk_edit['updated_fields']
        reverted_by = session['user']['id']

        dao_eq = EquipmentDao()
        try:
            reverted_count = dao_eq.revert_bulk_edit(batch_id, updated_fields, reverted_by)
        finally:
            dao_eq.close()

        # セッションから一括編集履歴を削除する（二重revert防止）
        session.pop('last_bulk_edit', None)

        flash(f'{reverted_count}件の設備を元に戻しました。', 'success')
        return redirect(url_for('equipment_list_get'))

    # ----- 一括削除 -----

    @app.route('/equipment/bulk_delete', methods=['POST'])
    @admin_required
    def equipment_bulk_delete_post():
        """複数の設備を一括でゴミ箱に送る（管理者のみ）"""
        form = EquipmentForm()
        # CSRFトークン検証
        if not form.validate_on_submit():
            flash('不正なリクエストです。', 'danger')
            return redirect(url_for('equipment_list_get'))

        # チェックボックスで選択した設備IDをカンマ区切りで受け取る
        id_list_str = request.form.get('equipment_ids', '')
        equipment_ids = [int(i) for i in id_list_str.split(',') if i.strip().isdigit()]
        if not equipment_ids:
            flash('設備が選択されていません。', 'warning')
            return redirect(url_for('equipment_list_get'))

        deleted_by = session['user']['id']
        dao_eq = EquipmentDao()
        try:
            deleted_count = dao_eq.bulk_delete(equipment_ids, deleted_by)
        finally:
            dao_eq.close()

        flash(f'{deleted_count}件の設備をゴミ箱に送りました。ゴミ箱から復元できます。', 'success')
        return redirect(url_for('equipment_list_get'))

    # ----- 担当者変更 -----

    @app.route('/equipment/<int:id>/assign', methods=['POST'])
    @admin_required
    def equipment_assign_post(id):
        """担当者を変更する（管理者のみ）"""
        form = EquipmentForm()
        if not form.validate_on_submit():
            flash('不正なリクエストです。', 'danger')
            return redirect(url_for('equipment_list_get'))

        assigned_user_id_str = request.form.get('assigned_user_id', '').strip()
        assigned_user_id = int(assigned_user_id_str) if assigned_user_id_str else None

        dao_eq = EquipmentDao()
        try:
            dao_eq.update_assigned_user(id, assigned_user_id,
                                        changed_by=session["user"]["id"])
        finally:
            dao_eq.close()

        flash('担当者を変更しました。', 'success')
        return redirect(url_for('equipment_list_get'))


def _calculate_chart_data(equipment, inspection_records):
    """設備詳細画面のチャート用データを計算して辞書で返す。"""
    # 時系列昇順に並び替える
    records_asc = list(reversed(inspection_records))

    # Chart④：点検間隔トレンド用データ
    scheduled_days = round(equipment.inspection_interval_months * 30.4)

    # 定期点検のみを抽出するフィルター（日次・週次モニタリング記録を除外）
    # 設定間隔の40%以上の間隔がある記録のみを定期点検とみなす
    min_gap_days = max(7, round(scheduled_days * 0.4))
    formal_records = []
    prev_date = None
    for r in records_asc:
        if prev_date is None or (r.inspected_at - prev_date).days >= min_gap_days:
            formal_records.append(r)
            prev_date = r.inspected_at

    # チャート表示は直近60件に絞る（横軸が読みやすい範囲）
    chart_records = formal_records[-60:]

    # チャート横軸ラベル（実施日）
    chart_labels = [str(r.inspected_at) for r in chart_records]

    # 各点検の間隔日数（1件目は前回がないのでNull）
    interval_values = [None]
    for i in range(1, len(chart_records)):
        days = (chart_records[i].inspected_at - chart_records[i - 1].inspected_at).days
        interval_values.append(days)

    # 各点検が設定間隔を超過しているかフラグ（1件目は比較不可のためNone）
    interval_over_scheduled = [None] + [
        (v > scheduled_days) if v is not None else None
        for v in interval_values[1:]
    ]

    return {
        "formal_records":          formal_records,
        "scheduled_days":          scheduled_days,
        "chart_labels":            chart_labels,
        "interval_values":         interval_values,
        "interval_over_scheduled": interval_over_scheduled,
    }


def _calculate_equipment_metrics(equipment, formal_records):
    """設備指標（稼働率・遵守率）を定期点検記録から計算して辞書で返す。
    記録が0件の場合は None を返す。
    """
    total = len(formal_records)
    if total == 0:
        return None

    # 点検ベース稼働率：正常点検の割合
    normal_count = sum(1 for r in formal_records if r.status == 'normal')
    availability  = round(normal_count / total * 100, 1)

    # 点検遵守率：expected_inspection_date が NULL の既存レコードは
    # 設定間隔（カレンダー月単位）で期待日を補完する（2件目以降のみ）
    # timedelta(days) ではなく relativedelta(months) を使うことで、
    # 31日の月でも「翌月同日」を正しく期限日として扱える
    prev_inspected = None
    for r in formal_records:
        if r.expected_inspection_date is None and prev_inspected is not None:
            r.expected_inspection_date = prev_inspected + relativedelta(months=equipment.inspection_interval_months)
        prev_inspected = r.inspected_at

    records_with_exp = [r for r in formal_records if r.expected_inspection_date]
    if records_with_exp:
        on_time      = sum(1 for r in records_with_exp if r.inspected_at <= r.expected_inspection_date)
        compliance   = round(on_time / len(records_with_exp) * 100, 1)
        compliance_n = len(records_with_exp)
    else:
        compliance   = None
        compliance_n = 0

    return {
        'total':        total,
        'normal_count': normal_count,
        'availability': availability,
        'compliance':   compliance,
        'compliance_n': compliance_n,
    }
