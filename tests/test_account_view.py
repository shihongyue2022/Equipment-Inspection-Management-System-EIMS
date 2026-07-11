"""
tests/test_account_view.py

アカウント管理機能（/accounts/*）のビューテスト。

テストの観点：3種ロールの支配関係
  root  > admin > engineer
  - root  : 全アカウントの参照・編集・削除、全ロール付与（root 付与除く）
  - admin : engineer のみ参照・編集・削除、engineer ロールのみ付与
  - engineer : /accounts/* へのアクセス不可

実装がどう変わっても本テストを実行することで権限設計を確認できる。
"""

import pytest
from unittest.mock import patch
from app.dto.user_dto import UserDto
from tests.conftest import login_as


# ==============================================================
# テストデータ生成ヘルパー
# ==============================================================

def _make_user(id=1, employee_no='ENG-001', last_name='山田', first_name='太郎',
               email='yamada@example.com', password='hashed_pw', role='engineer',
               phone=None, base=None):
    """テスト用 UserDto を生成する。"""
    dto = UserDto()
    dto.id          = id
    dto.employee_no = employee_no
    dto.last_name   = last_name
    dto.first_name  = first_name
    dto.email       = email
    dto.password    = password
    dto.role        = role
    dto.phone       = phone
    dto.base        = base
    return dto


# テスト全体で使い回す不変ユーザー定数
_ENGINEER = _make_user(
    id=10, role='engineer', employee_no='ENG-010', email='eng@example.com',
    last_name='田中', first_name='一郎',
)
_ADMIN = _make_user(
    id=20, role='admin', employee_no='ADM-020', email='adm@example.com',
    last_name='佐藤', first_name='管理',
)
_ROOT = _make_user(
    id=30, role='root', employee_no='ROOT-030', email='root@example.com',
    last_name='鈴木', first_name='最上位',
)


# ==============================================================
# 1. アカウント一覧  GET /accounts
# ==============================================================

class TestAccountListGet:
    """GET /accounts のアクセス制御テスト"""

    @patch('app.views.account_view.UserDao')
    def test_root_can_access(self, MockUserDao, client):
        """root はアカウント一覧にアクセスできる"""
        MockUserDao.return_value.find_all.return_value = []
        login_as(client, 'root')
        response = client.get('/accounts')
        assert response.status_code == 200

    @patch('app.views.account_view.UserDao')
    def test_admin_can_access(self, MockUserDao, client):
        """admin はアカウント一覧にアクセスできる"""
        MockUserDao.return_value.find_all.return_value = []
        login_as(client, 'admin')
        response = client.get('/accounts')
        assert response.status_code == 200

    def test_engineer_is_redirected(self, client):
        """engineer はアクセスできずダッシュボードへリダイレクトされる"""
        login_as(client, 'engineer')
        response = client.get('/accounts')
        assert response.status_code == 302
        assert '/dashboard' in response.location

    def test_unauthenticated_is_redirected(self, client):
        """未ログインは before_request フックにより /login へリダイレクトされる"""
        response = client.get('/accounts')
        assert response.status_code == 302
        assert '/login' in response.location


# ==============================================================
# 2. アカウント登録画面  GET /accounts/new
# ==============================================================

class TestAccountNewGet:
    """GET /accounts/new のアクセス制御テスト"""

    def test_root_can_access(self, client):
        """root はアカウント登録画面にアクセスできる"""
        login_as(client, 'root')
        response = client.get('/accounts/new')
        assert response.status_code == 200

    def test_admin_can_access(self, client):
        """admin はアカウント登録画面にアクセスできる"""
        login_as(client, 'admin')
        response = client.get('/accounts/new')
        assert response.status_code == 200

    def test_engineer_is_redirected(self, client):
        """engineer はアクセスできずダッシュボードへリダイレクトされる"""
        login_as(client, 'engineer')
        response = client.get('/accounts/new')
        assert response.status_code == 302
        assert '/dashboard' in response.location


# ==============================================================
# 3. アカウント登録処理  POST /accounts/new
#    ─ ロール付与の権限制御を重点的にテスト
# ==============================================================

