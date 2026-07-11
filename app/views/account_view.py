"""
アカウント管理画面用ビュー
URLルール: /accounts/*
アクセス権限: root・admin のみ
"""

from flask import render_template, session, redirect, url_for, request, flash
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash

from app.dao.user_dao import UserDao
from app.dao.equipment_dao import EquipmentDao
from app.dto.user_dto import UserDto
from app.utils import admin_required, login_required, is_valid_email


class AccountForm(FlaskForm):
    """アカウント管理フォーム（CSRFトークン生成用）"""
    pass


@admin_required
def account_list_get():
    """
    アカウント一覧画面を表示する（GET /accounts）
    キーワード・ロール・拠点で絞り込みができる。
    """
    try:
        # 検索・絞り込みパラメータをGETから取得する
        keyword = request.args.get("keyword", "").strip()
        selected_role = request.args.get("role", "")
        selected_base = request.args.get("base", "")

        # 条件に合うユーザー一覧と拠点プルダウン用一覧を取得する
        dao = UserDao()
        user_list = dao.find_by_conditions(
            keyword=keyword or None,
            role=selected_role or None,
            base=selected_base or None,
        )
        base_list = dao.find_distinct_bases()
        dao.close()

        form = AccountForm()
        return render_template(
            "account/list.html",
            user_list=user_list,
            base_list=base_list,
            keyword=keyword,
            selected_role=selected_role,
            selected_base=selected_base,
            form=form,
        )

    except Exception as e:
        raise e


@admin_required
def account_new_get():
    """
    アカウント登録画面を表示する（GET /accounts/new）
    """
    try:
        # admin 用に既存拠点一覧を取得する（プルダウン表示用）
        dao = UserDao()
        base_list = dao.find_distinct_bases()
        dao.close()

        form = AccountForm()
        return render_template("account/new.html", form=form, form_data=None, error_message=None, base_list=base_list)

    except Exception as e:
        raise e


@admin_required
def account_new_post():
    """
    アカウント登録処理を行う（POST /accounts/new）
    バリデーション → 重複チェック → パスワードハッシュ化 → DB登録
    """
    try:
        # ログインユーザーのロールを取得する（指定可能ロールの制御に使用）
        login_role = session["user"]["role"]

        # リクエストパラメータを取得する
        employee_no = request.form.get("employee_no", "").strip()
        last_name   = request.form.get("last_name", "").strip()
        first_name  = request.form.get("first_name", "").strip()
        email       = request.form.get("email", "").strip()
        password    = request.form.get("password", "").strip()
        role        = request.form.get("role", "").strip()
        phone       = request.form.get("phone", "").strip()
        base        = request.form.get("base", "").strip()
        # root が「新規追加」を選択した場合は入力欄の値を使用する
        if base == "__new__":
            base = request.form.get("base_new", "").strip()

        # フォームの入力値を再表示用にまとめる
        form = AccountForm()
        form_data = request.form

        # admin 用に既存拠点一覧を取得する（エラー時の再表示用）
        dao_base = UserDao()
        base_list = dao_base.find_distinct_bases()
        dao_base.close()

        # 必須項目の入力チェックを行う
        if not all([employee_no, last_name, first_name, email, password, role]):
            return render_template(
                "account/new.html",
                form=form,
                form_data=form_data,
                error_message="入力情報に誤りがあります。必須項目をすべて入力してください。",
                base_list=base_list,
            )

        # ロールの指定範囲チェックを行う（root は新規登録不可 / admin は engineer のみ指定可）
        if role == "root" or (login_role == "admin" and role != "engineer"):
            return render_template(
                "account/new.html",
                form=form,
                form_data=form_data,
                error_message="このロールは指定できません。",
                base_list=base_list,
            )

        # メールアドレスの形式チェックを行う
        if not is_valid_email(email):
            return render_template(
                "account/new.html",
                form=form,
                form_data=form_data,
                error_message="メールアドレスが正しくありません。",
                base_list=base_list,
            )

        dao = UserDao()

        # 社員番号の重複チェックを行う
        existing_by_no = dao.find_by_employee_no(employee_no)
        if existing_by_no:
            dao.close()
            return render_template(
                "account/new.html",
                form=form,
                form_data=form_data,
                error_message="この社員番号は既に使用されています。",
                base_list=base_list,
            )

        # メールアドレスの重複チェックを行う
        existing_by_email = dao.find_by_email(email)
        if existing_by_email:
            dao.close()
            return render_template(
                "account/new.html",
                form=form,
                form_data=form_data,
                error_message="このメールアドレスは既に使用されています。",
                base_list=base_list,
            )

        # パスワードをハッシュ化する
        hashed_password = generate_password_hash(password)

        # UserDto を生成してDB に登録する
        dto = UserDto()
        dto.employee_no = employee_no
        dto.last_name   = last_name
        dto.first_name  = first_name
        dto.email       = email
        dto.password    = hashed_password
        dto.role        = role
        dto.phone       = phone if phone else None
        dto.base        = base if base else None

        dao.create(dto)
        dao.close()

        return redirect(url_for("account_list_get"))

    except Exception as e:
        raise e


