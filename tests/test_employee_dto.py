"""
tests/test_employee_dto.py

B-07-01: UserDto の @property / @setter 動作確認テスト。

テスト対象：
  app.dto.user_dto.UserDto

テスト内容：
  - 全プロパティの getter / setter が正しく動作すること
  - full_name が last_name + first_name を結合して返すこと
  - 初期値がすべて None であること
"""

import pytest
from app.dto.user_dto import UserDto


class TestUserDtoInit:
    """UserDto の初期値テスト"""

    def test_initial_values_are_none(self):
        """インスタンス生成直後は全プロパティが None である"""
        dto = UserDto()
        assert dto.id is None
        assert dto.employee_no is None
        assert dto.last_name is None
        assert dto.first_name is None
        assert dto.email is None
        assert dto.password is None
        assert dto.role is None
        assert dto.phone is None
        assert dto.base is None
        assert dto.deleted_at is None
        assert dto.deleted_by_name is None


class TestUserDtoProperties:
    """UserDto の各 @property / @setter テスト"""

    def test_id_setter_and_getter(self):
        """id プロパティのセット・取得が正しく動作する"""
        dto = UserDto()
        dto.id = 10
        assert dto.id == 10

    def test_employee_no_setter_and_getter(self):
        """employee_no プロパティのセット・取得が正しく動作する"""
        dto = UserDto()
        dto.employee_no = 'ENG-021'
        assert dto.employee_no == 'ENG-021'

    def test_last_name_setter_and_getter(self):
        """last_name プロパティのセット・取得が正しく動作する"""
        dto = UserDto()
        dto.last_name = '山田'
        assert dto.last_name == '山田'

    def test_first_name_setter_and_getter(self):
        """first_name プロパティのセット・取得が正しく動作する"""
        dto = UserDto()
        dto.first_name = '太郎'
        assert dto.first_name == '太郎'

    def test_email_setter_and_getter(self):
        """email プロパティのセット・取得が正しく動作する"""
        dto = UserDto()
        dto.email = 'yamada@example.com'
        assert dto.email == 'yamada@example.com'

    def test_password_setter_and_getter(self):
        """password プロパティのセット・取得が正しく動作する"""
        dto = UserDto()
        dto.password = 'hashed_value'
        assert dto.password == 'hashed_value'

    def test_role_setter_and_getter(self):
        """role プロパティのセット・取得が正しく動作する"""
        dto = UserDto()
        dto.role = 'admin'
        assert dto.role == 'admin'

    def test_phone_setter_and_getter(self):
        """phone プロパティのセット・取得が正しく動作する"""
        dto = UserDto()
        dto.phone = '090-1234-5678'
        assert dto.phone == '090-1234-5678'

    def test_base_setter_and_getter(self):
        """base プロパティのセット・取得が正しく動作する"""
        dto = UserDto()
        dto.base = '東京'
        assert dto.base == '東京'

    def test_deleted_at_setter_and_getter(self):
        """deleted_at プロパティのセット・取得が正しく動作する"""
        from datetime import datetime
        dto = UserDto()
        dt = datetime(2026, 6, 1, 12, 0, 0)
        dto.deleted_at = dt
        assert dto.deleted_at == dt

    def test_deleted_by_name_setter_and_getter(self):
        """deleted_by_name プロパティのセット・取得が正しく動作する"""
        dto = UserDto()
        dto.deleted_by_name = '管理者 太郎'
        assert dto.deleted_by_name == '管理者 太郎'


class TestUserDtoFullName:
    """UserDto の full_name 計算プロパティテスト"""

    def test_full_name_combines_last_and_first_name(self):
        """full_name は last_name と first_name を結合した文字列を返す"""
        dto = UserDto()
        dto.last_name = '山田'
        dto.first_name = '太郎'
        assert dto.full_name == '山田太郎'

    def test_full_name_with_different_names(self):
        """full_name は別の氏名でも正しく結合される"""
        dto = UserDto()
        dto.last_name = '鈴木'
        dto.first_name = '花子'
        assert dto.full_name == '鈴木花子'
