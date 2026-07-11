"""
tests/test_password_change_view.py

B-06: パスワード変更機能テスト（書類No.011）

テスト対象：
  GET  /my/password → my_password_get
  POST /my/password → my_password_post

テスト項目：
  項目1: 未認証アクセス（GET → 302・/login）
  項目2: engineer で GET → 200
  項目3: admin で GET → 200
  項目5: 現在のパスワード未入力（POST → 200・エラーメッセージ）
  項目6: 新しいパスワード未入力（POST → 200・エラーメッセージ）
  項目7: 確認パスワード不一致（POST → 200・エラーメッセージ）
  項目8: 現在のパスワード誤り（POST → 200・エラーメッセージ）
  項目9: パスワード変更成功（POST → 302）
"""

import pytest
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash
from tests.conftest import login_as


def _make_user_dto(id=1, role='engineer', password=None):
    """テスト用 UserDto モックを生成する。"""
    user = MagicMock()
    user.id          = id
    user.employee_no = 'ENG-001'
    user.last_name   = 'テスト'
    user.first_name  = 'ユーザー'
    user.email       = 'test@example.com'
    user.role        = role
    user.phone       = None
    user.base        = '東京'
    # パスワード未指定の場合はデフォルト値をハッシュ化する
    user.password    = password or generate_password_hash('password123')
    return user


# ==============================================================
# GET /my/password ─ パスワード変更フォーム表示テスト
# ==============================================================

class TestMyPasswordGet:
    """GET /my/password のアクセス制御テスト（項目1・2・3）"""

    def test_unauthenticated_redirects_to_login(self, client):
        """項目1: 未認証でアクセスすると 302 で /login へリダイレクトされる"""
        response = client.get('/my/password')
        assert response.status_code == 302
        assert '/login' in response.location

    @patch('app.views.account_view.UserDao')
    def test_engineer_can_access(self, MockUserDao, client):
        """項目2: engineer セッションでアクセスすると 200 が返る"""
        login_as(client, 'engineer', user_id=1)
        response = client.get('/my/password')
        assert response.status_code == 200

    @patch('app.views.account_view.UserDao')
    def test_admin_can_access(self, MockUserDao, client):
        """項目3: admin セッションでアクセスすると 200 が返る"""
        login_as(client, 'admin', user_id=2)
        response = client.get('/my/password')
        assert response.status_code == 200

    @patch('app.views.account_view.UserDao')
    def test_root_can_access(self, MockUserDao, client):
        """項目4: root セッションでアクセスすると 200 が返る（B-09）"""
        login_as(client, 'root', user_id=3)
        response = client.get('/my/password')
        assert response.status_code == 200


# ==============================================================
# POST /my/password ─ パスワード変更処理テスト
# ==============================================================

class TestMyPasswordPost:
    """POST /my/password のバリデーション・変更処理テスト（項目5〜9）"""

    @patch('app.views.account_view.UserDao')
    def test_missing_current_password_shows_error(self, MockUserDao, client):
        """項目5: 現在のパスワードを空にしてPOSTすると 200 でエラーメッセージが表示される"""
        MockUserDao.return_value.find_by_id.return_value = _make_user_dto()
        login_as(client, 'engineer', user_id=1)
        response = client.post('/my/password', data={
            'current_password': '',
            'new_password':     'newpassword',
            'confirm_password': 'newpassword',
        })
        assert response.status_code == 200
        assert '現在のパスワードを入力してください' in response.data.decode('utf-8')

    @patch('app.views.account_view.UserDao')
    def test_missing_new_password_shows_error(self, MockUserDao, client):
        """項目6: 新しいパスワードを空にしてPOSTすると 200 でエラーメッセージが表示される"""
        MockUserDao.return_value.find_by_id.return_value = _make_user_dto()
        login_as(client, 'engineer', user_id=1)
        response = client.post('/my/password', data={
            'current_password': 'password123',
            'new_password':     '',
            'confirm_password': '',
        })
        assert response.status_code == 200
        assert '新しいパスワードを2回入力してください' in response.data.decode('utf-8')

    @patch('app.views.account_view.UserDao')
    def test_confirm_password_mismatch_shows_error(self, MockUserDao, client):
        """項目7: 新しいパスワードと確認パスワードが不一致の場合 200 でエラーメッセージが表示される"""
        MockUserDao.return_value.find_by_id.return_value = _make_user_dto()
        login_as(client, 'engineer', user_id=1)
        response = client.post('/my/password', data={
            'current_password': 'password123',
            'new_password':     'newpassword1',
            'confirm_password': 'newpassword2',
        })
        assert response.status_code == 200
        assert '新しいパスワードが一致しません' in response.data.decode('utf-8')

    @patch('app.views.account_view.check_password_hash', return_value=False)
    @patch('app.views.account_view.UserDao')
    def test_wrong_current_password_shows_error(self, MockUserDao, mock_check_pw, client):
        """項目8: 現在のパスワードが誤っている場合 200 でエラーメッセージが表示される"""
        MockUserDao.return_value.find_by_id.return_value = _make_user_dto()
        login_as(client, 'engineer', user_id=1)
        response = client.post('/my/password', data={
            'current_password': 'wrongpassword',
            'new_password':     'newpassword',
            'confirm_password': 'newpassword',
        })
        assert response.status_code == 200
        assert '現在のパスワードが正しくありません' in response.data.decode('utf-8')

    @patch('app.views.account_view.check_password_hash', return_value=True)
    @patch('app.views.account_view.UserDao')
    def test_valid_password_change_shows_success(self, MockUserDao, mock_check_pw, client):
        """項目9: 正しい入力でPOSTすると 200 で成功メッセージが表示され、update() が呼ばれる"""
        MockUserDao.return_value.find_by_id.return_value = _make_user_dto()
        login_as(client, 'engineer', user_id=1)
        response = client.post('/my/password', data={
            'current_password': 'password123',
            'new_password':     'newpassword',
            'confirm_password': 'newpassword',
        })
        assert response.status_code == 200
        assert 'パスワードを変更しました' in response.data.decode('utf-8')
        # update() が1回呼ばれたことを確認する
        MockUserDao.return_value.update.assert_called_once()
