"""
tests/conftest.py

pytest 共通フィクスチャ。
CSRF を無効化した Flask テストクライアントと、
ロール別ログインヘルパーを提供する。
"""

import pytest
from app import app as flask_app


@pytest.fixture
def app():
    """テスト用 Flask アプリを返す。CSRF と TESTING を設定する。"""
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    yield flask_app


@pytest.fixture
def client(app):
    """テスト用 HTTP クライアントを返す。"""
    return app.test_client()


def login_as(client, role, user_id=1):
    """
    テスト用セッションにログインユーザーをセットするヘルパー。

    使い方:
        login_as(client, 'root')
        login_as(client, 'admin', user_id=20)
    """
    with client.session_transaction() as sess:
        sess['user'] = {
            'id':         user_id,
            'last_name':  'テスト',
            'first_name': role,
            'role':       role,
        }