@admin_required
def account_detail_get(id):
    """
    アカウント詳細画面を表示する（GET /accounts/<int:id>）
    担当設備一覧も同時に取得して渡す。
    """
    try:
        # ユーザー情報を取得する
        dao_user = UserDao()
        user = dao_user.find_by_id(id)
        dao_user.close()

        # ユーザーが存在しない場合は404エラーを返す
        if not user:
            from flask import abort
            abort(404)

        # 担当設備一覧を取得する
        dao_equipment = EquipmentDao()
        assigned_equipment_list = dao_equipment.find_by_user_id(id)
        dao_equipment.close()

        # admin 用に既存拠点一覧を取得する（プルダウン表示用）
        dao_base = UserDao()
        base_list = dao_base.find_distinct_bases()
        dao_base.close()

        form = AccountForm()
        # back パラメータで戻り先を決定する（'dashboard' ならダッシュボード、それ以外はアカウント一覧）
        back = request.args.get('back', 'list')
        back_url = url_for('dashboard_get') if back == 'dashboard' else url_for('account_list_get')
        return render_template(
            "account/detail.html",
            user=user,
            assigned_equipment_list=assigned_equipment_list,
            form=form,
            error_message=None,
            base_list=base_list,
            back_url=back_url,
        )

    except Exception as e:
        raise e


@admin_required
def account_detail_post(id):
    """
    アカウント編集処理を行う（POST /accounts/<int:id>）
    ロール別の権限制御・重複チェック → DB更新
    """
    try:
        # ログインユーザーのロールを取得する
        login_role = session["user"]["role"]

        # CSRFトークン生成用フォームを作成する
        form = AccountForm()

        # admin 用に既存拠点一覧を取得する（エラー時の再表示用）
        dao_base = UserDao()
        base_list = dao_base.find_distinct_bases()
        dao_base.close()

        # 編集対象ユーザーを取得する
        dao = UserDao()
        target_user = dao.find_by_id(id)

        if not target_user:
            dao.close()
            from flask import abort
            abort(404)

        # リクエストパラメータを取得する
        employee_no = request.form.get("employee_no", "").strip()
        # root 以外のログインユーザーは社員番号を変更できないため、既存値を使用する
        if login_role != "root":
            employee_no = target_user.employee_no
        last_name  = request.form.get("last_name", "").strip()
        first_name = request.form.get("first_name", "").strip()
        email      = request.form.get("email", "").strip()
        role       = request.form.get("role", "").strip()
        phone      = request.form.get("phone", "").strip()
        base       = request.form.get("base", "").strip()
        # root が「新規追加」を選択した場合は入力欄の値を使用する
        if base == "__new__":
            base = request.form.get("base_new", "").strip()

        # 担当設備一覧（再表示用）
        dao_equipment = EquipmentDao()
        assigned_equipment_list = dao_equipment.find_by_user_id(id)
        dao_equipment.close()

        # 必須項目の入力チェックを行う
        if not all([employee_no, last_name, first_name, email, role]):
            dao.close()
            return render_template(
                "account/detail.html",
                user=target_user,
                assigned_equipment_list=assigned_equipment_list,
                form=form,
                error_message="入力情報に誤りがあります。必須項目をすべて入力してください。",
                base_list=base_list,
            )

        # root 以外のアカウントへの root 権限の付与を拒否する
        if role == "root" and target_user.role != "root":
            dao.close()
            return render_template(
                "account/detail.html",
                user=target_user,
                assigned_equipment_list=assigned_equipment_list,
                form=form,
                error_message="root権限を他のアカウントに付与することはできません。",
                base_list=base_list,
            )

        # admin は root・admin アカウントの編集および admin 権限の付与を拒否する
        if login_role == "admin":
            if target_user.role in ["root", "admin"]:
                dao.close()
                return render_template(
                    "account/detail.html",
                    user=target_user,
                    assigned_equipment_list=assigned_equipment_list,
                    form=form,
                    error_message="このアカウントは編集できません。",
                    base_list=base_list,
                )
            if role == "admin":
                dao.close()
                return render_template(
                    "account/detail.html",
                    user=target_user,
                    assigned_equipment_list=assigned_equipment_list,
                    form=form,
                    error_message="このロールは指定できません。",
                    base_list=base_list,
                )

        # メールアドレスの形式チェックを行う
        if not is_valid_email(email):
            dao.close()
            return render_template(
                "account/detail.html",
                user=target_user,
                assigned_equipment_list=assigned_equipment_list,
                form=form,
                error_message="メールアドレスが正しくありません。",
                base_list=base_list,
            )

        # 社員番号の重複チェックを行う（自分自身を除く）
        existing_by_no = dao.find_by_employee_no(employee_no)
        if existing_by_no and existing_by_no.id != id:
            dao.close()
            return render_template(
                "account/detail.html",
                user=target_user,
                assigned_equipment_list=assigned_equipment_list,
                form=form,
                error_message="この社員番号は既に使用されています。",
                base_list=base_list,
            )

        # メールアドレスの重複チェックを行う（自分自身を除く）
        existing_by_email = dao.find_by_email(email)
        if existing_by_email and existing_by_email.id != id:
            dao.close()
            return render_template(
                "account/detail.html",
                user=target_user,
                assigned_equipment_list=assigned_equipment_list,
                form=form,
                error_message="このメールアドレスは既に使用されています。",
                base_list=base_list,
            )

        # UserDto を生成して DB を更新する
        dto = UserDto()
        dto.id          = id
        dto.employee_no = employee_no
        dto.last_name   = last_name
        dto.first_name  = first_name
        dto.email       = email
        dto.password    = target_user.password  # パスワードは変更しないため既存値を引き継ぐ
        dto.role        = role
        dto.phone       = phone if phone else None
        dto.base        = base if base else None

        dao.update(dto)
        dao.close()

        return redirect(url_for("account_list_get"))  # アカウント情報保存後はリストへ

    except Exception as e:
        raise e


