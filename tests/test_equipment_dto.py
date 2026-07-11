"""
tests/test_equipment_dto.py

B-07-02: EquipmentDto の @property / @setter 動作確認テスト。

テスト対象：
  app.dto.equipment_dto.EquipmentDto

テスト内容：
  - 全プロパティの getter / setter が正しく動作すること
  - 初期値がすべて None であること
  - deadline_status に 'overdue' / 'soon' / 'normal' / None を格納できること
"""

import pytest
from datetime import date
from app.dto.equipment_dto import EquipmentDto


class TestEquipmentDtoInit:
    """EquipmentDto の初期値テスト"""

    def test_initial_values_are_none(self):
        """インスタンス生成直後は全プロパティが None である"""
        dto = EquipmentDto()
        assert dto.id is None
        assert dto.name is None
        assert dto.location is None
        assert dto.equipment_type is None
        assert dto.manufacturer is None
        assert dto.model_number is None
        assert dto.installed_at is None
        assert dto.inspection_interval_months is None
        assert dto.assigned_user_id is None
        assert dto.assigned_user_name is None
        assert dto.area is None
        assert dto.next_inspection_date is None
        assert dto.deadline_status is None
        assert dto.latest_inspection_status is None
        assert dto.deleted_at is None
        assert dto.deleted_by_name is None


class TestEquipmentDtoProperties:
    """EquipmentDto の各 @property / @setter テスト"""

    def test_id_setter_and_getter(self):
        """id プロパティのセット・取得が正しく動作する"""
        dto = EquipmentDto()
        dto.id = 1
        assert dto.id == 1

    def test_name_setter_and_getter(self):
        """name プロパティのセット・取得が正しく動作する"""
        dto = EquipmentDto()
        dto.name = '空調設備A'
        assert dto.name == '空調設備A'

    def test_location_setter_and_getter(self):
        """location プロパティのセット・取得が正しく動作する"""
        dto = EquipmentDto()
        dto.location = '東京本社 3F'
        assert dto.location == '東京本社 3F'

    def test_equipment_type_setter_and_getter(self):
        """equipment_type プロパティのセット・取得が正しく動作する"""
        dto = EquipmentDto()
        dto.equipment_type = '空調'
        assert dto.equipment_type == '空調'

    def test_manufacturer_setter_and_getter(self):
        """manufacturer プロパティのセット・取得が正しく動作する"""
        dto = EquipmentDto()
        dto.manufacturer = 'ダイキン工業'
        assert dto.manufacturer == 'ダイキン工業'

    def test_model_number_setter_and_getter(self):
        """model_number プロパティのセット・取得が正しく動作する"""
        dto = EquipmentDto()
        dto.model_number = 'VRV-X123'
        assert dto.model_number == 'VRV-X123'

    def test_installed_at_setter_and_getter(self):
        """installed_at プロパティのセット・取得が正しく動作する"""
        dto = EquipmentDto()
        d = date(2020, 4, 1)
        dto.installed_at = d
        assert dto.installed_at == d

    def test_inspection_interval_months_setter_and_getter(self):
        """inspection_interval_months プロパティのセット・取得が正しく動作する"""
        dto = EquipmentDto()
        dto.inspection_interval_months = 6
        assert dto.inspection_interval_months == 6

    def test_assigned_user_id_setter_and_getter(self):
        """assigned_user_id プロパティのセット・取得が正しく動作する"""
        dto = EquipmentDto()
        dto.assigned_user_id = 5
        assert dto.assigned_user_id == 5

    def test_assigned_user_name_setter_and_getter(self):
        """assigned_user_name プロパティのセット・取得が正しく動作する"""
        dto = EquipmentDto()
        dto.assigned_user_name = '山田太郎'
        assert dto.assigned_user_name == '山田太郎'

    def test_area_setter_and_getter(self):
        """area プロパティのセット・取得が正しく動作する"""
        dto = EquipmentDto()
        dto.area = '東京'
        assert dto.area == '東京'

    def test_next_inspection_date_setter_and_getter(self):
        """next_inspection_date プロパティのセット・取得が正しく動作する"""
        dto = EquipmentDto()
        d = date(2026, 7, 1)
        dto.next_inspection_date = d
        assert dto.next_inspection_date == d

    def test_latest_inspection_status_setter_and_getter(self):
        """latest_inspection_status プロパティのセット・取得が正しく動作する"""
        dto = EquipmentDto()
        dto.latest_inspection_status = 'normal'
        assert dto.latest_inspection_status == 'normal'

    def test_deleted_at_setter_and_getter(self):
        """deleted_at プロパティのセット・取得が正しく動作する"""
        from datetime import datetime
        dto = EquipmentDto()
        dt = datetime(2026, 6, 1, 10, 0, 0)
        dto.deleted_at = dt
        assert dto.deleted_at == dt

    def test_deleted_by_name_setter_and_getter(self):
        """deleted_by_name プロパティのセット・取得が正しく動作する"""
        dto = EquipmentDto()
        dto.deleted_by_name = '管理者 太郎'
        assert dto.deleted_by_name == '管理者 太郎'


class TestEquipmentDtoDeadlineStatus:
    """EquipmentDto の deadline_status プロパティテスト"""

    def test_deadline_status_overdue(self):
        """deadline_status に 'overdue' をセットして取得できる"""
        dto = EquipmentDto()
        dto.deadline_status = 'overdue'
        assert dto.deadline_status == 'overdue'

    def test_deadline_status_soon(self):
        """deadline_status に 'soon' をセットして取得できる"""
        dto = EquipmentDto()
        dto.deadline_status = 'soon'
        assert dto.deadline_status == 'soon'

    def test_deadline_status_normal(self):
        """deadline_status に 'normal' をセットして取得できる"""
        dto = EquipmentDto()
        dto.deadline_status = 'normal'
        assert dto.deadline_status == 'normal'

    def test_deadline_status_none_for_uninspected(self):
        """next_inspection_date が未設定の場合は deadline_status に None をセットできる"""
        dto = EquipmentDto()
        dto.deadline_status = None
        assert dto.deadline_status is None