class TestAccountNewPost:
    """POST /accounts/new のロール付与制限テスト"""

    # 有効な登録フォームの基本値
    _BASE_FORM = {
        'employee_no': 'ENG-099',
        'last_name':   '新規',
        'first_name':  'ユーザー',
        'email':       'newuser@example.com',
        'password':    'password123',
        'phone':       '',
        'base':        '',
    }

    def _post(self, client, role):
        """role を指定して POST するヘルパー。"""
        return client.post('/accounts/new', data={**self._BASE_FORM, 'role': role})

    # ---- root の権限 ----------------------------------------

    @patch('app.views.account_view.UserDao')
    def test_root_can_create_engineer(self, MockUserDao, client):
        """root は engineer ロールでアカウントを新規作成できる"""
        MockUserDao.return_value.find_by_employee_no.return_value = None
        MockUserDao.return_value.find_by_email.return_value = None
        login_as(client, 'root')
        response = self._post(client, 'engineer')
        assert response.status_code == 302
        assert '/accounts' in response.location

    @patch('app.views.account_view.UserDao')
    def test_root_can_create_admin(self, MockUserDao, client):
        """root は admin ロールでアカウントを新規作成できる"""
        MockUserDao.return_value.find_by_employee_no.return_value = None
        MockUserDao.return_value.find_by_email.return_value = None
        login_as(client, 'root')
        response = self._post(client, 'admin')
        assert response.status_code == 302
        assert '/accounts' in response.location

    # ---- admin の権限 ----------------------------------------

    @patch('app.views.account_view.UserDao')
    def test_admin_can_create_engineer(self, MockUserDao, client):
        """admin は engineer ロールでアカウントを新規作成できる"""
        MockUserDao.return_value.find_by_employee_no.return_value = None
        MockUserDao.return_value.find_by_email.return_value = None
        login_as(client, 'admin')
        response = self._post(client, 'engineer')
        assert response.status_code == 302
        assert '/accounts' in response.location

    def test_admin_cannot_create_admin(self, client):
        """admin は admin ロールのアカウントを作成できない（エラー表示）"""
        login_as(client, 'admin')
        response = self._post(client, 'admin')
        assert response.status_code == 200
        assert 'このロールは指定できません' in response.data.decode('utf-8')

    def test_admin_cannot_create_root(self, client):
        """admin は root ロールのアカウントを作成できない（エラー表示）"""
        login_as(client, 'admin')
        response = self._post(client, 'root')
        assert response.status_code == 200
        assert 'このロールは指定できません' in response.data.decode('utf-8')

    def test_root_cannot_create_root_account(self, client):
        """root であっても UI から root ロールのアカウントを新規作成できない"""
        login_as(client, 'root')
        response = self._post(client, 'root')
        assert response.status_code == 200
        assert 'このロールは指定できません' in response.data.decode('utf-8')

    # ---- engineer のアクセス制御 ----------------------------

    def test_engineer_is_redirected(self, client):
        """engineer はアカウント登録を実行できない"""
        login_as(client, 'engineer')
        response = self._post(client, 'engineer')
        assert response.status_code == 302
        assert '/dashboard' in response.location

    # ---- バリデーション -------------------------------------

    def test_missing_required_fields_shows_error(self, client):
        """必須項目が空の場合はエラーメッセージが表示される"""
        login_as(client, 'admin')
        response = client.post('/accounts/new', data={
            'employee_no': '',
            'last_name':   '',
            'first_name':  '',
            'email':       '',
            'password':    '',
            'role':        'engineer',
        })
        assert response.status_code == 200
        assert '必須項目' in response.data.decode('utf-8')

    @patch('app.views.account_view.UserDao')
    def test_duplicate_employee_no_shows_error(self, MockUserDao, client):
        """既存の社員番号で登録しようとするとエラーになる"""
        # 同じ社員番号のユーザーが存在することをモックで再現する
        MockUserDao.return_value.find_by_employee_no.return_value = _ENGINEER
        login_as(client, 'admin')
        response = self._post(client, 'engineer')
        assert response.status_code == 200
        assert '社員番号は既に使用されています' in response.data.decode('utf-8')

    @patch('app.views.account_view.UserDao')
    def test_duplicate_email_shows_error(self, MockUserDao, client):
        """既存のメールアドレスで登録しようとするとエラーになる"""
        MockUserDao.return_value.find_by_employee_no.return_value = None
        MockUserDao.return_value.find_by_email.return_value = _ENGINEER
        login_as(client, 'admin')
        response = self._post(client, 'engineer')
        assert response.status_code == 200
        assert 'メールアドレスは既に使用されています' in response.data.decode('utf-8')