@admin_required
def account_password_post(id):
    """
    パスワード変更処理を行う（POST /accounts/<int:id>/password）
    自分自身の変更は現在のパスワード照合が必要。他ユーザーは管理者リセットとして照合不要。
    """
    try:
        # 編集対象ユーザーを取得する
        dao = UserDao()
        target_user = dao.find_by_id(id)

        if not target_user:
            dao.close()
            from flask import abort
            abort(404)

        # admin は root のパスワードを変更できない
        login_role = session["user"]["role"]
        if login_role == "admin" and target_user.role == "root":
            dao.close()
            dao_equipment = EquipmentDao()
            assigned_equipment_list = dao_equipment.find_by_user_id(id)
            dao_equipment.close()
            return render_template(
                "account/detail.html",
                user=target_user,
                assigned_equipment_list=assigned_equipment_list,
                form=AccountForm(),
                error_message="rootのパスワードは変更できません。",
            )

        # 担当設備一覧（再表示用）
        dao_equipment = EquipmentDao()
        assigned_equipment_list = dao_equipment.find_by_user_id(id)
        dao_equipment.close()

        form = AccountForm()

        # フォーム入力値を取得する
        current_password = request.form.get("current_password", "").strip()
        new_password     = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # 新しいパスワードの入力チェックを行う
        if not new_password or not confirm_password:
            dao.close()
            return render_template(
                "account/detail.html",
                user=target_user,
                assigned_equipment_list=assigned_equipment_list,
                form=form,
                error_message="新しいパスワードを2回入力してください。",
            )

        # 新しいパスワードと確認用パスワードの一致チェックを行う
        if new_password != confirm_password:
            dao.close()
            return render_template(
                "account/detail.html",
                user=target_user,
                assigned_equipment_list=assigned_equipment_list,
                form=form,
                error_message="新しいパスワードが一致しません。",
            )

        # 自分自身のパスワード変更の場合は現在のパスワードを照合する
        login_user_id = session["user"]["id"]
        if login_user_id == id:
            if not current_password:
                dao.close()
                return render_template(
                    "account/detail.html",
                    user=target_user,
                    assigned_equipment_list=assigned_equipment_list,
                    form=form,
                    error_message="現在のパスワードを入力してください。",
                )
            if not check_password_hash(target_user.password, current_password):
                dao.close()
                return render_template(
                    "account/detail.html",
                    user=target_user,
                    assigned_equipment_list=assigned_equipment_list,
                    form=form,
                    error_message="現在のパスワードが正しくありません。",
                )

        # 新しいパスワードをハッシュ化してDBを更新する
        dto = UserDto()
        dto.id          = id
        dto.employee_no = target_user.employee_no
        dto.last_name   = target_user.last_name
        dto.first_name  = target_user.first_name
        dto.email       = target_user.email
        dto.password    = generate_password_hash(new_password)
        dto.role        = target_user.role
        dto.phone       = target_user.phone
        dto.base        = target_user.base

        dao.update(dto)
        dao.close()

        # 成功後は同じ詳細ページに戻り成功メッセージを表示する
        dao2 = UserDao()
        updated_user = dao2.find_by_id(id)
        dao2.close()
        dao_equipment2 = EquipmentDao()
        assigned_equipment_list2 = dao_equipment2.find_by_user_id(id)
        dao_equipment2.close()
        return render_template(
            "account/detail.html",
            user=updated_user,
            assigned_equipment_list=assigned_equipment_list2,
            form=AccountForm(),
            error_message=None,
            password_error=None,
            password_success="パスワードを変更しました。",
        )

    except Exception as e:
        raise e


