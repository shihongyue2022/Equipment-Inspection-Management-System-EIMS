"""
tests/test_inspection_view.py

書類No.010 点検記録登録機能 / 点検記録登録画面 の単体テスト。

テスト対象：
  GET  /inspection/new  → inspection_new_get
  POST /inspection/new  → inspection_new_post

テスト項目（単体テスト対象のみ）：
  項目1: 未認証アクセス（GET）             → ステータスコード302・/login
  項目5: 未入力チェック（POST）            → ステータスコード200・エラーメッセージ
  項目6: FE担当外設備への登録阻止（POST）  → ステータスコード302・ダッシュボード
  項目7: 正常登録・normal（POST）          → ステータスコード302・InspectionDao.create 呼び出し確認
  項目8: 正常登録・watch（POST）           → ステータスコード302・ダッシュボード
  項目9: 正常登録・repair（POST）          → ステータスコード302・ダッシュボード
"""

import pytest
from unittest.mock import patch, MagicMock
from tests.conftest import login_as


# ==============================================================
# テストデータ生成ヘルパー
# ==============================================================

def _make_equipment_mock(id=1, assigned_user_id=1):
    """テスト用 EquipmentDto モックを生成する。"""
    eq = MagicMock()
    eq.id = id
    eq.assigned_user_id = assigned_user_id
    return eq


# ==============================================================
# 1. GET /inspection/new  ─ アクセス制御テスト
# ==============================================================

class TestInspectionNewGet:
    """GET /inspection/new のアクセス制御テスト（項目1）"""

    def test_unauthenticated_redirects_to_login(self, client):
        """項目1：未ログイン状態でアクセスすると302で/loginへリダイレクトされる"""
        response = client.get('/inspection/new')
        assert response.status_code == 302
        assert '/login' in response.location


# ==============================================================
# 2. POST /inspection/new  ─ バリデーション・登録処理テスト
# ==============================================================

class TestInspectionNewPost:
    """POST /inspection/new のバリデーション・登録処理テスト（項目5・6・7・8・9）"""

    @patch('app.views.inspection_view.EquipmentDao')
    def test_missing_required_fields_shows_error(self, MockEquipmentDao, client):
        """項目5：必須項目（対象設備・実施日・点検ステータス）が空の場合、ステータスコード200でエラーメッセージが表示される"""
        MockEquipmentDao.return_value.find_all.return_value = []
        login_as(client, 'admin')
        response = client.post('/inspection/new', data={
            'equipment_id': '',
            'inspected_at': '',
            'status':       '',
            'note':         '',
        })
        assert response.status_code == 200
        assert '必須項目をすべて入力してください' in response.data.decode('utf-8')

    @patch('app.views.inspection_view.EquipmentDao')
    def test_engineer_cannot_register_for_unassigned_equipment(self, MockEquipmentDao, client):
        """項目6：engineerが担当外の設備IDを送信すると302でダッシュボードへリダイレクトされる"""
        # user_id=1 の担当設備として id=2 を返す（id=99 は担当外）
        MockEquipmentDao.return_value.find_by_user_id.return_value = [
            _make_equipment_mock(id=2, assigned_user_id=1)
        ]
        login_as(client, 'engineer', user_id=1)
        response = client.post('/inspection/new', data={
            'equipment_id': '99',
            'inspected_at': '2026-06-18',
            'status':       'normal',
            'note':         '',
        })
        assert response.status_code == 302
        assert '/dashboard' in response.location

    @patch('app.views.inspection_view.EquipmentDao')
    @patch('app.views.inspection_view.InspectionDao')
    def test_valid_registration_normal_status(self, MockInspectionDao, MockEquipmentDao, client):
        """項目7：ステータスnormalで正常登録すると302でダッシュボードへリダイレクトされ、InspectionDao.createが呼ばれる"""
        MockEquipmentDao.return_value.find_all.return_value = [_make_equipment_mock()]
        MockEquipmentDao.return_value.update_next_inspection_date.return_value = None
        MockInspectionDao.return_value.create.return_value = None
        login_as(client, 'admin')
        response = client.post('/inspection/new', data={
            'equipment_id': '1',
            'inspected_at': '2026-06-18',
            'status':       'normal',
            'note':         '',
        })
        assert response.status_code == 302
        assert '/dashboard' in response.location
        MockInspectionDao.return_value.create.assert_called_once()

    @patch('app.views.inspection_view.EquipmentDao')
    @patch('app.views.inspection_view.InspectionDao')
    def test_valid_registration_watch_status(self, MockInspectionDao, MockEquipmentDao, client):
        """項目8：ステータスwatchで正常登録すると302でダッシュボードへリダイレクトされる"""
        MockEquipmentDao.return_value.find_all.return_value = [_make_equipment_mock()]
        MockEquipmentDao.return_value.update_next_inspection_date.return_value = None
        MockInspectionDao.return_value.create.return_value = None
        login_as(client, 'admin')
        response = client.post('/inspection/new', data={
            'equipment_id': '1',
            'inspected_at': '2026-06-18',
            'status':       'watch',
            'note':         '要観察',
        })
        assert response.status_code == 302
        assert '/dashboard' in response.location

    @patch('app.views.inspection_view.EquipmentDao')
    @patch('app.views.inspection_view.InspectionDao')
    def test_valid_registration_repair_status(self, MockInspectionDao, MockEquipmentDao, client):
        """
        項目9：ステータスrepairで正常登録すると302でダッシュボードへリダイレクトされる
        repair の場合は repair_next_date（実施日より後）と note が必須。
        view は set_next_inspection_date() を呼ぶため mock が必要。
        """
        MockEquipmentDao.return_value.find_all.return_value = [_make_equipment_mock()]
        MockEquipmentDao.return_value.set_next_inspection_date.return_value = None
        MockInspectionDao.return_value.create.return_value = None
        login_as(client, 'admin')
        response = client.post('/inspection/new', data={
            'equipment_id':    '1',
            'inspected_at':    '2026-06-18',
            'status':          'repair',
            'note':            '修理が必要',
            # repair_next_date は実施日より後の日付が必須
            'repair_next_date': '2026-07-01',
        })
        assert response.status_code == 302
        assert '/dashboard' in response.location
