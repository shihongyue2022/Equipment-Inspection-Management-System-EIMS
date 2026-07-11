"""
ゴミ箱（データリサイクル）画面用ビュー
URLルール: /recycle-bin/*
アクセス権限: root・admin のみ
"""

from flask import render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from werkzeug.security import check_password_hash

from app.dao.equipment_dao import EquipmentDao
from app.dao.user_dao import UserDao
from app.dao.inspection_dao import InspectionDao
from app.utils import admin_required


class RecycleBinForm(FlaskForm):
    """ゴミ箱フォーム（CSRFトークン生成用）"""
    pass


def _check_root_role():
    """rootロール専用チェック。rootのみ通過できる。問題なければ None を返す。"""
    user = session.get("user")
    if not user or user["role"] != "root":
        flash("この操作はROOT管理者のみ実行できます。", "danger")
        return redirect(url_for("recycle_bin_get"))
    return None


def _verify_root_password():
    """
    フォームから送信された root_password をDBのハッシュと照合する。
    一致すれば True、不一致またはDB取得失敗なら False を返す。
    """
    submitted = request.form.get("root_password", "")
    if not submitted:
        return False
    dao = UserDao()
    try:
        current_user = dao.find_by_id(session["user"]["id"])
        if current_user is None:
            return False
        return check_password_hash(current_user.password, submitted)
    finally:
        dao.close()


@admin_required
def recycle_bin_get():
    """
    ゴミ箱一覧画面を表示する（GET /recycle-bin）
    論理削除済みの設備・アカウント・点検記録を3つのタブで表示する。
    """
    dao_eq  = EquipmentDao()
    dao_usr = UserDao()
    dao_ins = InspectionDao()
    try:
        # 各テーブルの論理削除済みレコードを取得する
        deleted_equipment   = dao_eq.find_all_deleted()
        deleted_users       = dao_usr.find_all_deleted()
        deleted_inspections = dao_ins.find_all_deleted()
    finally:
        dao_eq.close()
        dao_usr.close()
        dao_ins.close()

    form = RecycleBinForm()
    return render_template(
        "recycle_bin/index.html",
        deleted_equipment=deleted_equipment,
        deleted_users=deleted_users,
        deleted_inspections=deleted_inspections,
        form=form,
    )


@admin_required
def recycle_bin_equipment_restore_post(id):
    """
    論理削除済みの設備を復元する（POST /recycle-bin/equipment/<id>/restore）
    関連する点検記録も同時に復元する。
    """
    dao = EquipmentDao()
    try:
        restored_by = session["user"]["id"]
        affected = dao.restore(id, restored_by)
        if affected:
            flash('設備を復元しました。', 'success')
        else:
            flash('復元対象が見つかりませんでした。', 'danger')
    finally:
        dao.close()

    return redirect(url_for("recycle_bin_get"))


@admin_required
def recycle_bin_user_restore_post(id):
    """
    論理削除済みのアカウントを復元する（POST /recycle-bin/user/<id>/restore）
    復元時は担当設備の割り当ても自動で復元する（他者に再割り当て済みの設備は除く）。
    """
    dao = UserDao()
    try:
        restored_by = session["user"]["id"]
        # 担当設備の割り当ては常に自動復元する（他者割り当て済みは除外）
        affected = dao.restore(id, restored_by, restore_equipment=True)
        if affected:
            flash('アカウントを復元しました。担当設備の割り当ても復元しました。', 'success')
        else:
            flash('復元対象が見つかりませんでした。', 'danger')
    finally:
        dao.close()

    return redirect(url_for("recycle_bin_get"))


def recycle_bin_equipment_hard_delete_post(id):
    """
    論理削除済みの設備を物理削除する（POST /recycle-bin/equipment/<id>/hard-delete）
    関連する点検記録も同時に物理削除する。ROOT専用。取り消し不可。
    パスワード再入力による二重認証を行う。
    """
    redirect_response = _check_root_role()
    if redirect_response:
        return redirect_response

    form = RecycleBinForm()
    if not form.validate_on_submit():
        flash('不正なリクエストです。', 'danger')
        return redirect(url_for("recycle_bin_get"))

    # ROOTパスワードを再照合する（なりすまし防止）
    if not _verify_root_password():
        flash('パスワードが正しくありません。完全削除はキャンセルされました。', 'danger')
        return redirect(url_for("recycle_bin_get"))

    dao = EquipmentDao()
    try:
        deleted_by = session["user"]["id"]
        affected = dao.hard_delete(id, deleted_by)
        if affected:
            flash('設備を完全に削除しました。この操作は取り消せません。', 'warning')
        else:
            flash('対象が見つかりませんでした（すでに削除済みの可能性があります）。', 'danger')
    finally:
        dao.close()

    return redirect(url_for("recycle_bin_get"))


@admin_required
def recycle_bin_equipment_bulk_restore_post():
    """複数の論理削除済み設備を一括復元する（POST /recycle-bin/equipment/bulk-restore）"""
    form = RecycleBinForm()
    if not form.validate_on_submit():
        flash('不正なリクエストです。', 'danger')
        return redirect(url_for("recycle_bin_get"))

    id_list_str = request.form.get('equipment_ids', '')
    equipment_ids = [int(i) for i in id_list_str.split(',') if i.strip().isdigit()]
    if not equipment_ids:
        flash('設備が選択されていません。', 'warning')
        return redirect(url_for("recycle_bin_get"))

    restored_by = session["user"]["id"]
    dao = EquipmentDao()
    try:
        count = dao.bulk_restore(equipment_ids, restored_by)
    finally:
        dao.close()

    flash(f'{count}件の設備を復元しました。関連する点検記録も復元されました。', 'success')
    return redirect(url_for("recycle_bin_get"))