@admin_required
def account_bulk_delete_post():
    """
    複数のアカウントを一括論理削除する（POST /accounts/bulk-delete）
    admin は engineer のみ削除可。root は全ロール削除可。
    """
    try:
        login_role = session["user"]["role"]
        deleted_by = session["user"]["id"]

        # フォームから選択アカウントIDを取得する
        id_list_str = request.form.get("user_ids", "")
        user_ids = [int(i) for i in id_list_str.split(",") if i.strip().isdigit()]
        if not user_ids:
            return redirect(url_for("account_list_get"))

        dao = UserDao()
        # ロール権限に応じて削除対象を絞り込む（admin は engineer のみ / 自分自身は削除不可）
        for user_id in user_ids:
            target = dao.find_by_id(user_id)
            if not target:
                continue
            if user_id == deleted_by:
                continue
            if login_role == "admin" and target.role != "engineer":
                continue
            # 担当設備の unassign と audit_log 記録は dao.delete() 内で行う
            dao.delete(user_id, deleted_by)

        dao.close()
        return redirect(url_for("account_list_get"))

    except Exception as e:
        raise e


@admin_required
def account_bulk_edit_post():
    """
    複数のアカウントのロール・拠点を一括更新する（POST /accounts/bulk-edit）
    admin は engineer のみ変更可。root は全ロール変更可。
    """
    try:
        login_role = session["user"]["role"]
        changed_by = session["user"]["id"]

        # フォームから選択アカウントIDを取得する
        id_list_str = request.form.get("user_ids", "")
        user_ids = [int(i) for i in id_list_str.split(",") if i.strip().isdigit()]
        if not user_ids:
            return redirect(url_for("account_list_get"))

        # 変更するフィールドを取得する（空文字は変更なしとして無視する）
        bulk_role = request.form.get("bulk_role", "").strip()
        bulk_base = request.form.get("bulk_base", "").strip()

        update_fields = {}
        if bulk_role:
            # admin は engineer 以外のロールを指定できない
            if login_role == "admin" and bulk_role != "engineer":
                bulk_role = ""
            if bulk_role:
                update_fields["role"] = bulk_role
        if bulk_base:
            # "clear" の場合は NULL にする
            update_fields["base"] = None if bulk_base == "__clear__" else bulk_base

        if not update_fields:
            return redirect(url_for("account_list_get"))

        # admin の場合は root/admin アカウントをスキップする
        skip_roles = ["root", "admin"] if login_role == "admin" else None

        dao = UserDao()
        updated_count, batch_id = dao.bulk_update(
            user_ids, update_fields, changed_by, skip_roles=skip_roles
        )
        dao.close()

        # 元に戻す機能のためにバッチIDと変更フィールドをセッションに保存する
        if batch_id:
            session["last_account_bulk_edit"] = {
                "batch_id": batch_id,
                "updated_fields": list(update_fields.keys()),
                "count": updated_count,
            }

        return redirect(url_for("account_list_get"))

    except Exception as e:
        raise e


