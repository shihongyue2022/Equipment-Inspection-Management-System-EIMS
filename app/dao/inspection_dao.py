import pymysql
from app.dao.dao import Dao
from app.dto.inspection_dto import InspectionDto


class InspectionDao(Dao):
    """inspection_recordsテーブルに対するDB操作メソッドを定義するDAO。"""

    def __init__(self):
        super().__init__()

    def _row_to_dto(self, row):
        """辞書1行をInspectionDtoに詰め替える。"""
        dto = InspectionDto()
        dto.id                       = row["id"]
        dto.equipment_id             = row["equipment_id"]
        dto.engineer_id              = row["engineer_id"]
        dto.inspected_at             = row["inspected_at"]
        dto.expected_inspection_date = row.get("expected_inspection_date")
        dto.status                   = row["status"]
        dto.note                     = row["note"]
        dto.created_at               = row["created_at"]
        # JOINで取得した表示用の点検者名・設備名をセットする
        dto.engineer_name = row.get("engineer_name")
        dto.equipment_name = row.get("equipment_name")
        # ゴミ箱一覧でのみ値が入る（通常クエリでは None）
        dto.deleted_at = row.get("deleted_at")
        dto.deleted_by_name = row.get("deleted_by_name")
        dto.engineer_deleted = row.get("engineer_deleted", False)
        return dto

    def find_by_equipment_id(self, equipment_id):
        """設備IDに紐づく点検記録一覧を返す（論理削除済みを除く）。点検者名をJOINで付与する。"""
        sql = """
            SELECT
                ir.id,
                ir.equipment_id,
                ir.engineer_id,
                ir.inspected_at,
                ir.expected_inspection_date,
                ir.status,
                ir.note,
                ir.created_at,
                CONCAT(emp.last_name, emp.first_name) AS engineer_name,
                CASE WHEN emp.deleted_at IS NOT NULL THEN 1 ELSE 0 END AS engineer_deleted
            FROM inspection_records ir
            LEFT JOIN employee emp ON ir.engineer_id = emp.id
            WHERE ir.equipment_id = %s
              AND ir.deleted_at IS NULL
            ORDER BY ir.inspected_at DESC, ir.id DESC
        """
        self.cursor.execute(sql, (equipment_id,))
        rows = self.cursor.fetchall()
        return [self._row_to_dto(row) for row in rows]

    def count_by_engineer_id(self, engineer_id):
        """指定したエンジニアIDの点検記録件数を返す（論理削除済みを除く）。"""
        sql = """
            SELECT COUNT(*) AS cnt
            FROM inspection_records
            WHERE engineer_id = %s
              AND deleted_at IS NULL
        """
        self.cursor.execute(sql, (engineer_id,))
        row = self.cursor.fetchone()
        return int(row["cnt"]) if row else 0

    def find_all_deleted(self):
        """論理削除済みの点検記録一覧を返す（ゴミ箱表示用）。"""
        sql = """
            SELECT
                ir.id,
                ir.equipment_id,
                ir.engineer_id,
                ir.inspected_at,
                ir.status,
                ir.note,
                ir.created_at,
                ir.deleted_at,
                CONCAT(emp.last_name, emp.first_name) AS engineer_name,
                eq.name AS equipment_name,
                CASE
                    WHEN deleter.last_name IS NOT NULL
                    THEN CONCAT(deleter.last_name, deleter.first_name)
                    ELSE NULL
                END AS deleted_by_name
            FROM inspection_records ir
            LEFT JOIN employee  emp     ON ir.engineer_id  = emp.id
            LEFT JOIN equipment eq      ON ir.equipment_id = eq.id
            LEFT JOIN employee  deleter ON ir.deleted_by   = deleter.id
            WHERE ir.deleted_at IS NOT NULL
            ORDER BY ir.deleted_at DESC
        """
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return [self._row_to_dto(row) for row in rows]

    def create(self, dto):
        """inspection_recordsテーブルに新規レコードを挿入する。"""
        try:
            sql = """
                INSERT INTO inspection_records
                    (equipment_id, engineer_id, inspected_at, expected_inspection_date, status, note)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(sql, (
                dto.equipment_id,
                dto.engineer_id,
                dto.inspected_at,
                dto.expected_inspection_date,
                dto.status,
                dto.note,
            ))
            self.conn.commit()
            # 挿入した行のIDを返す
            return self.cursor.lastrowid
        except pymysql.Error as e:
            self.conn.rollback()
            raise e