# ==============================================================
# 4. アカウント詳細画面  GET /accounts/<id>
# ==============================================================

class TestAccountDetailGet:
    """GET /accounts/<id> のアクセス制御テスト"""

    @patch('app.views.account_view.EquipmentDao')
    @patch('app.views.account_view.UserDao')
    def test_root_can_view_any_account(self, MockUserDao, MockEquipmentDao, client):
        """root はどのロールのアカウント詳細も表示できる"""
        MockUserDao.return_value.find_by_id.return_value = _ENGINEER
        MockEquipmentDao.return_value.find_by_user_id.return_value = []
        login_as(client, 'root')
        response = client.get('/accounts/10')
        assert response.status_code == 200

    @patch('app.views.account_view.EquipmentDao')
    @patch('app.views.account_view.UserDao')
    def test_admin_can_view_engineer(self, MockUserDao, MockEquipmentDao, client):
        """admin は engineer アカウントの詳細を表示できる"""
        MockUserDao.return_value.find_by_id.return_value = _ENGINEER
        MockEquipmentDao.return_value.find_by_user_id.return_value = []
        login_as(client, 'admin')
        response = client.get('/accounts/10')
        assert response.status_code == 200

    def test_engineer_is_redirected(self, client):
        """engineer はアカウント詳細にアクセスできない"""
        login_as(client, 'engineer')
        response = client.get('/accounts/10')
        assert response.status_code == 302
        assert '/dashboard' in response.location


# ==============================================================
# 5. アカウント編集処理  POST /accounts/<id>
#    ─ 編集可否とロール変更権限を重点的にテスト
# ==============================================================