@admin_required
def recycle_bin_user_bulk_restore_post():
    """複数の論理削除済みアカウントを一括復元する（POST /recycle-bin/user/bulk-restore）"""
    form = RecycleBinForm()
    if not form.validate_on_submit():
        flash('不正なリクエストです。', 'danger')
        return redirect(url_for("recycle_bin_get"))

    id_list_str = request.form.get('user_ids', '')
    user_ids = [int(i) for i in id_list_str.split(',') if i.strip().isdigit()]
    if not user_ids:
        flash('アカウントが選択されていません。', 'warning')
        return redirect(url_for("recycle_bin_get"))

    restored_by = session["user"]["id"]
    dao = UserDao()
    try:
        # 担当設備の割り当ては常に自動復元する（他者割り当て済みは除外）
        count = dao.bulk_restore(user_ids, restored_by, restore_equipment=True)
    finally:
        dao.close()

    flash(f'{count}件のアカウントを復元しました。担当設備の割り当ても復元しました。', 'success')
    return redirect(url_for("recycle_bin_get"))


def recycle_bin_equipment_bulk_hard_delete_post():
    """複数の論理削除済み設備を一括物理削除する（POST /recycle-bin/equipment/bulk-hard-delete）ROOT専用。"""
    redirect_response = _check_root_role()
    if redirect_response:
        return redirect_response

    form = RecycleBinForm()
    if not form.validate_on_submit():
        flash('不正なリクエストです。', 'danger')
        return redirect(url_for("recycle_bin_get"))

    if not _verify_root_password():
        flash('パスワードが正しくありません。完全削除はキャンセルされました。', 'danger')
        return redirect(url_for("recycle_bin_get"))

    id_list_str = request.form.get('equipment_ids', '')
    equipment_ids = [int(i) for i in id_list_str.split(',') if i.strip().isdigit()]
    if not equipment_ids:
        flash('設備が選択されていません。', 'warning')
        return redirect(url_for("recycle_bin_get"))

    deleted_by = session["user"]["id"]
    dao = EquipmentDao()
    try:
        count = dao.bulk_hard_delete_from_recycle(equipment_ids, deleted_by)
    finally:
        dao.close()

    flash(f'{count}件の設備を完全に削除しました。この操作は取り消せません。', 'warning')
    return redirect(url_for("recycle_bin_get"))


def recycle_bin_user_bulk_hard_delete_post():
    """複数の論理削除済みアカウントを一括物理削除する（POST /recycle-bin/user/bulk-hard-delete）ROOT専用。"""
    redirect_response = _check_root_role()
    if redirect_response:
        return redirect_response

    form = RecycleBinForm()
    if not form.validate_on_submit():
        flash('不正なリクエストです。', 'danger')
        return redirect(url_for("recycle_bin_get"))

    if not _verify_root_password():
        flash('パスワードが正しくありません。完全削除はキャンセルされました。', 'danger')
        return redirect(url_for("recycle_bin_get"))

    id_list_str = request.form.get('user_ids', '')
    user_ids = [int(i) for i in id_list_str.split(',') if i.strip().isdigit()]
    if not user_ids:
        flash('アカウントが選択されていません。', 'warning')
        return redirect(url_for("recycle_bin_get"))

    deleted_by = session["user"]["id"]
    dao = UserDao()
    try:
        count = dao.bulk_hard_delete_from_recycle(user_ids, deleted_by)
    finally:
        dao.close()

    flash(f'{count}件のアカウントを完全に削除しました。この操作は取り消せません。', 'warning')
    return redirect(url_for("recycle_bin_get"))


def recycle_bin_user_hard_delete_post(id):
    """
    論理削除済みのアカウントを物理削除する（POST /recycle-bin/user/<id>/hard-delete）
    担当していた点検記録と設備の担当者設定も同時にクリアする。ROOT専用。取り消し不可。
    パスワード再入力による二重認証を行う。
    """
    redirect_response = _check_root_role()
    if redirect_response:
        return redirect_response

    form = RecycleBinForm()
    if not form.validate_on_submit():
        flash('不正なリクエストです。', 'danger')
        return redirect(url_for("recycle_bin_get"))

    # ROOTパスワードを再照合する（なりすまし防止）
    if not _verify_root_password():
        flash('パスワードが正しくありません。完全削除はキャンセルされました。', 'danger')
        return redirect(url_for("recycle_bin_get"))

    dao = UserDao()
    try:
        deleted_by = session["user"]["id"]
        affected = dao.hard_delete(id, deleted_by)
        if affected:
            flash('アカウントを完全に削除しました。この操作は取り消せません。', 'warning')
        else:
            flash('対象が見つかりませんでした（すでに削除済みの可能性があります）。', 'danger')
    finally:
        dao.close()

    return redirect(url_for("recycle_bin_get"))
