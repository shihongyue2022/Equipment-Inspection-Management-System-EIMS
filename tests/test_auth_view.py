"""
tests/test_auth_view.py

書類No.001 ユーザー認証機能 / ログイン画面 の単体テスト。

テスト対象：
  POST /login  → login_post
  GET  /logout → logout_get

テスト項目（単体テスト対象のみ）：
  項目3: ログイン成功（302・/dashboard）
  項目4: パスワード誤り（200・エラーメッセージ）
  項目5: 存在しない社員番号（200・エラーメッセージ）
  項目6: 未入力（200・エラーメッセージ）
  項目7: ログアウト（302・/login）
"""

import pytest
from unittest.mock import patch, MagicMock
from tests.conftest import login_as


# ==============================================================
# テストデータ生成ヘルパー
# ==============================================================

def _make_user(id=1, last_name='テスト', first_name='ユーザー',
               employee_no='ENG-001', role='engineer',
               password='hashed_password'):
    """テスト用ユーザーモックを生成する。"""
    user = MagicMock()
    user.id = id
    user.last_name = last_name
    user.first_name = first_name
    # full_name は UserDto のプロパティ。MagicMock のままだとセッション JSON シリアライズ時に TypeError が発生する
    user.full_name = f"{last_name}{first_name}"
    user.employee_no = employee_no
    user.role = role
    user.password = password
    # base が MagicMock のままだとセッション JSON シリアライズ時に TypeError が発生する
    user.base = None
    return user


# ==============================================================
# POST /login  ─ ログイン処理テスト
# ==============================================================

class TestLoginPost:
    """POST /login のログイン処理テスト（項目3・4・5・6）"""

    @patch('app.views.auth_view.check_password_hash', return_value=True)
    @patch('app.views.auth_view.UserDao')
    def test_valid_login_redirects_to_dashboard(self, MockUserDao, mock_check_pw, client):
        """項目3：正しい社員番号・パスワードでログインすると302でダッシュボードへリダイレクトされる"""
        # with文のコンテキストマネージャが dao インスタンスを返すように設定する
        MockUserDao.return_value.__enter__.return_value = MockUserDao.return_value
        MockUserDao.return_value.find_by_employee_no.return_value = _make_user()
        response = client.post('/login', data={
            'employee_no': 'ENG-001',
            'password':    'password123',
        })
        assert response.status_code == 302
        assert '/dashboard' in response.location

    @patch('app.views.auth_view.check_password_hash', return_value=False)
    @patch('app.views.auth_view.UserDao')
    def test_wrong_password_shows_error(self, MockUserDao, mock_check_pw, client):
        """項目4：パスワードが誤っている場合、ステータスコード200でエラーメッセージが表示される"""
        # with文のコンテキストマネージャが dao インスタンスを返すように設定する
        MockUserDao.return_value.__enter__.return_value = MockUserDao.return_value
        MockUserDao.return_value.find_by_employee_no.return_value = _make_user()
        response = client.post('/login', data={
            'employee_no': 'ENG-001',
            'password':    'wrongpassword',
        })
        assert response.status_code == 200
        assert '社員番号またはパスワードに誤りがあります' in response.data.decode('utf-8')

    @patch('app.views.auth_view.UserDao')
    def test_unknown_employee_no_shows_error(self, MockUserDao, client):
        """項目5：存在しない社員番号でPOSTした場合、ステータスコード200でエラーメッセージが表示される"""
        # with文のコンテキストマネージャが dao インスタンスを返すように設定する
        MockUserDao.return_value.__enter__.return_value = MockUserDao.return_value
        MockUserDao.return_value.find_by_employee_no.return_value = None
        response = client.post('/login', data={
            'employee_no': 'NOT-EXIST',
            'password':    'password123',
        })
        assert response.status_code == 200
        assert '社員番号またはパスワードに誤りがあります' in response.data.decode('utf-8')

    def test_empty_input_shows_error(self, client):
        """項目6：社員番号・パスワードともに空でPOSTした場合、ステータスコード200でエラーメッセージが表示される"""
        response = client.post('/login', data={
            'employee_no': '',
            'password':    '',
        })
        assert response.status_code == 200
        assert '入力情報に誤りがあります' in response.data.decode('utf-8')


# ==============================================================
# GET /logout  ─ ログアウトテスト
# ==============================================================

class TestLogoutGet:
    """GET /logout のログアウトテスト（項目7）"""

    def test_logout_redirects_to_login(self, client):
        """項目7：ログイン済みセッションでGET /logout にアクセスすると302で/loginへリダイレクトされる"""
        login_as(client, 'engineer')
        response = client.get('/logout')
        assert response.status_code == 302
        assert '/login' in response.location