class TestAccountDetailPost:
    """POST /accounts/<id> の権限制御テスト"""

    def _post_edit(self, client, target_id, overrides=None):
        """engineer 向けデフォルトフォームで POST する共通ヘルパー。"""
        form = {
            'employee_no': 'ENG-010',
            'last_name':   '田中',
            'first_name':  '一郎',
            'email':       'eng@example.com',
            'role':        'engineer',
            'phone':       '',
            'base':        '',
        }
        if overrides:
            form.update(overrides)
        return client.post(f'/accounts/{target_id}', data=form)

    # ---- root の権限 ----------------------------------------

    @patch('app.views.account_view.EquipmentDao')
    @patch('app.views.account_view.UserDao')
    def test_root_can_assign_admin_role_to_engineer(self, MockUserDao, MockEquipmentDao, client):
        """root は engineer に admin ロールを付与できる"""
        dao_inst = MockUserDao.return_value
        dao_inst.find_by_id.return_value = _ENGINEER
        dao_inst.find_by_employee_no.return_value = None
        dao_inst.find_by_email.return_value = None
        MockEquipmentDao.return_value.find_by_user_id.return_value = []
        login_as(client, 'root')
        response = self._post_edit(client, 10, {'role': 'admin'})
        assert response.status_code == 302
        assert '/accounts' in response.location

    @patch('app.views.account_view.EquipmentDao')
    @patch('app.views.account_view.UserDao')
    def test_root_cannot_assign_root_role_to_others(self, MockUserDao, MockEquipmentDao, client):
        """root であっても他アカウントに root ロールを付与することはできない"""
        MockUserDao.return_value.find_by_id.return_value = _ENGINEER
        MockEquipmentDao.return_value.find_by_user_id.return_value = []
        login_as(client, 'root')
        response = self._post_edit(client, 10, {'role': 'root'})
        assert response.status_code == 200
        assert 'root権限を他のアカウントに付与することはできません' in response.data.decode('utf-8')

    # ---- admin の権限 ----------------------------------------

    @patch('app.views.account_view.EquipmentDao')
    @patch('app.views.account_view.UserDao')
    def test_admin_can_edit_engineer(self, MockUserDao, MockEquipmentDao, client):
        """admin は engineer アカウントを正常に編集できる"""
        dao_inst = MockUserDao.return_value
        dao_inst.find_by_id.return_value = _ENGINEER
        dao_inst.find_by_employee_no.return_value = None
        dao_inst.find_by_email.return_value = None
        MockEquipmentDao.return_value.find_by_user_id.return_value = []
        login_as(client, 'admin')
        response = self._post_edit(client, 10)
        assert response.status_code == 302
        assert '/accounts' in response.location

    @patch('app.views.account_view.EquipmentDao')
    @patch('app.views.account_view.UserDao')
    def test_admin_cannot_edit_admin_account(self, MockUserDao, MockEquipmentDao, client):
        """admin は admin アカウントを編集できない（エラー表示）"""
        MockUserDao.return_value.find_by_id.return_value = _ADMIN
        MockEquipmentDao.return_value.find_by_user_id.return_value = []
        login_as(client, 'admin')
        # ターゲットが admin なので、フォームの role に関わらずエラーになる
        response = self._post_edit(client, 20)
        assert response.status_code == 200
        assert 'このアカウントは編集できません' in response.data.decode('utf-8')

    @patch('app.views.account_view.EquipmentDao')
    @patch('app.views.account_view.UserDao')
    def test_admin_cannot_edit_root_account(self, MockUserDao, MockEquipmentDao, client):
        """admin は root アカウントを編集できない（エラー表示）"""
        MockUserDao.return_value.find_by_id.return_value = _ROOT
        MockEquipmentDao.return_value.find_by_user_id.return_value = []
        login_as(client, 'admin')
        response = self._post_edit(client, 30)
        assert response.status_code == 200
        assert 'このアカウントは編集できません' in response.data.decode('utf-8')

    @patch('app.views.account_view.EquipmentDao')
    @patch('app.views.account_view.UserDao')
    def test_admin_cannot_assign_admin_role_to_engineer(self, MockUserDao, MockEquipmentDao, client):
        """admin は engineer に admin ロールを付与できない（エラー表示）"""
        MockUserDao.return_value.find_by_id.return_value = _ENGINEER
        MockEquipmentDao.return_value.find_by_user_id.return_value = []
        login_as(client, 'admin')
        response = self._post_edit(client, 10, {'role': 'admin'})
        assert response.status_code == 200
        assert 'このロールは指定できません' in response.data.decode('utf-8')

    @patch('app.views.account_view.EquipmentDao')
    @patch('app.views.account_view.UserDao')
    def test_root_can_edit_own_account(self, MockUserDao, MockEquipmentDao, client):
        """root は自身のアカウント情報（社員番号・氏名・メール）を編集できる"""
        dao_inst = MockUserDao.return_value
        dao_inst.find_by_id.return_value = _ROOT
        dao_inst.find_by_employee_no.return_value = None
        dao_inst.find_by_email.return_value = None
        MockEquipmentDao.return_value.find_by_user_id.return_value = []
        login_as(client, 'root', user_id=30)
        response = self._post_edit(client, 30, {
            'employee_no': 'ROOT-030',
            'last_name':   '鈴木',
            'first_name':  '最上位',
            'email':       'root@example.com',
            'role':        'root',
        })
        assert response.status_code == 302
        assert '/accounts' in response.location

    # ---- engineer のアクセス制御 ----------------------------

    def test_engineer_cannot_edit_accounts(self, client):
        """engineer はアカウント編集を実行できない"""
        login_as(client, 'engineer')
        response = self._post_edit(client, 10)
        assert response.status_code == 302
        assert '/dashboard' in response.location


# ==============================================================
# 6. アカウント削除処理  POST /accounts/<id>/delete
# ==============================================================