@admin_required
def account_bulk_revert_post():
    """
    直前のアカウント一括編集を元に戻す（POST /accounts/bulk-revert）
    """
    try:
        # セッションから一括編集のバッチIDと変更フィールドを取得する
        last_edit = session.get("last_account_bulk_edit")
        if not last_edit or not last_edit.get("batch_id"):
            return redirect(url_for("account_list_get"))

        batch_id = last_edit["batch_id"]
        updated_fields = last_edit["updated_fields"]
        reverted_by = session["user"]["id"]

        dao = UserDao()
        dao.revert_bulk_edit(batch_id, updated_fields, reverted_by)
        dao.close()

        # セッションから一括編集履歴を削除する（二重revert防止）
        session.pop("last_account_bulk_edit", None)

        return redirect(url_for("account_list_get"))

    except Exception as e:
        raise e


@admin_required
def account_delete_post(id):
    """
    アカウント削除処理を行う（POST /accounts/<int:id>/delete）
    ロール別の削除権限を確認してから削除する。
    """
    try:
        # ログインユーザーのロールを取得する
        login_role = session["user"]["role"]

        # 削除対象ユーザーを取得する
        dao = UserDao()
        target_user = dao.find_by_id(id)

        if not target_user:
            dao.close()
            from flask import abort
            abort(404)

        # 自分自身は削除できない（ロールに関わらず）
        if target_user.id == session["user"]["id"]:
            dao.close()
            flash("自分のアカウントは削除できません。", "danger")
            return redirect(url_for("account_list_get"))

        # 削除権限を確認する（admin は engineer のみ / root は全ロール削除可）
        if login_role == "admin" and target_user.role != "engineer":
            dao.close()
            return redirect(url_for("account_list_get"))

        # 担当設備の unassign と audit_log 記録は dao.delete() 内で行う
        # 点検記録は論理削除後も履歴として保持されるため、件数に関わらず削除可能
        deleted_by = session["user"]["id"]
        dao.delete(id, deleted_by)
        dao.close()

        flash("アカウントを削除しました", "success")
        return redirect(url_for("account_list_get"))

    except Exception as e:
        raise e


@login_required
def my_password_get():
    """
    自分のパスワード変更画面を表示する（GET /my/password）
    ロールに関わらずログイン済みの全ユーザーがアクセスできる。
    """
    form = AccountForm()
    return render_template("account/my_password.html", form=form, error_message=None, success_message=None)


@login_required
def my_password_post():
    """
    自分のパスワード変更処理を行う（POST /my/password）
    現在のパスワード照合 → 新しいパスワードに更新する。
    """
    try:
        form = AccountForm()
        login_user_id = session["user"]["id"]

        # ログインユーザーの情報をDBから取得する
        dao = UserDao()
        current_user = dao.find_by_id(login_user_id)

        if not current_user:
            dao.close()
            return redirect(url_for("login_get"))

        # フォーム入力値を取得する
        current_password = request.form.get("current_password", "").strip()
        new_password     = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # 現在のパスワードの入力チェック
        if not current_password:
            dao.close()
            return render_template(
                "account/my_password.html",
                form=form,
                error_message="現在のパスワードを入力してください。",
                success_message=None,
            )

        # 新しいパスワードの入力チェック
        if not new_password or not confirm_password:
            dao.close()
            return render_template(
                "account/my_password.html",
                form=form,
                error_message="新しいパスワードを2回入力してください。",
                success_message=None,
            )

        # 新しいパスワードの一致チェック
        if new_password != confirm_password:
            dao.close()
            return render_template(
                "account/my_password.html",
                form=form,
                error_message="新しいパスワードが一致しません。",
                success_message=None,
            )

        # 現在のパスワードの照合
        if not check_password_hash(current_user.password, current_password):
            dao.close()
            return render_template(
                "account/my_password.html",
                form=form,
                error_message="現在のパスワードが正しくありません。",
                success_message=None,
            )

        # 新しいパスワードをハッシュ化してDBを更新する
        dto = UserDto()
        dto.id          = login_user_id
        dto.employee_no = current_user.employee_no
        dto.last_name   = current_user.last_name
        dto.first_name  = current_user.first_name
        dto.email       = current_user.email
        dto.password    = generate_password_hash(new_password)
        dto.role        = current_user.role
        dto.phone       = current_user.phone
        dto.base        = current_user.base

        dao.update(dto)
        dao.close()

        return render_template(
            "account/my_password.html",
            form=AccountForm(),
            error_message=None,
            success_message="パスワードを変更しました。",
        )

    except Exception as e:
        raise e
