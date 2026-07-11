"""
tests/test_equipment_list_view.py

書類No.003 設備マスタ一覧・担当者変更・削除機能 / 設備一覧画面 の単体テスト。

テスト対象：
  GET  /equipment              → equipment_list_get
  POST /equipment/<id>/delete  → equipment_delete_post
  POST /equipment/<id>/assign  → equipment_assign_post

テスト項目（単体テスト対象のみ）：
  項目1:  admin アクセス（GET）    → ステータスコード200
  項目2:  engineer アクセス（GET） → ステータスコード302（ダッシュボードへ）
  項目3:  未認証アクセス（GET）    → ステータスコード302（ログインへ）
  項目8:  削除（点検記録なし）     → ステータスコード302・delete 呼び出し確認
  項目9:  削除制限（点検記録あり） → ステータスコード302・delete 例外処理確認
  項目10: 担当者変更               → ステータスコード302・update_assigned_user 呼び出し確認
"""

import pytest
from unittest.mock import patch
from app.dto.equipment_dto import EquipmentDto
from tests.conftest import login_as


# ==============================================================
# テストデータ生成ヘルパー
# ==============================================================

def _make_equipment(id=1, name='テスト空調'):
    """テスト用 EquipmentDto を生成する。"""
    dto = EquipmentDto()
    dto.id = id
    dto.name = name
    dto.location = '1F機械室'
    dto.equipment_type = '空調'
    dto.manufacturer = 'ダイキン'
    dto.model_number = 'TEST-001'
    dto.installed_at = '2020-04-01'
    dto.inspection_interval_months = 6
    dto.assigned_user_id = None
    dto.next_inspection_date = None
    return dto


# ==============================================================
# 1. GET /equipment  ─ アクセス制御テスト
# ==============================================================

class TestEquipmentListGet:
    """GET /equipment のアクセス制御テスト（項目1・2・3）"""

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_admin_can_access(self, MockEquipmentDao, MockUserDao, client):
        """項目1：adminは設備一覧画面にアクセスできる（ステータスコード200）"""
        MockEquipmentDao.return_value.find_all.return_value = []
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.get('/equipment')
        assert response.status_code == 200

    def test_engineer_is_redirected_to_dashboard(self, client):
        """項目2：engineerは設備一覧画面にアクセスできずダッシュボードへリダイレクトされる（ステータスコード302）"""
        login_as(client, 'engineer')
        response = client.get('/equipment')
        assert response.status_code == 302
        assert '/dashboard' in response.location

    def test_unauthenticated_is_redirected_to_login(self, client):
        """項目3：未ログイン状態でアクセスすると302で/loginへリダイレクトされる"""
        response = client.get('/equipment')
        assert response.status_code == 302
        assert '/login' in response.location


# ==============================================================
# 2. POST /equipment/<id>/delete  ─ 削除処理テスト
# ==============================================================

class TestEquipmentDeletePost:
    """POST /equipment/<id>/delete の削除処理テスト（項目8・9）"""

    @patch('app.views.equipment.EquipmentDao')
    def test_delete_equipment_without_inspection_records(self, MockEquipmentDao, client):
        """項目8：点検記録のない設備を削除すると302で設備一覧へリダイレクトされ、DAOのdeleteが呼ばれる"""
        MockEquipmentDao.return_value.find_by_id.return_value = _make_equipment()
        MockEquipmentDao.return_value.delete.return_value = None
        login_as(client, 'admin')
        response = client.post('/equipment/1/delete')
        assert response.status_code == 302
        assert '/equipment' in response.location
        # 実装は delete(id, deleted_by_id) の2引数で呼ぶ。admin の user_id は login_as デフォルト値 1
        MockEquipmentDao.return_value.delete.assert_called_once_with(1, 1)

    @patch('app.views.equipment.EquipmentDao')
    def test_delete_equipment_with_inspection_records_is_rejected(self, MockEquipmentDao, client):
        """項目9：点検記録のある設備はdelete()が例外を発生させ、302で設備一覧へリダイレクトされる"""
        MockEquipmentDao.return_value.find_by_id.return_value = _make_equipment()
        # 外部キー制約エラーをシミュレートする
        MockEquipmentDao.return_value.delete.side_effect = Exception('foreign key constraint')
        login_as(client, 'admin')
        response = client.post('/equipment/1/delete')
        assert response.status_code == 302
        assert '/equipment' in response.location
        # delete() が呼ばれたことを確認する（例外により削除は失敗している）
        MockEquipmentDao.return_value.delete.assert_called_once_with(1, 1)


# ==============================================================
# 3. POST /equipment/<id>/assign  ─ 担当者変更テスト
# ==============================================================

class TestEquipmentAssignPost:
    """POST /equipment/<id>/assign の担当者変更テスト（項目10）"""

    @patch('app.views.equipment.EquipmentDao')
    def test_assign_updates_assigned_user(self, MockEquipmentDao, client):
        """項目10：担当者変更でupdate_assigned_userが呼ばれ、302で設備一覧へリダイレクトされる"""
        MockEquipmentDao.return_value.update_assigned_user.return_value = None
        login_as(client, 'admin')
        response = client.post('/equipment/1/assign', data={'assigned_user_id': '5'})
        assert response.status_code == 302
        assert '/equipment' in response.location
        MockEquipmentDao.return_value.update_assigned_user.assert_called_once_with(1, 5, changed_by=1)
