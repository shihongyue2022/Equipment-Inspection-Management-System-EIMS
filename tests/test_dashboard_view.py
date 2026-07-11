"""
tests/test_dashboard_view.py

書類No.002 ダッシュボード表示機能 / ダッシュボード画面 の単体テスト（項目1・4・5）。
書類No.015 ダッシュボード拠点フィルタ修正確認 / ダッシュボード画面（再テスト）（項目1〜4）。

テスト対象：
  GET /dashboard  → dashboard_get

書類No.002 テスト項目：
  項目1: 未認証アクセス（302・/login）
  項目4: 管理者アクセス（200・EquipmentDao.find_all が呼ばれる）
  項目5: FEアクセス（200・EquipmentDao.find_by_user_id が呼ばれる）

書類No.015 テスト項目（単体テスト・結合テスト）：
  項目1: 拠点パラメータあり → find_all_by_base() が指定拠点で呼ばれる（単体）
  項目2: 拠点選択で対象設備のみ表示される（結合）
  項目3: 拠点未選択（全拠点）→ find_all() が呼ばれ全件表示（結合）
  項目4: FEには拠点フィルタの select が描画されない（結合）
"""

import pytest
from unittest.mock import patch, MagicMock
from tests.conftest import login_as


# ==============================================================
# テストデータ生成ヘルパー
# ==============================================================

def _make_equipment_mock():
    """テスト用 EquipmentDto モックを生成する。next_inspection_date を None にして get_deadline_status が安全に動作するようにする。"""
    eq = MagicMock()
    eq.next_inspection_date = None
    eq.latest_inspection_status = None
    eq.deadline_status = None
    return eq


def _make_equipment_mock_with_name(name='テスト設備', eq_id=1):
    """テスト用 EquipmentDto モックを設備名・ID 付きで生成する。テンプレート描画確認用。"""
    eq = MagicMock()
    eq.id = eq_id
    eq.name = name
    eq.next_inspection_date = None
    eq.latest_inspection_status = None
    eq.deadline_status = None
    eq.assigned_user_id = None
    return eq


def _setup_admin_analytics_mocks(MockEquipmentDao, MockUserDao, bases=None):
    """管理者ダッシュボード用の分析系 DAO メソッドをまとめてモックするヘルパー関数。

    json.dumps() に渡されるメソッドは空リストを、
    整数演算（先週比計算）に使うカウントメソッドは 0 を返すように設定する。
    MagicMock のままにしておくと JSON シリアライズや整数演算で例外が発生するため必須。
    """
    # json.dumps() に渡す find_stats_by_base / find_weekly_schedule はリストを返す
    MockEquipmentDao.return_value.find_stats_by_base.return_value = []
    MockEquipmentDao.return_value.find_weekly_schedule.return_value = []
    # テンプレートでループするため find_stats_by_engineer もリストを返す
    MockEquipmentDao.return_value.find_stats_by_engineer.return_value = []
    # 先週比の整数演算（overdue_count - overdue_last_week 等）に使うため 0 を返す
    MockEquipmentDao.return_value.count_overdue_7days_ago.return_value = 0
    MockEquipmentDao.return_value.count_soon_7days_ago.return_value = 0
    MockEquipmentDao.return_value.count_repair_7days_ago.return_value = 0
    MockEquipmentDao.return_value.count_unassigned_7days_ago.return_value = 0
    # 拠点フィルタ UI の表示用拠点一覧
    MockUserDao.return_value.find_distinct_bases.return_value = (
        bases if bases is not None else ['東京', '大阪']
    )


# ==============================================================
# GET /dashboard  ─ アクセス制御・表示テスト（書類No.002）
# ==============================================================

class TestDashboardGet:
    """GET /dashboard のテスト（書類No.002 項目1・4・5）"""

    def test_unauthenticated_redirects_to_login(self, client):
        """項目1：未ログイン状態でアクセスすると302で/loginへリダイレクトされる"""
        response = client.get('/dashboard')
        assert response.status_code == 302
        assert '/login' in response.location

    @patch('app.views.dashboard_view.UserDao')
    @patch('app.views.dashboard_view.EquipmentDao')
    def test_admin_uses_find_all(self, MockEquipmentDao, MockUserDao, client):
        """
        項目4：adminでアクセスすると全設備を取得するfind_allが呼ばれ、200が返る
        find_stats_by_base() の戻り値が MagicMock のまま json.dumps() に渡ると
        TypeError が発生するため、分析系 DAO を正しい型でモックする必要がある。
        """
        MockEquipmentDao.return_value.find_all.return_value = [_make_equipment_mock()]
        _setup_admin_analytics_mocks(MockEquipmentDao, MockUserDao)
        login_as(client, 'admin')
        response = client.get('/dashboard')
        assert response.status_code == 200
        MockEquipmentDao.return_value.find_all.assert_called_once()

    @patch('app.views.dashboard_view.EquipmentDao')
    def test_engineer_uses_find_by_user_id(self, MockEquipmentDao, client):
        """項目5：engineerでアクセスすると担当設備のみを取得するfind_by_user_idが呼ばれ、200が返る"""
        MockEquipmentDao.return_value.find_by_user_id.return_value = [_make_equipment_mock()]
        login_as(client, 'engineer', user_id=1)
        response = client.get('/dashboard')
        assert response.status_code == 200
        MockEquipmentDao.return_value.find_by_user_id.assert_called_once_with(1)


