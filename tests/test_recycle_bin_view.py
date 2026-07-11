"""
tests/test_recycle_bin_view.py

ゴミ箱機能（/recycle-bin/*）のビューテスト。

テストの観点：
  - アカウント復元時は担当設備の割り当てを常に自動復元する（No.047）
  - restore_equipment=True がビューからDAOへ固定で渡されることを確認する
  - 一括復元も同じ挙動であることを確認する
"""

import pytest
from unittest.mock import patch
from tests.conftest import login_as


# ==============================================================
# 1. アカウント単体復元  POST /recycle-bin/user/<id>/restore
# ==============================================================

class TestRecycleBinUserRestorePost:
    """POST /recycle-bin/user/<id>/restore の復元テスト"""

    @patch('app.views.recycle_bin_view.UserDao')
    def test_restore_always_restores_equipment(self, MockUserDao, client):
        """復元時は restore_equipment=True を固定で渡す（No.047）"""
        MockUserDao.return_value.restore.return_value = 1
        login_as(client, 'admin')
        response = client.post('/recycle-bin/user/10/restore')
        assert response.status_code == 302
        # restore_equipment=True が固定で渡されることを確認する
        MockUserDao.return_value.restore.assert_called_once_with(10, 1, restore_equipment=True)

    @patch('app.views.recycle_bin_view.UserDao')
    def test_restore_not_found_redirects(self, MockUserDao, client):
        """復元対象が見つからない場合もリダイレクトする"""
        MockUserDao.return_value.restore.return_value = 0
        login_as(client, 'admin')
        response = client.post('/recycle-bin/user/99/restore')
        assert response.status_code == 302

    @patch('app.views.recycle_bin_view.UserDao')
    def test_engineer_cannot_restore(self, MockUserDao, client):
        """engineer はゴミ箱にアクセスできない"""
        login_as(client, 'engineer')
        response = client.post('/recycle-bin/user/10/restore')
        assert response.status_code == 302
        assert '/dashboard' in response.location
        MockUserDao.return_value.restore.assert_not_called()


# ==============================================================
# 2. アカウント一括復元  POST /recycle-bin/user/bulk-restore
# ==============================================================

class TestRecycleBinUserBulkRestorePost:
    """POST /recycle-bin/user/bulk-restore の一括復元テスト"""

    @patch('app.views.recycle_bin_view.UserDao')
    def test_bulk_restore_always_restores_equipment(self, MockUserDao, client):
        """一括復元時も restore_equipment=True を固定で渡す（No.047）"""
        MockUserDao.return_value.bulk_restore.return_value = 2
        login_as(client, 'admin')
        response = client.post('/recycle-bin/user/bulk-restore', data={
            'user_ids': '10,20',
        })
        assert response.status_code == 302
        MockUserDao.return_value.bulk_restore.assert_called_once_with(
            [10, 20], 1, restore_equipment=True
        )

    @patch('app.views.recycle_bin_view.UserDao')
    def test_bulk_restore_empty_ids_redirects(self, MockUserDao, client):
        """IDが空の場合はbulk_restoreを呼ばずリダイレクトする"""
        login_as(client, 'admin')
        response = client.post('/recycle-bin/user/bulk-restore', data={
            'user_ids': '',
        })
        assert response.status_code == 302
        MockUserDao.return_value.bulk_restore.assert_not_called()
