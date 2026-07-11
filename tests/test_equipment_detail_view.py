"""
tests/test_equipment_detail_view.py

書類No.005 設備マスタ詳細表示機能 / 設備詳細画面 の単体テスト。

テスト対象：
  GET /equipment/<id>  → equipment_detail_get

テスト項目（単体テスト対象のみ）：
  項目1: 管理者アクセス       → ステータスコード200
  項目2: FE担当外設備アクセス → ステータスコード302（ダッシュボードへ）
  項目3: FE担当設備アクセス   → ステータスコード200
"""

import pytest
from unittest.mock import patch
from app.dto.equipment_dto import EquipmentDto
from tests.conftest import login_as


# ==============================================================
# テストデータ生成ヘルパー
# ==============================================================

def _make_equipment(id=1, name='テスト空調', location='1F機械室',
                    equipment_type='空調', manufacturer='ダイキン',
                    model_number='TEST-001', installed_at='2020-04-01',
                    inspection_interval_months=6, assigned_user_id=None,
                    next_inspection_date=None):
    """テスト用 EquipmentDto を生成する。"""
    dto = EquipmentDto()
    dto.id = id
    dto.name = name
    dto.location = location
    dto.equipment_type = equipment_type
    dto.manufacturer = manufacturer
    dto.model_number = model_number
    dto.installed_at = installed_at
    dto.inspection_interval_months = inspection_interval_months
    dto.assigned_user_id = assigned_user_id
    dto.next_inspection_date = next_inspection_date
    return dto


# ==============================================================
# GET /equipment/<id>  ─ アクセス制御テスト
# ==============================================================

class TestEquipmentDetailGet:
    """GET /equipment/<id> のアクセス制御テスト（項目1・2・3）"""

    @patch('app.views.equipment.InspectionDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_admin_can_access(self, MockEquipmentDao, MockInspectionDao, client):
        """項目1：admin は設備詳細画面にアクセスできる（ステータスコード200）"""
        MockEquipmentDao.return_value.find_by_id.return_value = _make_equipment(id=1)
        MockInspectionDao.return_value.find_by_equipment_id.return_value = []
        login_as(client, 'admin')
        response = client.get('/equipment/1')
        assert response.status_code == 200

    @patch('app.views.equipment.InspectionDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_engineer_cannot_access_unassigned_equipment(self, MockEquipmentDao, MockInspectionDao, client):
        """項目2：engineer は担当外の設備詳細にアクセスできずダッシュボードへリダイレクトされる（ステータスコード302）"""
        # ログインユーザー（id=1）とは異なる担当者IDを持つ設備を返す
        MockEquipmentDao.return_value.find_by_id.return_value = _make_equipment(id=1, assigned_user_id=99)
        MockInspectionDao.return_value.find_by_equipment_id.return_value = []
        login_as(client, 'engineer', user_id=1)
        response = client.get('/equipment/1')
        assert response.status_code == 302
        assert '/dashboard' in response.location

    @patch('app.views.equipment.InspectionDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_engineer_can_access_own_assigned_equipment(self, MockEquipmentDao, MockInspectionDao, client):
        """項目3：engineer は自分の担当設備の詳細にアクセスできる（ステータスコード200）"""
        # ログインユーザー（id=1）と同じ担当者IDを持つ設備を返す
        MockEquipmentDao.return_value.find_by_id.return_value = _make_equipment(id=1, assigned_user_id=1)
        MockInspectionDao.return_value.find_by_equipment_id.return_value = []
        login_as(client, 'engineer', user_id=1)
        response = client.get('/equipment/1')
        assert response.status_code == 200
