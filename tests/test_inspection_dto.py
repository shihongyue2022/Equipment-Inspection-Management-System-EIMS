"""
tests/test_inspection_dto.py

B-07-03: InspectionDto の @property / @setter 動作確認テスト。

テスト対象：
  app.dto.inspection_dto.InspectionDto

テスト内容：
  - 全プロパティの getter / setter が正しく動作すること
  - 初期値がすべて None であること
  - status_label が 'normal'・'watch'・'repair' を正しく日本語に変換すること
  - status_label で未知のステータスコードの場合は '不明' を返すこと
"""

import pytest
from datetime import date, datetime
from app.dto.inspection_dto import InspectionDto


class TestInspectionDtoInit:
    """InspectionDto の初期値テスト"""

    def test_initial_values_are_none(self):
        """インスタンス生成直後は全プロパティが None である"""
        dto = InspectionDto()
        assert dto.id is None
        assert dto.equipment_id is None
        assert dto.engineer_id is None
        assert dto.inspected_at is None
        assert dto.expected_inspection_date is None
        assert dto.status is None
        assert dto.note is None
        assert dto.created_at is None
        assert dto.equipment_name is None
        assert dto.engineer_name is None
        assert dto.deleted_at is None
        assert dto.deleted_by_name is None


class TestInspectionDtoProperties:
    """InspectionDto の各 @property / @setter テスト"""

    def test_id_setter_and_getter(self):
        """id プロパティのセット・取得が正しく動作する"""
        dto = InspectionDto()
        dto.id = 100
        assert dto.id == 100

    def test_equipment_id_setter_and_getter(self):
        """equipment_id プロパティのセット・取得が正しく動作する"""
        dto = InspectionDto()
        dto.equipment_id = 3
        assert dto.equipment_id == 3

    def test_engineer_id_setter_and_getter(self):
        """engineer_id プロパティのセット・取得が正しく動作する"""
        dto = InspectionDto()
        dto.engineer_id = 7
        assert dto.engineer_id == 7

    def test_inspected_at_setter_and_getter(self):
        """inspected_at プロパティのセット・取得が正しく動作する"""
        dto = InspectionDto()
        d = date(2026, 6, 20)
        dto.inspected_at = d
        assert dto.inspected_at == d

    def test_expected_inspection_date_setter_and_getter(self):
        """expected_inspection_date プロパティのセット・取得が正しく動作する"""
        dto = InspectionDto()
        d = date(2026, 7, 1)
        dto.expected_inspection_date = d
        assert dto.expected_inspection_date == d

    def test_status_setter_and_getter(self):
        """status プロパティのセット・取得が正しく動作する"""
        dto = InspectionDto()
        dto.status = 'watch'
        assert dto.status == 'watch'

    def test_note_setter_and_getter(self):
        """note プロパティのセット・取得が正しく動作する"""
        dto = InspectionDto()
        dto.note = '異音あり。次回も注意が必要。'
        assert dto.note == '異音あり。次回も注意が必要。'

    def test_note_can_be_none(self):
        """note プロパティは None を格納できる（NULL許容）"""
        dto = InspectionDto()
        dto.note = None
        assert dto.note is None

    def test_created_at_setter_and_getter(self):
        """created_at プロパティのセット・取得が正しく動作する"""
        dto = InspectionDto()
        dt = datetime(2026, 6, 20, 9, 30, 0)
        dto.created_at = dt
        assert dto.created_at == dt

    def test_equipment_name_setter_and_getter(self):
        """equipment_name プロパティのセット・取得が正しく動作する"""
        dto = InspectionDto()
        dto.equipment_name = '空調設備A'
        assert dto.equipment_name == '空調設備A'

    def test_engineer_name_setter_and_getter(self):
        """engineer_name プロパティのセット・取得が正しく動作する"""
        dto = InspectionDto()
        dto.engineer_name = '山田太郎'
        assert dto.engineer_name == '山田太郎'

    def test_deleted_at_setter_and_getter(self):
        """deleted_at プロパティのセット・取得が正しく動作する"""
        dto = InspectionDto()
        dt = datetime(2026, 6, 1, 12, 0, 0)
        dto.deleted_at = dt
        assert dto.deleted_at == dt

    def test_deleted_by_name_setter_and_getter(self):
        """deleted_by_name プロパティのセット・取得が正しく動作する"""
        dto = InspectionDto()
        dto.deleted_by_name = '管理者 太郎'
        assert dto.deleted_by_name == '管理者 太郎'


class TestInspectionDtoStatusLabel:
    """InspectionDto の status_label 計算プロパティテスト"""

    def test_status_normal_returns_japanese_label(self):
        """status が 'normal' の場合は '正常' を返す"""
        dto = InspectionDto()
        dto.status = 'normal'
        assert dto.status_label == '正常'

    def test_status_watch_returns_japanese_label(self):
        """status が 'watch' の場合は '要観察' を返す"""
        dto = InspectionDto()
        dto.status = 'watch'
        assert dto.status_label == '要観察'

    def test_status_repair_returns_japanese_label(self):
        """status が 'repair' の場合は '要修理' を返す"""
        dto = InspectionDto()
        dto.status = 'repair'
        assert dto.status_label == '要修理'

    def test_unknown_status_returns_unknown_label(self):
        """未定義のステータスコードの場合は '不明' を返す"""
        dto = InspectionDto()
        dto.status = 'unknown_value'
        assert dto.status_label == '不明'

    def test_none_status_returns_unknown_label(self):
        """status が None の場合は '不明' を返す"""
        dto = InspectionDto()
        dto.status = None
        assert dto.status_label == '不明'
