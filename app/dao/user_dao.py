import json
import uuid
import pymysql
from datetime import datetime, timezone, timedelta
from app.dao.dao import Dao
from app.dto.user_dto import UserDto


class UserDao(Dao):
    """Employeeテーブルに対するDB操作メソッドを定義するDAO。"""

    def __init__(self):
        super().__init__()

    def _row_to_dto(self, row):
        """辞書1行をUserDtoに詰め替える。"""
        dto = UserDto()
        dto.id = row["id"]
        dto.employee_no = row["employee_no"]
        dto.last_name = row["last_name"]
        dto.first_name = row["first_name"]
        dto.email = row["email"]
        dto.password = row["password"]
        dto.role = row["role"]
        dto.phone = row["phone"]
        dto.base = row["base"]
        # ゴミ箱一覧でのみ値が入る（通常クエリでは None）
        dto.deleted_at = row.get("deleted_at")
        dto.deleted_by_name = row.get("deleted_by_name")
        return dto

    def find_all(self):
        """Employeeテーブルの全件を返す（論理削除済みを除く）。"""
        try:
            sql = """
                SELECT id, employee_no, last_name, first_name,
                       email, password, role, phone, base, created_at
                FROM employee
                WHERE deleted_at IS NULL
                ORDER BY id
            """
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            return [self._row_to_dto(row) for row in rows]
        except pymysql.Error as e:
            raise e

    def find_by_id(self, id):
        """Employeeテーブルのidで検索し1件返す（論理削除済みを除く）。"""
        try:
            sql = """
                SELECT id, employee_no, last_name, first_name,
                       email, password, role, phone, base, created_at
                FROM employee
                WHERE id = %s
                  AND deleted_at IS NULL
            """
            self.cursor.execute(sql, (id,))
            row = self.cursor.fetchone()
            if row is None:
                return None
            return self._row_to_dto(row)
        except pymysql.Error as e:
            raise e

    def find_by_employee_no(self, employee_no):
        """社員番号で検索し1件返す（論理削除済みを除く）。ログイン認証・重複チェックで使用する。"""
        try:
            sql = """
                SELECT id, employee_no, last_name, first_name,
                       email, password, role, phone, base, created_at
                FROM employee
                WHERE employee_no = %s
                  AND deleted_at IS NULL
            """
            self.cursor.execute(sql, (employee_no,))
            row = self.cursor.fetchone()
            if row is None:
                return None
            return self._row_to_dto(row)
        except pymysql.Error as e:
            raise e

    def find_by_email(self, email):
        """メールアドレスで検索し1件返す（論理削除済みを除く）。重複チェックで使用する。"""
        try:
            sql = """
                SELECT id, employee_no, last_name, first_name,
                       email, password, role, phone, base, created_at
                FROM employee
                WHERE email = %s
                  AND deleted_at IS NULL
            """
            self.cursor.execute(sql, (email,))
            row = self.cursor.fetchone()
            if row is None:
                return None
            return self._row_to_dto(row)
        except pymysql.Error as e:
            raise e

    def find_by_role(self, role):
        """ロールで検索し一覧を返す（論理削除済みを除く）。担当者選択用プルダウンで使用する。"""
        try:
            sql = """
                SELECT id, employee_no, last_name, first_name,
                       email, password, role, phone, base, created_at
                FROM employee
                WHERE role = %s
                  AND deleted_at IS NULL
                ORDER BY id
            """
            self.cursor.execute(sql, (role,))
            rows = self.cursor.fetchall()
            return [self._row_to_dto(row) for row in rows]
        except pymysql.Error as e:
            raise e

    def find_distinct_bases(self):
        """拠点（base）の重複なし一覧を返す（論理削除済みを除く）。NULLは除外する。"""
        try:
            sql = """
                SELECT DISTINCT base
                FROM employee
                WHERE base IS NOT NULL
                  AND deleted_at IS NULL
                ORDER BY base
            """
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            return [row["base"] for row in rows]
        except pymysql.Error as e:
            raise e

    def find_by_conditions(self, keyword=None, role=None, base=None):
        """氏名・社員番号のキーワード、ロール、拠点で絞り込んだ一覧を返す（論理削除済みを除く）。"""
        try:
            sql = """
                SELECT id, employee_no, last_name, first_name,
                       email, password, role, phone, base, created_at
                FROM employee
                WHERE deleted_at IS NULL
            """
            params = []

            # キーワードで氏名（姓＋名の結合）または社員番号を部分一致検索する
            if keyword:
                sql += " AND (CONCAT(last_name, first_name) LIKE %s OR employee_no LIKE %s)"
                like_keyword = f"%{keyword}%"
                params.extend([like_keyword, like_keyword])

            # ロールで絞り込む
            if role:
                sql += " AND role = %s"
                params.append(role)

            # 拠点で絞り込む
            if base:
                sql += " AND base = %s"
                params.append(base)

            sql += " ORDER BY id"

            self.cursor.execute(sql, params)
            rows = self.cursor.fetchall()
            return [self._row_to_dto(row) for row in rows]
        except pymysql.Error as e:
            raise e

    def find_all_deleted(self):
        """論理削除済みのアカウント一覧を返す（ゴミ箱表示用）。"""
        try:
            sql = """
                SELECT
                    emp.id,
                    emp.employee_no,
                    emp.last_name,
                    emp.first_name,
                    emp.email,
                    emp.password,
                    emp.role,
                    emp.phone,
                    emp.base,
                    emp.created_at,
                    emp.deleted_at,
                    CASE
                        WHEN deleter.last_name IS NOT NULL
                        THEN CONCAT(deleter.last_name, deleter.first_name)
                        ELSE NULL
                    END AS deleted_by_name
                FROM employee emp
                LEFT JOIN employee deleter ON emp.deleted_by = deleter.id
                WHERE emp.deleted_at IS NOT NULL
                ORDER BY emp.deleted_at DESC
            """
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            return [self._row_to_dto(row) for row in rows]
        except pymysql.Error as e:
            raise e

    def create(self, dto):
        """Employeeテーブルに新規レコードを挿入する。"""
        try:
            sql = """
                INSERT INTO employee
                    (employee_no, last_name, first_name, email, password, role, phone, base)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(sql, (
                dto.employee_no,
                dto.last_name,
                dto.first_name,
                dto.email,
                dto.password,
                dto.role,
                dto.phone,
                dto.base,
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def update(self, dto):
        """Employeeテーブルの既存レコードを上書きする。"""
        try:
            sql = """
                UPDATE employee
                SET employee_no = %s,
                    last_name   = %s,
                    first_name  = %s,
                    email       = %s,
                    password    = %s,
                    role        = %s,
                    phone       = %s,
                    base        = %s
                WHERE id = %s
            """
            self.cursor.execute(sql, (
                dto.employee_no,
                dto.last_name,
                dto.first_name,
                dto.email,
                dto.password,
                dto.role,
                dto.phone,
                dto.base,
                dto.id,
            ))
            self.conn.commit()
            return self.cursor.rowcount
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def delete(self, id, deleted_by):
        """アカウントを論理削除する。担当設備は未割り当てにし、IDをaudit_logに記録する。"""
        try:
            # 削除前にアカウントデータを取得する（audit_log用）
            self.cursor.execute(
                "SELECT * FROM employee WHERE id = %s AND deleted_at IS NULL",
                (id,)
            )
            old_row = self.cursor.fetchone()
            if old_row is None:
                # 既に削除済みまたは存在しない
                return 0

            # 担当設備IDを取得してaudit_logに記録する（復元時に割り当てを戻せるようにする）
            self.cursor.execute(
                "SELECT id FROM equipment WHERE assigned_user_id = %s AND deleted_at IS NULL",
                (id,)
            )
            eq_rows = self.cursor.fetchall()
            if eq_rows:
                eq_ids = [row['id'] for row in eq_rows]
                self._log_audit(
                    'employee', id, 'EQUIPMENT_UNASSIGN',
                    {'equipment_ids': eq_ids}, deleted_by
                )
                # 担当設備の assigned_user_id を NULL にする
                self.cursor.execute(
                    "UPDATE equipment SET assigned_user_id = NULL WHERE assigned_user_id = %s",
                    (id,)
                )

            # 日本時間（JST）で現在日時を取得する
            jst = timezone(timedelta(hours=9))
            now_jst = datetime.now(jst).replace(tzinfo=None)

            # アカウントを論理削除する
            self.cursor.execute(
                "UPDATE employee SET deleted_at = %s, deleted_by = %s WHERE id = %s AND deleted_at IS NULL",
                (now_jst, deleted_by, id)
            )
            emp_affected = self.cursor.rowcount

            # 点検記録は過去の実績として残すため削除しない（担当者が削除されても履歴は保持する）

            # audit_logにアカウントの削除を記録する
            self._log_audit('employee', id, 'DELETE', old_row, deleted_by)

            self.conn.commit()
            return emp_affected
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def restore(self, id, restored_by, restore_equipment=False):
        """論理削除済みのアカウントを復元する。restore_equipment=True の場合は担当設備の割り当ても戻す。"""
        try:
            # アカウントを復元する
            self.cursor.execute(
                "UPDATE employee SET deleted_at = NULL, deleted_by = NULL"
                " WHERE id = %s AND deleted_at IS NOT NULL",
                (id,)
            )
            emp_affected = self.cursor.rowcount

            # 担当設備の割り当てを復元する（オプション）
            if restore_equipment and emp_affected:
                self.cursor.execute(
                    "SELECT old_data FROM audit_log"
                    " WHERE table_name = 'employee' AND record_id = %s AND action = 'EQUIPMENT_UNASSIGN'"
                    " ORDER BY changed_at DESC LIMIT 1",
                    (id,)
                )
                eq_log = self.cursor.fetchone()
                if eq_log and eq_log['old_data']:
                    eq_ids = json.loads(eq_log['old_data']).get('equipment_ids', [])
                    if eq_ids:
                        eq_placeholders = ', '.join('%s' for _ in eq_ids)
                        # 現在未割り当ての設備のみ復元する（既に別の担当者がいる設備は上書きしない）
                        self.cursor.execute(
                            f"UPDATE equipment SET assigned_user_id = %s"
                            f" WHERE id IN ({eq_placeholders})"
                            f"   AND assigned_user_id IS NULL AND deleted_at IS NULL",
                            [id] + eq_ids
                        )

            # audit_logに復元を記録する
            self._log_audit('employee', id, 'RESTORE', None, restored_by)

            self.conn.commit()
            return emp_affected
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def hard_delete(self, id, deleted_by):
        """
        論理削除済みのアカウントを物理削除する（取り消し不可）。
        ① 担当設備の assigned_user_id を NULL にする
        ② 担当していた点検記録を物理削除する（engineer_id NOT NULL制約のため）
        ③ アカウントを物理削除する
        audit_logに記録してからDELETEする。
        対象: deleted_at IS NOT NULL のアカウントのみ（ゴミ箱にある社員に限定）。
        """
        try:
            # 対象アカウントを取得する（ゴミ箱にある社員のみ）
            self.cursor.execute(
                "SELECT * FROM employee WHERE id = %s AND deleted_at IS NOT NULL",
                (id,)
            )
            old_row = self.cursor.fetchone()
            if old_row is None:
                return 0

            # 担当していた点検記録を取得する（audit_log用）
            self.cursor.execute(
                "SELECT * FROM inspection_records WHERE engineer_id = %s",
                (id,)
            )
            ir_rows = self.cursor.fetchall()

            # audit_logに物理削除を記録してから削除する
            self._log_audit('employee', id, 'HARD_DELETE', old_row, deleted_by)
            for ir in ir_rows:
                self._log_audit('inspection_records', ir['id'], 'HARD_DELETE', ir, deleted_by)

            # 担当設備の assigned_user_id を NULL に更新する（FK参照を解除する）
            self.cursor.execute(
                "UPDATE equipment SET assigned_user_id = NULL WHERE assigned_user_id = %s",
                (id,)
            )

            # 点検記録を先に物理削除する（engineer_id の FK制約 NOT NULL のため先に削除する）
            self.cursor.execute(
                "DELETE FROM inspection_records WHERE engineer_id = %s",
                (id,)
            )

            # アカウントを物理削除する
            self.cursor.execute(
                "DELETE FROM employee WHERE id = %s AND deleted_at IS NOT NULL",
                (id,)
            )
            emp_affected = self.cursor.rowcount

            self.conn.commit()
            return emp_affected
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def bulk_update(self, user_ids, update_fields, changed_by, skip_roles=None):
        """複数のユーザーのフィールドを一括更新する。変更前の値を audit_log に記録する。

        Args:
            user_ids (list[int]): 更新対象のユーザーIDリスト
            update_fields (dict): {フィールド名: 新しい値} の辞書（role / base のみ許可）
            changed_by (int): 操作者のemployee.id
            skip_roles (list[str]|None): このロールを持つユーザーはスキップする（admin操作時に使用）

        Returns:
            tuple[int, str]: (更新された行数, batch_id)
        """
        # SQLインジェクション対策として更新を許可するフィールド名を明示的に指定する
        ALLOWED_FIELDS = {'role', 'base'}
        safe_fields = {k: v for k, v in update_fields.items() if k in ALLOWED_FIELDS}
        if not safe_fields or not user_ids:
            return 0, None

        try:
            placeholders = ', '.join('%s' for _ in user_ids)

            # スキップするロールが指定されている場合は対象IDを絞り込む（admin 操作時に root/admin を除外する）
            if skip_roles:
                skip_placeholders = ', '.join('%s' for _ in skip_roles)
                self.cursor.execute(
                    f"SELECT id FROM employee WHERE id IN ({placeholders})"
                    f" AND role NOT IN ({skip_placeholders}) AND deleted_at IS NULL",
                    list(user_ids) + list(skip_roles)
                )
                target_ids = [row['id'] for row in self.cursor.fetchall()]
            else:
                target_ids = list(user_ids)

            if not target_ids:
                return 0, None

            target_placeholders = ', '.join('%s' for _ in target_ids)

            # 更新前のユーザーデータを取得する（audit_log用・元に戻す機能で使用する）
            self.cursor.execute(
                f"SELECT * FROM employee WHERE id IN ({target_placeholders}) AND deleted_at IS NULL",
                target_ids
            )
            old_rows = self.cursor.fetchall()

            # 今回の一括操作をグループ化するためのIDを生成する
            batch_id = str(uuid.uuid4())

            # 各ユーザーの変更前データを audit_log に記録する
            for row in old_rows:
                self._log_audit('employee', row['id'], 'BULK_UPDATE', row, changed_by, batch_id=batch_id)

            # SET句を動的に構築する（例: "role = %s, base = %s"）
            set_clause = ', '.join(f'{field} = %s' for field in safe_fields.keys())
            # バインド変数：SET句の値 + WHERE IN句のIDリスト
            values = list(safe_fields.values()) + target_ids

            sql = f"""
                UPDATE employee
                SET {set_clause}
                WHERE id IN ({target_placeholders})
                  AND deleted_at IS NULL
            """
            self.cursor.execute(sql, values)
            self.conn.commit()
            return self.cursor.rowcount, batch_id
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def revert_bulk_edit(self, batch_id, updated_fields, reverted_by):
        """一括編集を元に戻す。audit_log の old_data から変更前の値を復元する。

        Args:
            batch_id (str): 元に戻す一括編集のバッチID
            updated_fields (list[str]): 復元するフィールド名のリスト
            reverted_by (int): 操作者のemployee.id

        Returns:
            int: 復元された行数
        """
        ALLOWED_FIELDS = {'role', 'base'}
        safe_fields = [f for f in updated_fields if f in ALLOWED_FIELDS]
        if not safe_fields or not batch_id:
            return 0

        try:
            # batch_id に対応する audit_log エントリを取得する
            self.cursor.execute(
                "SELECT record_id, old_data FROM audit_log"
                " WHERE batch_id = %s AND table_name = 'employee'",
                (batch_id,)
            )
            entries = self.cursor.fetchall()
            if not entries:
                return 0

            reverted_count = 0
            for entry in entries:
                user_id = entry['record_id']
                old_data = json.loads(entry['old_data']) if entry['old_data'] else {}

                # 復元するフィールドと旧値のみ抽出する
                restore_values = {f: old_data[f] for f in safe_fields if f in old_data}
                if not restore_values:
                    continue

                # 現在の値を audit_log に記録してから復元する（操作履歴として残す）
                self.cursor.execute(
                    "SELECT * FROM employee WHERE id = %s AND deleted_at IS NULL",
                    (user_id,)
                )
                current_row = self.cursor.fetchone()
                if current_row is None:
                    continue
                self._log_audit('employee', user_id, 'BULK_REVERT', current_row, reverted_by)

                # 旧値に戻す
                set_clause = ', '.join(f'{f} = %s' for f in restore_values.keys())
                values = list(restore_values.values()) + [user_id]
                self.cursor.execute(
                    f"UPDATE employee SET {set_clause} WHERE id = %s AND deleted_at IS NULL",
                    values
                )
                reverted_count += self.cursor.rowcount

            self.conn.commit()
            return reverted_count
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def bulk_restore(self, user_ids, restored_by, restore_equipment=False):
        """複数の論理削除済みアカウントを一括復元する。restore_equipment=True の場合は担当設備の割り当ても戻す。"""
        if not user_ids:
            return 0
        try:
            placeholders = ', '.join('%s' for _ in user_ids)

            # アカウントを一括復元する
            self.cursor.execute(
                f"UPDATE employee SET deleted_at = NULL, deleted_by = NULL"
                f" WHERE id IN ({placeholders}) AND deleted_at IS NOT NULL",
                user_ids
            )
            emp_affected = self.cursor.rowcount

            # 担当設備の割り当てを復元する（オプション）
            if restore_equipment and emp_affected:
                for user_id in user_ids:
                    self.cursor.execute(
                        "SELECT old_data FROM audit_log"
                        " WHERE table_name = 'employee' AND record_id = %s AND action = 'EQUIPMENT_UNASSIGN'"
                        " ORDER BY changed_at DESC LIMIT 1",
                        (user_id,)
                    )
                    eq_log = self.cursor.fetchone()
                    if eq_log and eq_log['old_data']:
                        eq_ids = json.loads(eq_log['old_data']).get('equipment_ids', [])
                        if eq_ids:
                            eq_placeholders = ', '.join('%s' for _ in eq_ids)
                            # 現在未割り当ての設備のみ復元する（既に別の担当者がいる設備は上書きしない）
                            self.cursor.execute(
                                f"UPDATE equipment SET assigned_user_id = %s"
                                f" WHERE id IN ({eq_placeholders})"
                                f"   AND assigned_user_id IS NULL AND deleted_at IS NULL",
                                [user_id] + eq_ids
                            )

            # audit_logに各アカウントの復元を記録する
            for user_id in user_ids:
                self._log_audit('employee', user_id, 'RESTORE', None, restored_by)

            self.conn.commit()
            return emp_affected
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def bulk_hard_delete_from_recycle(self, user_ids, deleted_by):
        """複数の論理削除済みアカウントを一括物理削除する（ROOT専用・取り消し不可）。"""
        if not user_ids:
            return 0
        try:
            placeholders = ', '.join('%s' for _ in user_ids)

            # 対象アカウントを取得する（ゴミ箱にある社員のみ）
            self.cursor.execute(
                f"SELECT * FROM employee WHERE id IN ({placeholders}) AND deleted_at IS NOT NULL",
                user_ids
            )
            old_rows = self.cursor.fetchall()
            if not old_rows:
                return 0

            target_ids = [row['id'] for row in old_rows]
            target_placeholders = ', '.join('%s' for _ in target_ids)

            # 担当していた点検記録を取得する（audit_log用）
            self.cursor.execute(
                f"SELECT * FROM inspection_records WHERE engineer_id IN ({target_placeholders})",
                target_ids
            )
            ir_rows = self.cursor.fetchall()

            # audit_logに記録してから削除する
            for row in old_rows:
                self._log_audit('employee', row['id'], 'HARD_DELETE', row, deleted_by)
            for ir in ir_rows:
                self._log_audit('inspection_records', ir['id'], 'HARD_DELETE', ir, deleted_by)

            # 担当設備のassigned_user_idをNULLにする（FK参照を解除する）
            self.cursor.execute(
                f"UPDATE equipment SET assigned_user_id = NULL WHERE assigned_user_id IN ({target_placeholders})",
                target_ids
            )

            # 点検記録を先に物理削除する（engineer_id NOT NULL制約のため）
            self.cursor.execute(
                f"DELETE FROM inspection_records WHERE engineer_id IN ({target_placeholders})",
                target_ids
            )

            # アカウントを物理削除する
            self.cursor.execute(
                f"DELETE FROM employee WHERE id IN ({target_placeholders}) AND deleted_at IS NOT NULL",
                target_ids
            )
            emp_affected = self.cursor.rowcount

            self.conn.commit()
            return emp_affected
        except pymysql.Error as e:
            self.conn.rollback()
            raise e