# ==============================================================
# GET /dashboard ─ 拠点フィルタ修正確認テスト（書類No.015）
# ==============================================================

class TestDashboardBaseFilter:
    """GET /dashboard の拠点フィルタ機能テスト（書類No.015 項目1〜4）"""

    @patch('app.views.dashboard_view.UserDao')
    @patch('app.views.dashboard_view.EquipmentDao')
    def test_find_all_by_base_is_called_with_base_param(self, MockEquipmentDao, MockUserDao, client):
        """
        書類No.015 項目1（単体）: ?base=東京 を渡すと find_all_by_base('東京') が1回呼ばれる
        find_all() ではなく find_all_by_base() が呼ばれていることを確認する。
        """
        MockEquipmentDao.return_value.find_all_by_base.return_value = [_make_equipment_mock()]
        _setup_admin_analytics_mocks(MockEquipmentDao, MockUserDao)
        login_as(client, 'admin', user_id=2)

        response = client.get('/dashboard?base=東京')

        assert response.status_code == 200
        MockEquipmentDao.return_value.find_all_by_base.assert_called_once_with('東京')
        MockEquipmentDao.return_value.find_all.assert_not_called()

    @patch('app.views.dashboard_view.UserDao')
    @patch('app.views.dashboard_view.EquipmentDao')
    def test_base_filter_shows_only_base_equipment(self, MockEquipmentDao, MockUserDao, client):
        """
        書類No.015 項目2（結合）: 拠点フィルタで「東京」を選択すると東京の設備のみ表示される
        find_all_by_base('東京') が返した設備の名前が HTML 内に描画されることを確認する。
        """
        eq_tokyo = _make_equipment_mock_with_name(name='東京本社エアコン', eq_id=1)
        MockEquipmentDao.return_value.find_all_by_base.return_value = [eq_tokyo]
        _setup_admin_analytics_mocks(MockEquipmentDao, MockUserDao)
        login_as(client, 'admin', user_id=2)

        response = client.get('/dashboard?base=東京')

        assert response.status_code == 200
        assert '東京本社エアコン' in response.data.decode('utf-8')

    @patch('app.views.dashboard_view.UserDao')
    @patch('app.views.dashboard_view.EquipmentDao')
    def test_no_base_param_uses_find_all_and_shows_all(self, MockEquipmentDao, MockUserDao, client):
        """
        書類No.015 項目3（結合）: 拠点パラメータなし（全拠点）で全設備が表示される
        find_all() が呼ばれ、返された全設備が HTML に描画されることを確認する。
        """
        eq_tokyo = _make_equipment_mock_with_name(name='東京設備', eq_id=1)
        eq_osaka = _make_equipment_mock_with_name(name='大阪設備', eq_id=2)
        MockEquipmentDao.return_value.find_all.return_value = [eq_tokyo, eq_osaka]
        _setup_admin_analytics_mocks(MockEquipmentDao, MockUserDao)
        login_as(client, 'admin', user_id=2)

        response = client.get('/dashboard')

        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert '東京設備' in html
        assert '大阪設備' in html
        MockEquipmentDao.return_value.find_all.assert_called_once()
        MockEquipmentDao.return_value.find_all_by_base.assert_not_called()

    @patch('app.views.dashboard_view.EquipmentDao')
    def test_engineer_has_no_base_filter(self, MockEquipmentDao, client):
        """
        書類No.015 項目4（結合）: FE でアクセスすると拠点フィルタの select が描画されない
        管理者専用の拠点フィルタ UI（name="base" select）が HTML に存在しないことを確認する。
        """
        MockEquipmentDao.return_value.find_by_user_id.return_value = []
        login_as(client, 'engineer', user_id=1)

        response = client.get('/dashboard')

        assert response.status_code == 200
        assert 'name="base"' not in response.data.decode('utf-8')
