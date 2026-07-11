import json
import math
import uuid
import pymysql
from datetime import date, datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from app.dao.dao import Dao
from app.dto.equipment_dto import EquipmentDto


class EquipmentDao(Dao):
    """equipmentテーブルに対するDB操作メソッドを定義するDAO。"""

    # 設備一覧取得SELECTの共通部分（FROM句・担当者JOIN含む）
    _SELECT_BASE = """
        SELECT
            e.id,
            e.name,
            e.location,
            e.equipment_type,
            e.manufacturer,
            e.model_number,
            e.installed_at,
            e.inspection_interval_months,
            e.assigned_user_id,
            e.area,
            e.next_inspection_date,
            CASE
                WHEN emp.last_name IS NOT NULL
                THEN CONCAT(emp.last_name, emp.first_name)
                ELSE NULL
            END AS assigned_user_name,
            last_ir.status AS latest_inspection_status,
            last_ir.inspected_at AS latest_inspection_date,
            last_ir.note AS latest_inspection_note
        FROM equipment e
        LEFT JOIN employee emp ON e.assigned_user_id = emp.id
    """

    # 最新点検記録を取得するLEFT JOINサブクエリ（4メソッドで共通使用）
    _LATEST_INSPECTION_JOIN = """
        LEFT JOIN (
            SELECT ir.equipment_id, ir.status, ir.inspected_at, ir.note
            FROM inspection_records ir
            INNER JOIN (
                SELECT ir1.equipment_id, MAX(ir1.id) AS max_id
                FROM inspection_records ir1
                INNER JOIN (
                    SELECT equipment_id, MAX(inspected_at) AS latest_date
                    FROM inspection_records
                    WHERE deleted_at IS NULL
                    GROUP BY equipment_id
                ) ld ON ir1.equipment_id = ld.equipment_id
                      AND ir1.inspected_at = ld.latest_date
                WHERE ir1.deleted_at IS NULL
                GROUP BY ir1.equipment_id
            ) latest ON ir.id = latest.max_id
        ) last_ir ON last_ir.equipment_id = e.id
    """

    def __init__(self):
        super().__init__()

    def _row_to_dto(self, row):
        """辞書1行をEquipmentDtoに詰め替える。"""
        dto = EquipmentDto()
        dto.id = row["id"]
        dto.name = row["name"]
        dto.location = row["location"]
        dto.equipment_type = row["equipment_type"]
        dto.manufacturer = row["manufacturer"]
        dto.model_number = row["model_number"]
        dto.installed_at = row["installed_at"]
        dto.inspection_interval_months = row["inspection_interval_months"]
        dto.assigned_user_id = row["assigned_user_id"]
        dto.assigned_user_name = row.get("assigned_user_name")
        dto.area = row.get("area")
        dto.next_inspection_date = row["next_inspection_date"]
        dto.latest_inspection_status = row.get("latest_inspection_status")
        dto.latest_inspection_date = row.get("latest_inspection_date")
        dto.latest_inspection_note = row.get("latest_inspection_note")
        # ゴミ箱一覧でのみ値が入る（通常クエリでは None）
        dto.deleted_at = row.get("deleted_at")
        dto.deleted_by_name = row.get("deleted_by_name")
        return dto

    def find_all(self):
        """全設備を返す（論理削除済みを除く）。担当者名と最新点検ステータスをJOINで付与する。"""
        try:
            sql = (
                self._SELECT_BASE
                + self._LATEST_INSPECTION_JOIN
                + """
                WHERE e.deleted_at IS NULL
                ORDER BY e.next_inspection_date IS NULL, e.next_inspection_date, e.id
                """
            )
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            return [self._row_to_dto(row) for row in rows]
        except pymysql.Error as e:
            raise e

    def find_with_filter(self, name=None, equipment_type=None, assigned_user_id=None):
        """検索条件に一致する設備一覧を返す（論理削除済みを除く）。条件が None の場合はその項目を絞り込まない。"""
        try:
            # 基本SQL（_SELECT_BASE + _LATEST_INSPECTION_JOIN を使用）
            sql = self._SELECT_BASE + self._LATEST_INSPECTION_JOIN
            # 論理削除済みを必ず除外する
            conditions = ["e.deleted_at IS NULL"]
            params = []

            if name:
                # 設備名：部分一致（LIKE）
                conditions.append("e.name LIKE %s")
                params.append(f"%{name}%")

            if equipment_type:
                # 設備種別：部分一致（LIKE）
                conditions.append("e.equipment_type LIKE %s")
                params.append(f"%{equipment_type}%")

            if assigned_user_id:
                # 担当者：完全一致
                conditions.append("e.assigned_user_id = %s")
                params.append(assigned_user_id)

            sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY e.next_inspection_date IS NULL, e.next_inspection_date, e.id"

            self.cursor.execute(sql, params)
            rows = self.cursor.fetchall()
            return [self._row_to_dto(row) for row in rows]
        except pymysql.Error as e:
            raise e

    def find_all_by_base(self, base):
        """担当者の拠点が一致する設備一覧を返す（論理削除済みを除く）。担当者名と最新点検ステータスをJOINで付与する。"""
        try:
            sql = (
                self._SELECT_BASE
                + self._LATEST_INSPECTION_JOIN
                + """
                WHERE e.area = %s
                  AND e.deleted_at IS NULL
                ORDER BY e.next_inspection_date IS NULL, e.next_inspection_date, e.id
                """
            )
            self.cursor.execute(sql, (base,))
            rows = self.cursor.fetchall()
            return [self._row_to_dto(row) for row in rows]
        except pymysql.Error as e:
            raise e

    def find_by_id(self, id):
        """設備IDで検索し1件返す（論理削除済みを除く）。"""
        try:
            sql = (
                self._SELECT_BASE
                + self._LATEST_INSPECTION_JOIN
                + """
                WHERE e.id = %s
                  AND e.deleted_at IS NULL
                """
            )
            self.cursor.execute(sql, (id,))
            row = self.cursor.fetchone()
            if row is None:
                return None
            return self._row_to_dto(row)
        except pymysql.Error as e:
            raise e

    def find_by_user_id(self, user_id):
        """担当者IDで設備一覧を返す（論理削除済みを除く）。FEの担当設備取得に使用する。"""
        try:
            sql = (
                self._SELECT_BASE
                + self._LATEST_INSPECTION_JOIN
                + """
                WHERE e.assigned_user_id = %s
                  AND e.deleted_at IS NULL
                ORDER BY e.next_inspection_date IS NULL, e.next_inspection_date, e.id
                """
            )
            self.cursor.execute(sql, (user_id,))
            rows = self.cursor.fetchall()
            return [self._row_to_dto(row) for row in rows]
        except pymysql.Error as e:
            raise e

    def find_all_deleted(self):
        """論理削除済みの設備一覧を返す（ゴミ箱表示用）。"""
        try:
            sql = """
                SELECT
                    e.id,
                    e.name,
                    e.location,
                    e.equipment_type,
                    e.manufacturer,
                    e.model_number,
                    e.installed_at,
                    e.inspection_interval_months,
                    e.assigned_user_id,
                    e.area,
                    e.next_inspection_date,
                    e.deleted_at,
                    CASE
                        WHEN emp.last_name IS NOT NULL
                        THEN CONCAT(emp.last_name, emp.first_name)
                        ELSE NULL
                    END AS assigned_user_name,
                    CASE
                        WHEN deleter.last_name IS NOT NULL
                        THEN CONCAT(deleter.last_name, deleter.first_name)
                        ELSE NULL
                    END AS deleted_by_name,
                    NULL AS latest_inspection_status,
                    NULL AS latest_inspection_date,
                    NULL AS latest_inspection_note
                FROM equipment e
                LEFT JOIN employee emp     ON e.assigned_user_id = emp.id
                LEFT JOIN employee deleter ON e.deleted_by        = deleter.id
                WHERE e.deleted_at IS NOT NULL
                ORDER BY e.deleted_at DESC
            """
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            return [self._row_to_dto(row) for row in rows]
        except pymysql.Error as e:
            raise e

    def create(self, dto):
        """equipmentテーブルに新規レコードを挿入する。assigned_user_idはNULL許容。"""
        try:
            sql = """
                INSERT INTO equipment
                    (name, location, equipment_type, manufacturer, model_number,
                     installed_at, inspection_interval_months, assigned_user_id, area)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(sql, (
                dto.name,
                dto.location,
                dto.equipment_type,
                dto.manufacturer,
                dto.model_number,
                dto.installed_at,
                dto.inspection_interval_months,
                dto.assigned_user_id,
                dto.area,
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def update(self, dto):
        """equipmentテーブルの既存レコードを上書きする。"""
        try:
            sql = """
                UPDATE equipment
                SET name                       = %s,
                    location                   = %s,
                    equipment_type             = %s,
                    manufacturer               = %s,
                    model_number               = %s,
                    installed_at               = %s,
                    inspection_interval_months = %s,
                    assigned_user_id           = %s,
                    area                       = %s
                WHERE id = %s
            """
            self.cursor.execute(sql, (
                dto.name,
                dto.location,
                dto.equipment_type,
                dto.manufacturer,
                dto.model_number,
                dto.installed_at,
                dto.inspection_interval_months,
                dto.assigned_user_id,
                dto.area,
                dto.id,
            ))
            self.conn.commit()
            return self.cursor.rowcount
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def update_assigned_user(self, id, assigned_user_id, changed_by=None):
        """担当者（assigned_user_id）のみを更新する。インライン変更で使用する。"""
        try:
            # 変更前の担当者IDを取得する（audit_log用）
            self.cursor.execute(
                "SELECT assigned_user_id FROM equipment WHERE id = %s AND deleted_at IS NULL",
                (id,)
            )
            old_row = self.cursor.fetchone()
            old_assigned = old_row["assigned_user_id"] if old_row else None

            sql = """
                UPDATE equipment
                SET assigned_user_id = %s
                WHERE id = %s
            """
            self.cursor.execute(sql, (assigned_user_id, id))

            # 担当変更をaudit_logに記録する
            if changed_by and self.cursor.rowcount > 0:
                if old_assigned is None and assigned_user_id is not None:
                    action = "ASSIGN"      # 未割当 → 割当あり
                elif old_assigned is not None and assigned_user_id is None:
                    action = "UNASSIGN"    # 割当あり → 未割当
                else:
                    action = "REASSIGN"    # 担当者の変更（どちらも非NULL）
                self._log_audit(
                    "equipment", id, action,
                    {"assigned_user_id": old_assigned}, changed_by
                )

            self.conn.commit()
            return self.cursor.rowcount
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def update_next_inspection_date(self, equipment_id, half_interval=False):
        """最新点検日と点検間隔から次回点検予定日を再計算してDBを更新する。
        half_interval=True の場合は間隔を半分にして計算する（要観察時に使用）。
        """
        try:
            # 最新点検日と点検間隔を取得する（論理削除済みの点検記録は除く）
            sql = """
                SELECT
                    e.inspection_interval_months,
                    MAX(ir.inspected_at) AS last_inspected_at
                FROM equipment e
                LEFT JOIN inspection_records ir
                    ON ir.equipment_id = e.id
                   AND ir.deleted_at IS NULL
                WHERE e.id = %s
                GROUP BY e.id, e.inspection_interval_months
            """
            self.cursor.execute(sql, (equipment_id,))
            row = self.cursor.fetchone()
            if row is None or row["last_inspected_at"] is None:
                return 0

            # 点検間隔を決定する
            interval = row["inspection_interval_months"]
            if half_interval:
                if interval == 1:
                    # 間隔が1ヶ月の場合は2週間後に設定する
                    next_date = row["last_inspected_at"] + relativedelta(weeks=2)
                else:
                    # それ以外は半分の間隔（最小1ヶ月）で設定する
                    next_date = row["last_inspected_at"] + relativedelta(months=max(1, math.ceil(interval / 2)))
            else:
                next_date = row["last_inspected_at"] + relativedelta(months=interval)

            # next_inspection_date を更新する
            update_sql = """
                UPDATE equipment
                SET next_inspection_date = %s
                WHERE id = %s
            """
            self.cursor.execute(update_sql, (next_date, equipment_id))
            self.conn.commit()
            return self.cursor.rowcount
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def set_next_inspection_date(self, equipment_id, next_date):
        """次回点検予定日を指定した日付で直接更新する（要修理時に使用）。"""
        try:
            sql = """
                UPDATE equipment
                SET next_inspection_date = %s
                WHERE id = %s
            """
            self.cursor.execute(sql, (next_date, equipment_id))
            self.conn.commit()
            return self.cursor.rowcount
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def unassign_by_user_id(self, user_id):
        """指定ユーザーが担当する全設備の assigned_user_id を NULL にする。ユーザー削除前に使用する。"""
        try:
            sql = "UPDATE equipment SET assigned_user_id = NULL WHERE assigned_user_id = %s"
            self.cursor.execute(sql, (user_id,))
            self.conn.commit()
            return self.cursor.rowcount
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def find_overdue_ids(self, equipment_ids):
        """指定IDリストの中で next_inspection_date が今日より前の設備IDを返す。
        一括編集のロックチェック（admin は超過設備を編集不可）に使用する。"""
        if not equipment_ids:
            return []
        try:
            placeholders = ', '.join('%s' for _ in equipment_ids)
            sql = f"""
                SELECT id FROM equipment
                WHERE id IN ({placeholders})
                  AND deleted_at IS NULL
                  AND next_inspection_date < CURDATE()
            """
            self.cursor.execute(sql, list(equipment_ids))
            rows = self.cursor.fetchall()
            return [row['id'] for row in rows]
        except pymysql.Error as e:
            raise e

    def bulk_update(self, equipment_ids, update_fields, changed_by):
        """複数の設備のフィールドを一括更新する。変更前の値を audit_log に記録する。

        Args:
            equipment_ids (list[int]): 更新対象の設備IDリスト
            update_fields (dict): {フィールド名: 新しい値} の辞書
            changed_by (int): 操作者のemployee.id

        Returns:
            tuple[int, str]: (更新された行数, batch_id)
        """
        # SQLインジェクション対策として、更新を許可するフィールド名を明示的に指定する
        ALLOWED_FIELDS = {
            'name', 'location', 'equipment_type', 'manufacturer',
            'model_number', 'inspection_interval_months', 'assigned_user_id', 'area'
        }
        # 許可外フィールドを除外する
        safe_fields = {k: v for k, v in update_fields.items() if k in ALLOWED_FIELDS}
        if not safe_fields or not equipment_ids:
            return 0, None

        try:
            placeholders = ', '.join('%s' for _ in equipment_ids)

            # 更新前の設備データを取得する（audit_log用・元に戻す機能で使用する）
            self.cursor.execute(
                f"SELECT * FROM equipment WHERE id IN ({placeholders}) AND deleted_at IS NULL",
                equipment_ids
            )
            old_rows = self.cursor.fetchall()

            # 今回の一括操作をグループ化するためのIDを生成する
            batch_id = str(uuid.uuid4())

            # 各設備の変更前データを audit_log に記録する
            for row in old_rows:
                self._log_audit('equipment', row['id'], 'BULK_UPDATE', row, changed_by, batch_id=batch_id)

            # SET句を動的に構築する（例: "name = %s, location = %s"）
            set_clause = ', '.join(f'{field} = %s' for field in safe_fields.keys())
            # バインド変数：SET句の値 + WHERE IN句のIDリスト
            values = list(safe_fields.values()) + list(equipment_ids)

            sql = f"""
                UPDATE equipment
                SET {set_clause}
                WHERE id IN ({placeholders})
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
        ALLOWED_FIELDS = {
            'name', 'location', 'equipment_type', 'manufacturer',
            'model_number', 'inspection_interval_months', 'assigned_user_id', 'area'
        }
        # 許可外フィールドを除外する
        safe_fields = [f for f in updated_fields if f in ALLOWED_FIELDS]
        if not safe_fields or not batch_id:
            return 0

        try:
            # batch_id に対応する audit_log エントリを取得する
            self.cursor.execute(
                "SELECT record_id, old_data FROM audit_log"
                " WHERE batch_id = %s AND table_name = 'equipment'",
                (batch_id,)
            )
            entries = self.cursor.fetchall()
            if not entries:
                return 0

            reverted_count = 0
            for entry in entries:
                equipment_id = entry['record_id']
                old_data = json.loads(entry['old_data']) if entry['old_data'] else {}

                # 復元するフィールドと旧値のみ抽出する
                restore_values = {f: old_data[f] for f in safe_fields if f in old_data}
                if not restore_values:
                    continue

                # 現在の値を audit_log に記録してから復元する（操作履歴として残す）
                self.cursor.execute(
                    "SELECT * FROM equipment WHERE id = %s AND deleted_at IS NULL",
                    (equipment_id,)
                )
                current_row = self.cursor.fetchone()
                if current_row is None:
                    continue
                self._log_audit('equipment', equipment_id, 'BULK_REVERT', current_row, reverted_by)

                # 旧値に戻す
                set_clause = ', '.join(f'{f} = %s' for f in restore_values.keys())
                values = list(restore_values.values()) + [equipment_id]
                self.cursor.execute(
                    f"UPDATE equipment SET {set_clause} WHERE id = %s AND deleted_at IS NULL",
                    values
                )
                reverted_count += self.cursor.rowcount

            self.conn.commit()
            return reverted_count
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def find_stats_by_base(self):
        """設備のエリア（equipment.area）別の異常件数統計を返す（管理者ダッシュボード分析用）。"""
        try:
            sql = """
                SELECT
                    COALESCE(e.area, 'エリア未設定') AS base_name,
                    COUNT(e.id) AS total,
                    SUM(CASE WHEN e.next_inspection_date < CURDATE() THEN 1 ELSE 0 END) AS overdue,
                    SUM(CASE WHEN last_ir.status = 'repair' THEN 1 ELSE 0 END) AS repair,
                    SUM(CASE WHEN e.assigned_user_id IS NULL THEN 1 ELSE 0 END) AS unassigned
                FROM equipment e
                LEFT JOIN (
                    SELECT ir.equipment_id, ir.status
                    FROM inspection_records ir
                    INNER JOIN (
                        SELECT ir1.equipment_id, MAX(ir1.id) AS max_id
                        FROM inspection_records ir1
                        INNER JOIN (
                            SELECT equipment_id, MAX(inspected_at) AS latest_date
                            FROM inspection_records
                            WHERE deleted_at IS NULL
                            GROUP BY equipment_id
                        ) ld ON ir1.equipment_id = ld.equipment_id
                              AND ir1.inspected_at = ld.latest_date
                        WHERE ir1.deleted_at IS NULL
                        GROUP BY ir1.equipment_id
                    ) latest ON ir.id = latest.max_id
                ) last_ir ON last_ir.equipment_id = e.id
                WHERE e.deleted_at IS NULL
                GROUP BY e.area
                ORDER BY
                    -- エリア未設定（e.area が NULL）は常に末尾に固定する
                    (e.area IS NULL) ASC,
                    (
                        SUM(CASE WHEN e.next_inspection_date < CURDATE() THEN 1 ELSE 0 END)
                        + SUM(CASE WHEN last_ir.status = 'repair' THEN 1 ELSE 0 END)
                    ) DESC,
                    COUNT(e.id) DESC
            """
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            # int変換（MySQLのDecimalが返る場合があるため）
            result = []
            for row in rows:
                result.append({
                    "base_name": row["base_name"],
                    "total": int(row["total"]),
                    "overdue": int(row["overdue"] or 0),
                    "repair": int(row["repair"] or 0),
                    "unassigned": int(row["unassigned"] or 0),
                })
            return result
        except pymysql.Error as e:
            raise e

    def find_stats_by_engineer(self, base=None):
        """担当者別の設備保有件数・異常件数を返す（管理者ダッシュボード分析用）。
        base を指定した場合は、その拠点に所属する担当者のみ返す。
        """
        try:
            sql = """
                SELECT
                    emp.id AS engineer_id,
                    CASE
                        WHEN emp.id IS NULL THEN '担当未登録'
                        ELSE CONCAT(emp.last_name, emp.first_name)
                    END AS engineer_name,
                    COALESCE(emp.base, '─') AS base_name,
                    COUNT(e.id) AS total,
                    SUM(CASE WHEN e.next_inspection_date < CURDATE() THEN 1 ELSE 0 END) AS overdue,
                    SUM(CASE WHEN last_ir.status = 'repair' THEN 1 ELSE 0 END) AS repair
                FROM equipment e
                LEFT JOIN employee emp ON e.assigned_user_id = emp.id
                LEFT JOIN (
                    SELECT ir.equipment_id, ir.status
                    FROM inspection_records ir
                    INNER JOIN (
                        SELECT ir1.equipment_id, MAX(ir1.id) AS max_id
                        FROM inspection_records ir1
                        INNER JOIN (
                            SELECT equipment_id, MAX(inspected_at) AS latest_date
                            FROM inspection_records
                            WHERE deleted_at IS NULL
                            GROUP BY equipment_id
                        ) ld ON ir1.equipment_id = ld.equipment_id
                              AND ir1.inspected_at = ld.latest_date
                        WHERE ir1.deleted_at IS NULL
                        GROUP BY ir1.equipment_id
                    ) latest ON ir.id = latest.max_id
                ) last_ir ON last_ir.equipment_id = e.id
            """
            # 拠点フィルタが指定されている場合は絞り込む
            params = []
            if base:
                sql += " WHERE emp.base = %s"
                params.append(base)

            sql += """
                GROUP BY emp.id, emp.last_name, emp.first_name
                ORDER BY
                    -- 担当未登録（emp.id が NULL）は常に先頭に固定する
                    (emp.id IS NULL) DESC,
                    (
                        SUM(CASE WHEN e.next_inspection_date < CURDATE() THEN 1 ELSE 0 END)
                        + SUM(CASE WHEN last_ir.status = 'repair' THEN 1 ELSE 0 END)
                    ) DESC,
                    COUNT(e.id) DESC
            """
            self.cursor.execute(sql, params)
            rows = self.cursor.fetchall()
            result = []
            for row in rows:
                result.append({
                    "engineer_id": row["engineer_id"],
                    "engineer_name": row["engineer_name"],
                    "base_name": row["base_name"],
                    "total": int(row["total"]),
                    "overdue": int(row["overdue"] or 0),
                    "repair": int(row["repair"] or 0),
                })
            return result
        except pymysql.Error as e:
            raise e

    def find_weekly_schedule(self, base=None):
        """次回点検の週別件数を返す（拠点選択時のスケジュールグラフ用）。
        超過分 + 今週を含む直近8週の9件を返す。週は月曜始まりで集計する。
        """
        try:
            # 今週の月曜日を算出する
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(weeks=8)

            # 期限超過（今週の月曜より前）の件数を取得する（論理削除済みを除く）
            overdue_sql = """
                SELECT COUNT(*) AS count
                FROM equipment e
                LEFT JOIN employee emp ON e.assigned_user_id = emp.id
                WHERE e.next_inspection_date IS NOT NULL
                  AND e.next_inspection_date < %s
                  AND e.deleted_at IS NULL
            """
            overdue_params = [week_start]
            if base:
                overdue_sql += " AND emp.base = %s"
                overdue_params.append(base)

            self.cursor.execute(overdue_sql, overdue_params)
            overdue_row = self.cursor.fetchone()
            overdue_count = int(overdue_row["count"]) if overdue_row else 0

            # 今週から8週分の週別件数を取得する（週の月曜日でグループ化する、論理削除済みを除く）
            schedule_sql = """
                SELECT
                    DATE_SUB(e.next_inspection_date,
                             INTERVAL WEEKDAY(e.next_inspection_date) DAY) AS week_monday,
                    COUNT(*) AS count
                FROM equipment e
                LEFT JOIN employee emp ON e.assigned_user_id = emp.id
                WHERE e.next_inspection_date IS NOT NULL
                  AND e.next_inspection_date >= %s
                  AND e.next_inspection_date < %s
                  AND e.deleted_at IS NULL
            """
            schedule_params = [week_start, week_end]
            if base:
                schedule_sql += " AND emp.base = %s"
                schedule_params.append(base)

            schedule_sql += " GROUP BY week_monday ORDER BY week_monday"

            self.cursor.execute(schedule_sql, schedule_params)
            rows = self.cursor.fetchall()

            # DBの結果をdictに変換する（キーは週月曜日の日付文字列）
            db_data = {
                row["week_monday"].strftime("%Y-%m-%d"): int(row["count"])
                for row in rows
            }

            # 8週分のラベルとカウントを生成する（データなし週は0で補完）
            result = []
            for i in range(8):
                ws = week_start + timedelta(weeks=i)
                key = ws.strftime("%Y-%m-%d")
                label = ws.strftime("%m/%d")
                result.append({
                    "week_key": key,
                    "week_label": label,
                    "count": db_data.get(key, 0),
                    "is_overdue": False,
                })

            # 先頭に超過分のバーを追加する
            result.insert(0, {
                "week_key": "overdue",
                "week_label": "超過",
                "count": overdue_count,
                "is_overdue": True,
            })

            return result
        except pymysql.Error as e:
            raise e

    def count_overdue_7days_ago(self, base=None):
        """7日前時点での期限超過件数を返す（先週比計算用）。baseを指定すると拠点で絞り込む。"""
        try:
            sql = """
                SELECT COUNT(*) AS cnt
                FROM equipment e
                WHERE e.next_inspection_date < DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                  AND e.deleted_at IS NULL
            """
            params = []
            if base:
                sql += " AND e.area = %s"
                params.append(base)
            self.cursor.execute(sql, params)
            row = self.cursor.fetchone()
            return int(row["cnt"]) if row else 0
        except pymysql.Error as e:
            raise e

    def count_soon_7days_ago(self, base=None):
        """7日前時点での点検期限間近件数を返す（先週比計算用）。baseを指定すると拠点で絞り込む。"""
        try:
            sql = """
                SELECT COUNT(*) AS cnt
                FROM equipment e
                WHERE e.next_inspection_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                  AND e.next_inspection_date <= CURDATE()
                  AND e.deleted_at IS NULL
            """
            params = []
            if base:
                sql += " AND e.area = %s"
                params.append(base)
            self.cursor.execute(sql, params)
            row = self.cursor.fetchone()
            return int(row["cnt"]) if row else 0
        except pymysql.Error as e:
            raise e

    def count_repair_7days_ago(self, base=None):
        """7日前時点での要修理件数を返す（先週比計算用）。baseを指定すると拠点で絞り込む。"""
        try:
            sql = """
                SELECT COUNT(*) AS cnt
                FROM equipment e
                INNER JOIN (
                    SELECT ir.equipment_id, ir.status
                    FROM inspection_records ir
                    INNER JOIN (
                        SELECT ir1.equipment_id, MAX(ir1.id) AS latest_id
                        FROM inspection_records ir1
                        INNER JOIN (
                            SELECT equipment_id, MAX(inspected_at) AS latest_date
                            FROM inspection_records
                            WHERE deleted_at IS NULL
                              AND inspected_at <= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                            GROUP BY equipment_id
                        ) ld ON ir1.equipment_id = ld.equipment_id
                              AND ir1.inspected_at = ld.latest_date
                        WHERE ir1.deleted_at IS NULL
                        GROUP BY ir1.equipment_id
                    ) latest ON ir.id = latest.latest_id
                ) last_ir ON e.id = last_ir.equipment_id
                WHERE last_ir.status = 'repair'
                  AND e.deleted_at IS NULL
            """
            params = []
            if base:
                sql += " AND e.area = %s"
                params.append(base)
            self.cursor.execute(sql, params)
            row = self.cursor.fetchone()
            return int(row["cnt"]) if row else 0
        except pymysql.Error as e:
            raise e

    def count_new_repair_this_week(self, base=None):
        """直近7日間に要修理になった設備のうち、現在も最新点検が要修理の件数を返す（今週バッジ用）。baseを指定すると拠点で絞り込む。"""
        try:
            base_cond = "AND e.area = %s " if base else ""
            params = [base] if base else []
            sql = f"""
                SELECT COUNT(*) AS cnt
                FROM (
                    SELECT ir.equipment_id
                    FROM inspection_records ir
                    INNER JOIN (
                        SELECT ir1.equipment_id, MAX(ir1.id) AS latest_id
                        FROM inspection_records ir1
                        INNER JOIN (
                            SELECT equipment_id, MAX(inspected_at) AS latest_date
                            FROM inspection_records
                            WHERE deleted_at IS NULL
                            GROUP BY equipment_id
                        ) ld ON ir1.equipment_id = ld.equipment_id
                              AND ir1.inspected_at = ld.latest_date
                        WHERE ir1.deleted_at IS NULL
                        GROUP BY ir1.equipment_id
                    ) latest ON ir.id = latest.latest_id
                    INNER JOIN equipment e ON ir.equipment_id = e.id
                    WHERE ir.status = 'repair'
                      AND ir.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                      AND e.deleted_at IS NULL
                      {base_cond}
                ) AS subq
            """
            self.cursor.execute(sql, params)
            row = self.cursor.fetchone()
            return int(row["cnt"]) if row else 0
        except pymysql.Error as e:
            raise e

    def count_unassigned_7days_ago(self, base=None):
        """7日前時点での担当未登録件数を返す（先週比計算用）。
        audit_logの変更履歴からデルタ計算で推定する。
        """
        try:
            base_cond   = "AND e.area = %s " if base else ""
            base_params = [base] if base else []

            # 現在の未割当件数
            self.cursor.execute(
                "SELECT COUNT(*) AS cnt FROM equipment e "
                "WHERE e.assigned_user_id IS NULL AND e.deleted_at IS NULL " + base_cond,
                base_params
            )
            current = int(self.cursor.fetchone()["cnt"])

            # 直近7日間に個別操作で「割当あり → NULL」になった設備数（UNASSIGN）
            # これらは現在は未割当だが、7日前は割当があったため過去件数から除く
            self.cursor.execute(
                "SELECT COUNT(DISTINCT al.record_id) AS cnt "
                "FROM audit_log al INNER JOIN equipment e ON al.record_id = e.id "
                "WHERE al.table_name = 'equipment' AND al.action = 'UNASSIGN' "
                "  AND al.changed_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) "
                "  AND e.deleted_at IS NULL " + base_cond,
                base_params
            )
            unassign_delta = int(self.cursor.fetchone()["cnt"])

            # 直近7日間に個別操作で「NULL → 割当あり」になった設備数（ASSIGN）
            # これらは現在は割当ありだが、7日前は未割当だったため過去件数に加える
            self.cursor.execute(
                "SELECT COUNT(DISTINCT al.record_id) AS cnt "
                "FROM audit_log al INNER JOIN equipment e ON al.record_id = e.id "
                "WHERE al.table_name = 'equipment' AND al.action = 'ASSIGN' "
                "  AND al.changed_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) "
                "  AND e.deleted_at IS NULL " + base_cond,
                base_params
            )
            assign_delta = int(self.cursor.fetchone()["cnt"])

            # 直近7日間の一括更新で「NULL → 割当あり」になった設備数（BULK_UPDATE）
            self.cursor.execute(
                "SELECT COUNT(DISTINCT al.record_id) AS cnt "
                "FROM audit_log al INNER JOIN equipment e ON al.record_id = e.id "
                "WHERE al.table_name = 'equipment' AND al.action = 'BULK_UPDATE' "
                "  AND al.changed_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) "
                "  AND JSON_EXTRACT(al.old_data, '$.assigned_user_id') IS NULL "
                "  AND e.assigned_user_id IS NOT NULL "
                "  AND e.deleted_at IS NULL " + base_cond,
                base_params
            )
            bulk_assign_delta = int(self.cursor.fetchone()["cnt"])

            # 直近7日間の一括更新で「割当あり → NULL」になった設備数（BULK_UPDATE）
            self.cursor.execute(
                "SELECT COUNT(DISTINCT al.record_id) AS cnt "
                "FROM audit_log al INNER JOIN equipment e ON al.record_id = e.id "
                "WHERE al.table_name = 'equipment' AND al.action = 'BULK_UPDATE' "
                "  AND al.changed_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) "
                "  AND JSON_EXTRACT(al.old_data, '$.assigned_user_id') IS NOT NULL "
                "  AND e.assigned_user_id IS NULL "
                "  AND e.deleted_at IS NULL " + base_cond,
                base_params
            )
            bulk_unassign_delta = int(self.cursor.fetchone()["cnt"])

            # 7日前推定件数 = 現在 + 直近7日でASSIGN分 - 直近7日でUNASSIGN分
            past = (current
                    + assign_delta + bulk_assign_delta
                    - unassign_delta - bulk_unassign_delta)
            return max(0, past)
        except pymysql.Error as e:
            raise e

    def count_new_unassigned_this_week(self, base=None):
        """直近7日間に新規追加された担当未登録設備の件数を返す（今週バッジ用）。baseを指定すると拠点で絞り込む。
        拠点フィルタは equipment.area で代用する（担当者がいないため employee JOIN 不可）。
        """
        try:
            sql = """
                SELECT COUNT(*) AS cnt
                FROM equipment
                WHERE assigned_user_id IS NULL
                  AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                  AND deleted_at IS NULL
            """
            params = []
            if base:
                sql += " AND area = %s"
                params.append(base)
            self.cursor.execute(sql, params)
            row = self.cursor.fetchone()
            return int(row["cnt"]) if row else 0
        except pymysql.Error as e:
            raise e

    def delete(self, id, deleted_by):
        """設備を論理削除し、関連する点検記録も同時に論理削除する。audit_logに記録する。"""
        try:
            # 削除前に設備データを取得する（audit_log用）
            self.cursor.execute(
                "SELECT * FROM equipment WHERE id = %s AND deleted_at IS NULL",
                (id,)
            )
            old_row = self.cursor.fetchone()
            if old_row is None:
                # 既に削除済みまたは存在しない
                return 0

            # 関連する点検記録を先に取得する（audit_log用）
            self.cursor.execute(
                "SELECT * FROM inspection_records WHERE equipment_id = %s AND deleted_at IS NULL",
                (id,)
            )
            ir_rows = self.cursor.fetchall()

            # 日本時間（JST）で現在日時を取得する
            jst = timezone(timedelta(hours=9))
            now_jst = datetime.now(jst).replace(tzinfo=None)

            # 設備を論理削除する
            self.cursor.execute(
                "UPDATE equipment SET deleted_at = %s, deleted_by = %s WHERE id = %s AND deleted_at IS NULL",
                (now_jst, deleted_by, id)
            )
            eq_affected = self.cursor.rowcount

            # 関連する点検記録を論理削除する
            if ir_rows:
                self.cursor.execute(
                    "UPDATE inspection_records SET deleted_at = %s, deleted_by = %s"
                    " WHERE equipment_id = %s AND deleted_at IS NULL",
                    (now_jst, deleted_by, id)
                )

            # audit_logに設備の削除を記録する
            self._log_audit('equipment', id, 'DELETE', old_row, deleted_by)

            # audit_logに各点検記録の削除を記録する
            for ir in ir_rows:
                self._log_audit('inspection_records', ir['id'], 'DELETE', ir, deleted_by)

            self.conn.commit()
            return eq_affected
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def bulk_delete(self, equipment_ids, deleted_by):
        """複数の設備を一括論理削除し、関連する点検記録も同時に論理削除する。audit_logに記録する。"""
        if not equipment_ids:
            return 0
        try:
            placeholders = ', '.join('%s' for _ in equipment_ids)

            # 削除前に設備データを取得する（audit_log用・既に削除済みは除外）
            self.cursor.execute(
                f"SELECT * FROM equipment WHERE id IN ({placeholders}) AND deleted_at IS NULL",
                equipment_ids
            )
            old_rows = self.cursor.fetchall()
            if not old_rows:
                return 0

            # 実際に削除対象となるIDリストを確定する
            target_ids = [row['id'] for row in old_rows]
            target_placeholders = ', '.join('%s' for _ in target_ids)

            # 関連する点検記録を取得する（audit_log用）
            self.cursor.execute(
                f"SELECT * FROM inspection_records WHERE equipment_id IN ({target_placeholders}) AND deleted_at IS NULL",
                target_ids
            )
            ir_rows = self.cursor.fetchall()

            # 日本時間（JST）で現在日時を取得する
            jst = timezone(timedelta(hours=9))
            now_jst = datetime.now(jst).replace(tzinfo=None)

            # 設備を一括論理削除する
            self.cursor.execute(
                f"UPDATE equipment SET deleted_at = %s, deleted_by = %s"
                f" WHERE id IN ({target_placeholders}) AND deleted_at IS NULL",
                [now_jst, deleted_by] + target_ids
            )
            eq_affected = self.cursor.rowcount

            # 関連する点検記録を一括論理削除する
            if ir_rows:
                self.cursor.execute(
                    f"UPDATE inspection_records SET deleted_at = %s, deleted_by = %s"
                    f" WHERE equipment_id IN ({target_placeholders}) AND deleted_at IS NULL",
                    [now_jst, deleted_by] + target_ids
                )

            # audit_logに各設備の削除を記録する
            for row in old_rows:
                self._log_audit('equipment', row['id'], 'DELETE', row, deleted_by)

            # audit_logに各点検記録の削除を記録する
            for ir in ir_rows:
                self._log_audit('inspection_records', ir['id'], 'DELETE', ir, deleted_by)

            self.conn.commit()
            return eq_affected
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def hard_delete(self, id, deleted_by):
        """
        論理削除済みの設備を物理削除する（取り消し不可）。
        関連する点検記録も同時に物理削除する。audit_logに記録してからDELETEする。
        対象: deleted_at IS NOT NULL の設備のみ（ゴミ箱にある設備に限定）。
        """
        try:
            # 対象設備を取得する（ゴミ箱にある設備のみ）
            self.cursor.execute(
                "SELECT * FROM equipment WHERE id = %s AND deleted_at IS NOT NULL",
                (id,)
            )
            old_row = self.cursor.fetchone()
            if old_row is None:
                return 0

            # 関連する点検記録を取得する（audit_log用）
            self.cursor.execute(
                "SELECT * FROM inspection_records WHERE equipment_id = %s",
                (id,)
            )
            ir_rows = self.cursor.fetchall()

            # audit_logに設備の物理削除を記録してから削除する
            self._log_audit('equipment', id, 'HARD_DELETE', old_row, deleted_by)
            for ir in ir_rows:
                self._log_audit('inspection_records', ir['id'], 'HARD_DELETE', ir, deleted_by)

            # 点検記録を先に物理削除する（FK制約があるため先に削除する）
            self.cursor.execute(
                "DELETE FROM inspection_records WHERE equipment_id = %s",
                (id,)
            )

            # 設備を物理削除する
            self.cursor.execute(
                "DELETE FROM equipment WHERE id = %s AND deleted_at IS NOT NULL",
                (id,)
            )
            eq_affected = self.cursor.rowcount

            self.conn.commit()
            return eq_affected
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def bulk_restore(self, equipment_ids, restored_by):
        """複数の論理削除済み設備と関連する点検記録を一括復元する。"""
        if not equipment_ids:
            return 0
        try:
            placeholders = ', '.join('%s' for _ in equipment_ids)

            # 設備を一括復元する
            self.cursor.execute(
                f"UPDATE equipment SET deleted_at = NULL, deleted_by = NULL"
                f" WHERE id IN ({placeholders}) AND deleted_at IS NOT NULL",
                equipment_ids
            )
            eq_affected = self.cursor.rowcount

            # 関連する点検記録を一括復元する
            self.cursor.execute(
                f"UPDATE inspection_records SET deleted_at = NULL, deleted_by = NULL"
                f" WHERE equipment_id IN ({placeholders}) AND deleted_at IS NOT NULL",
                equipment_ids
            )

            # audit_logに各設備の復元を記録する
            for eq_id in equipment_ids:
                self._log_audit('equipment', eq_id, 'RESTORE', None, restored_by)

            self.conn.commit()
            return eq_affected
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def bulk_hard_delete_from_recycle(self, equipment_ids, deleted_by):
        """複数の論理削除済み設備を一括物理削除する（ROOT専用・取り消し不可）。"""
        if not equipment_ids:
            return 0
        try:
            placeholders = ', '.join('%s' for _ in equipment_ids)

            # 対象設備を取得する（ゴミ箱にある設備のみ）
            self.cursor.execute(
                f"SELECT * FROM equipment WHERE id IN ({placeholders}) AND deleted_at IS NOT NULL",
                equipment_ids
            )
            old_rows = self.cursor.fetchall()
            if not old_rows:
                return 0

            target_ids = [row['id'] for row in old_rows]
            target_placeholders = ', '.join('%s' for _ in target_ids)

            # 関連する点検記録を取得する（audit_log用）
            self.cursor.execute(
                f"SELECT * FROM inspection_records WHERE equipment_id IN ({target_placeholders})",
                target_ids
            )
            ir_rows = self.cursor.fetchall()

            # audit_logに記録してから削除する
            for row in old_rows:
                self._log_audit('equipment', row['id'], 'HARD_DELETE', row, deleted_by)
            for ir in ir_rows:
                self._log_audit('inspection_records', ir['id'], 'HARD_DELETE', ir, deleted_by)

            # 点検記録を先に物理削除する（FK制約のため）
            self.cursor.execute(
                f"DELETE FROM inspection_records WHERE equipment_id IN ({target_placeholders})",
                target_ids
            )

            # 設備を物理削除する
            self.cursor.execute(
                f"DELETE FROM equipment WHERE id IN ({target_placeholders}) AND deleted_at IS NOT NULL",
                target_ids
            )
            eq_affected = self.cursor.rowcount

            self.conn.commit()
            return eq_affected
        except pymysql.Error as e:
            self.conn.rollback()
            raise e

    def find_distinct_locations(self):
        """登録済みのロケーション名（重複なし）をリストで返す。オートコンプリート用。"""
        sql = "SELECT DISTINCT location FROM equipment WHERE deleted_at IS NULL ORDER BY location"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return [row["location"] for row in rows]

    def find_distinct_manufacturers(self):
        """登録済みのメーカー名（重複なし）をリストで返す。オートコンプリート用。"""
        sql = "SELECT DISTINCT manufacturer FROM equipment WHERE deleted_at IS NULL ORDER BY manufacturer"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return [row["manufacturer"] for row in rows]

    def restore(self, id, restored_by):
        """論理削除済みの設備と関連する点検記録を復元する。audit_logに記録する。"""
        try:
            # 設備を復元する
            self.cursor.execute(
                "UPDATE equipment SET deleted_at = NULL, deleted_by = NULL"
                " WHERE id = %s AND deleted_at IS NOT NULL",
                (id,)
            )
            eq_affected = self.cursor.rowcount

            # 関連する点検記録を復元する
            self.cursor.execute(
                "UPDATE inspection_records SET deleted_at = NULL, deleted_by = NULL"
                " WHERE equipment_id = %s AND deleted_at IS NOT NULL",
                (id,)
            )

            # audit_logに復元を記録する
            self._log_audit('equipment', id, 'RESTORE', None, restored_by)

            self.conn.commit()
            return eq_affected
        except pymysql.Error as e:
            self.conn.rollback()
            raise e