class TestAccountDeletePost:
    """POST /accounts/<id>/delete の権限制御テスト"""

    @patch('app.views.account_view.UserDao')
    def test_root_can_delete_engineer(self, MockUserDao, client):
        """root は engineer アカウントを削除できる"""
        MockUserDao.return_value.find_by_id.return_value = _ENGINEER
        login_as(client, 'root')
        response = client.post('/accounts/10/delete')
        assert response.status_code == 302
        assert '/accounts' in response.location
        # 実装は delete(id, deleted_by_id) の2引数で呼ぶ。root の user_id は login_as デフォルト値 1
        MockUserDao.return_value.delete.assert_called_once_with(10, 1)

    @patch('app.views.account_view.UserDao')
    def test_root_can_delete_admin(self, MockUserDao, client):
        """root は admin アカウントを削除できる"""
        MockUserDao.return_value.find_by_id.return_value = _ADMIN
        login_as(client, 'root')
        response = client.post('/accounts/20/delete')
        assert response.status_code == 302
        assert '/accounts' in response.location
        MockUserDao.return_value.delete.assert_called_once_with(20, 1)

    @patch('app.views.account_view.UserDao')
    def test_admin_can_delete_engineer(self, MockUserDao, client):
        """admin は engineer アカウントを削除できる"""
        MockUserDao.return_value.find_by_id.return_value = _ENGINEER
        login_as(client, 'admin')
        response = client.post('/accounts/10/delete')
        assert response.status_code == 302
        assert '/accounts' in response.location
        MockUserDao.return_value.delete.assert_called_once_with(10, 1)

    @patch('app.views.account_view.UserDao')
    def test_can_delete_engineer_with_inspection_records(self, MockUserDao, client):
        """点検記録が存在する engineer も論理削除できる（No.046：件数チェック廃止）"""
        MockUserDao.return_value.find_by_id.return_value = _ENGINEER
        login_as(client, 'admin')
        response = client.post('/accounts/10/delete')
        # 点検記録件数にかかわらず削除（302リダイレクト）されることを確認する
        assert response.status_code == 302
        assert '/accounts' in response.location
        MockUserDao.return_value.delete.assert_called_once_with(10, 1)

    @patch('app.views.account_view.UserDao')
    def test_admin_cannot_delete_admin(self, MockUserDao, client):
        """admin は admin アカウントを削除できない（削除されずリダイレクト）"""
        MockUserDao.return_value.find_by_id.return_value = _ADMIN
        login_as(client, 'admin')
        response = client.post('/accounts/20/delete')
        assert response.status_code == 302
        assert '/accounts' in response.location
        # delete が呼ばれていないことを確認する
        MockUserDao.return_value.delete.assert_not_called()

    @patch('app.views.account_view.UserDao')
    def test_admin_cannot_delete_root(self, MockUserDao, client):
        """admin は root アカウントを削除できない（削除されずリダイレクト）"""
        MockUserDao.return_value.find_by_id.return_value = _ROOT
        login_as(client, 'admin')
        response = client.post('/accounts/30/delete')
        assert response.status_code == 302
        assert '/accounts' in response.location
        MockUserDao.return_value.delete.assert_not_called()

    @patch('app.views.account_view.UserDao')
    def test_cannot_delete_self(self, MockUserDao, client):
        """自分自身は削除できない（No.4：自己削除防止）"""
        # ログインユーザーと同じ id=1 のユーザーを返すようにモックする
        self_user = _make_user(id=1, role='root')
        MockUserDao.return_value.find_by_id.return_value = self_user
        login_as(client, 'root', user_id=1)
        response = client.post('/accounts/1/delete')
        # 302 リダイレクトで削除されないことを確認する
        assert response.status_code == 302
        assert '/accounts' in response.location
        # delete が呼ばれていないことを確認する
        MockUserDao.return_value.delete.assert_not_called()
        # エラーメッセージがセッションにセットされていることを確認する
        with client.session_transaction() as sess:
            flashes = sess.get('_flashes', [])
            assert ('danger', '自分のアカウントは削除できません。') in flashes

    def test_engineer_cannot_delete(self, client):
        """engineer はアカウントを削除できない"""
        login_as(client, 'engineer')
        response = client.post('/accounts/10/delete')
        assert response.status_code == 302
        assert '/dashboard' in response.location
