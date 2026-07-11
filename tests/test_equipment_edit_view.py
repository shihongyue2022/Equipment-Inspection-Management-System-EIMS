"""
tests/test_equipment_edit_view.py

書類No.006 設備マスタ編集機能 / 設備編集画面 の単体テスト。

テスト対象：
  GET  /equipment/<id>/edit  → equipment_edit_get
  POST /equipment/<id>/edit  → equipment_edit_post

テスト項目（単体テスト対象のみ）：
  項目1: 管理者アクセス（GET） → ステータスコード200
  項目2: FEアクセス（GET）    → ステータスコード302（ダッシュボードへ）
  項目4: 必須項目未入力（POST）→ ステータスコード200・エラーメッセージ表示
  項目5: 点検間隔バリデーション（0・13）→ ステータスコード200・エラーメッセージ表示
  項目6: 正常更新（POST）     → ステータスコード302・DBのupdate呼び出し確認
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
# 1. GET /equipment/<id>/edit  ─ アクセス制御テスト
# ==============================================================

class TestEquipmentEditGet:
    """GET /equipment/<id>/edit のアクセス制御テスト（項目1・2）"""

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_admin_can_access(self, MockEquipmentDao, MockUserDao, client):
        """項目1：admin は設備編集画面にアクセスできる（ステータスコード200）"""
        MockEquipmentDao.return_value.find_by_id.return_value = _make_equipment()
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.get('/equipment/1/edit')
        assert response.status_code == 200

    def test_engineer_is_redirected_to_dashboard(self, client):
        """項目2：engineer は設備編集画面にアクセスできずダッシュボードへリダイレクトされる（ステータスコード302）"""
        login_as(client, 'engineer')
        response = client.get('/equipment/1/edit')
        assert response.status_code == 302
        assert '/dashboard' in response.location


# ==============================================================
# 2. POST /equipment/<id>/edit  ─ バリデーション・更新処理テスト
# ==============================================================

class TestEquipmentEditPost:
    """POST /equipment/<id>/edit のバリデーション・更新処理テスト（項目4・5・6）"""

    # 正常な更新フォームの基本値
    _VALID_FORM = {
        'name':                       'テスト空調',
        'location':                   '1F機械室',
        'equipment_type':             '空調',
        'manufacturer':               'ダイキン',
        'model_number':               'TEST-001',
        'installed_at':               '2020-04-01',
        'inspection_interval_months': '6',
        'assigned_user_id':           '',
    }

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_missing_required_fields_shows_error(self, MockEquipmentDao, MockUserDao, client):
        """項目4：必須項目が空の場合、ステータスコード200でエラーメッセージが表示される"""
        MockEquipmentDao.return_value.find_by_id.return_value = _make_equipment()
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.post('/equipment/1/edit', data={
            'name':                       '',
            'location':                   '',
            'equipment_type':             '',
            'manufacturer':               '',
            'model_number':               '',
            'installed_at':               '',
            'inspection_interval_months': '',
            'assigned_user_id':           '',
        })
        assert response.status_code == 200
        assert '必須項目をすべて入力してください' in response.data.decode('utf-8')

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_interval_zero_shows_error(self, MockEquipmentDao, MockUserDao, client):
        """項目5（境界値 0）：点検間隔が 0 の場合、ステータスコード200でエラーメッセージが表示される"""
        MockEquipmentDao.return_value.find_by_id.return_value = _make_equipment()
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.post('/equipment/1/edit', data={
            **self._VALID_FORM,
            'inspection_interval_months': '0',
        })
        assert response.status_code == 200
        assert '点検間隔は1〜12の整数を入力してください' in response.data.decode('utf-8')

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_interval_thirteen_shows_error(self, MockEquipmentDao, MockUserDao, client):
        """項目5（境界値 13）：点検間隔が 13 の場合、ステータスコード200でエラーメッセージが表示される"""
        MockEquipmentDao.return_value.find_by_id.return_value = _make_equipment()
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.post('/equipment/1/edit', data={
            **self._VALID_FORM,
            'inspection_interval_months': '13',
        })
        assert response.status_code == 200
        assert '点検間隔は1〜12の整数を入力してください' in response.data.decode('utf-8')

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_valid_update_redirects_and_calls_dao_update(self, MockEquipmentDao, MockUserDao, client):
        """項目6：正しい値で送信した場合、DBが更新されてステータスコード302で設備一覧にリダイレクトされる"""
        MockEquipmentDao.return_value.find_by_id.return_value = _make_equipment()
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.post('/equipment/1/edit', data=self._VALID_FORM)
        assert response.status_code == 302
        assert '/equipment' in response.location
        # DAO の update が1回呼ばれたことを確認する
        MockEquipmentDao.return_value.update.assert_called_once()
