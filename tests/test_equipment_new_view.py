"""
tests/test_equipment_new_view.py

書類No.004 設備マスタ登録機能 / 設備登録画面 の単体テスト。

テスト対象：
  GET  /equipment/new  → equipment_new_get
  POST /equipment/new  → equipment_new_post

テスト項目（単体テスト対象のみ）：
  項目1: 管理者アクセス（GET）             → ステータスコード200
  項目2: FEアクセス（GET）                 → ステータスコード302（ダッシュボードへ）
  項目4: 未入力チェック（POST）            → ステータスコード200・エラーメッセージ
  項目5: 点検間隔バリデーション（POST）    → ステータスコード200・エラーメッセージ
  項目6: 正常登録・担当者なし（POST）      → ステータスコード302・/equipment
  項目7: 正常登録・担当者あり（POST）      → ステータスコード302・/equipment
"""

import pytest
from unittest.mock import patch
from tests.conftest import login_as


# ==============================================================
# 正常フォームの基本値
# ==============================================================

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


# ==============================================================
# 1. GET /equipment/new  ─ アクセス制御テスト
# ==============================================================

class TestEquipmentNewGet:
    """GET /equipment/new のアクセス制御テスト（項目1・2）"""

    @patch('app.views.equipment.UserDao')
    def test_admin_can_access(self, MockUserDao, client):
        """項目1：adminは設備登録フォームにアクセスできる（ステータスコード200）"""
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.get('/equipment/new')
        assert response.status_code == 200

    def test_engineer_is_redirected_to_dashboard(self, client):
        """項目2：engineerは設備登録フォームにアクセスできずダッシュボードへリダイレクトされる（ステータスコード302）"""
        login_as(client, 'engineer')
        response = client.get('/equipment/new')
        assert response.status_code == 302
        assert '/dashboard' in response.location


# ==============================================================
# 2. POST /equipment/new  ─ バリデーション・登録処理テスト
# ==============================================================

class TestEquipmentNewPost:
    """POST /equipment/new のバリデーション・登録処理テスト（項目4・5・6・7）"""

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_missing_required_fields_shows_error(self, MockEquipmentDao, MockUserDao, client):
        """項目4：必須項目が空の場合、ステータスコード200でエラーメッセージが表示される"""
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.post('/equipment/new', data={
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
        """項目5（境界値 0）：点検間隔が0の場合、ステータスコード200でエラーメッセージが表示される"""
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.post('/equipment/new', data={
            **_VALID_FORM,
            'inspection_interval_months': '0',
        })
        assert response.status_code == 200
        assert '点検間隔は1〜12の整数を入力してください' in response.data.decode('utf-8')

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_interval_thirteen_shows_error(self, MockEquipmentDao, MockUserDao, client):
        """項目5（境界値 13）：点検間隔が13の場合、ステータスコード200でエラーメッセージが表示される"""
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.post('/equipment/new', data={
            **_VALID_FORM,
            'inspection_interval_months': '13',
        })
        assert response.status_code == 200
        assert '点検間隔は1〜12の整数を入力してください' in response.data.decode('utf-8')

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_valid_post_without_assigned_user_redirects(self, MockEquipmentDao, MockUserDao, client):
        """項目6：担当者なしで正しい値を送信すると、DBに登録されて302で設備一覧へリダイレクトされる"""
        MockUserDao.return_value.find_by_role.return_value = []
        MockEquipmentDao.return_value.create.return_value = None
        login_as(client, 'admin')
        response = client.post('/equipment/new', data=_VALID_FORM)
        assert response.status_code == 302
        assert '/equipment' in response.location
        MockEquipmentDao.return_value.create.assert_called_once()

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_valid_post_with_assigned_user_redirects(self, MockEquipmentDao, MockUserDao, client):
        """項目7：担当者ありで正しい値を送信すると、DBに登録されて302で設備一覧へリダイレクトされる"""
        MockUserDao.return_value.find_by_role.return_value = []
        MockEquipmentDao.return_value.create.return_value = None
        login_as(client, 'admin')
        response = client.post('/equipment/new', data={
            **_VALID_FORM,
            'assigned_user_id': '1',
        })
        assert response.status_code == 302
        assert '/equipment' in response.location
        MockEquipmentDao.return_value.create.assert_called_once()
