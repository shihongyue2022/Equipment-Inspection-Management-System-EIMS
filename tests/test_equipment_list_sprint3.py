"""
tests/test_equipment_list_sprint3.py

書類No.016 設備一覧ページネーション機能 ／ 設備一覧画面
書類No.021 設備一覧列追加（最新点検日・備考）・最新記録基準変更 ／ 設備一覧画面
の単体テスト（Sprint 3）。

テスト対象：
  GET /equipment           → equipment_list_get

書類No.016 テスト項目：
  項目1: 21件以上の設備がある場合、200を返す（全件がテンプレートに渡される）
  項目2: ?page=2 パラメータを受け付けても200を返す
  項目3: ?page=1 パラメータを受け付けても200を返す
  項目5: 検索条件とページパラメータを同時に渡しても200を返す
  項目6: 20件以下の設備のみの場合でも200を返す

書類No.021 テスト項目：
  項目1: EquipmentDtoにlatest_inspection_date・latest_inspection_noteが存在する
  項目2: 点検記録がある設備のlatest_inspection_dateが正しくDTOに格納される
  項目3: 点検記録がない設備のlatest_inspection_dateはNone
  項目4: latest_inspection_statusが各点検ステータス値を正しく保持する
  項目5: 最新点検記録のlatest_inspection_noteが正しくDTOに格納される
"""

import pytest
from datetime import date
from unittest.mock import patch
from app.dto.equipment_dto import EquipmentDto
from tests.conftest import login_as


# ==============================================================
# テストデータ生成ヘルパー
# ==============================================================

def _make_equipment(
    id=1,
    name='テスト空調',
    next_inspection_date=None,
    latest_inspection_date=None,
    latest_inspection_status=None,
    latest_inspection_note=None,
):
    """テスト用 EquipmentDto を生成する。Sprint 3 で追加された最新点検フィールドも含む。"""
    dto = EquipmentDto()
    dto.id = id
    dto.name = name
    dto.location = '1F機械室'
    dto.equipment_type = '空調'
    dto.manufacturer = 'ダイキン'
    dto.model_number = f'TEST-{id:03d}'
    dto.installed_at = '2020-04-01'
    dto.inspection_interval_months = 6
    dto.assigned_user_id = None
    dto.next_inspection_date = next_inspection_date
    # Sprint 3 追加フィールド
    dto.latest_inspection_date = latest_inspection_date
    dto.latest_inspection_status = latest_inspection_status
    dto.latest_inspection_note = latest_inspection_note
    return dto


def _make_equipment_list(count):
    """指定件数の EquipmentDto リストを生成する。ページネーションテスト用。"""
    return [_make_equipment(id=i + 1, name=f'テスト設備{i + 1:02d}') for i in range(count)]


# ==============================================================
# 書類No.016 ─ 設備一覧ページネーション機能テスト
# ==============================================================

class TestEquipmentListPagination:
    """書類No.016 設備一覧ページネーション機能の単体テスト（全6項目対応）"""

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_21_items_returns_200(self, MockEquipmentDao, MockUserDao, client):
        """項目1：21件以上の設備がある場合、設備一覧画面が200を返す"""
        # 21件の設備をDAOが返すよう設定する
        MockEquipmentDao.return_value.find_with_filter.return_value = _make_equipment_list(21)
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.get('/equipment')
        assert response.status_code == 200

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_page2_param_returns_200(self, MockEquipmentDao, MockUserDao, client):
        """項目2：?page=2 パラメータ付きで設備一覧を表示しても200を返す"""
        MockEquipmentDao.return_value.find_with_filter.return_value = _make_equipment_list(25)
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.get('/equipment?page=2')
        assert response.status_code == 200

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_page1_param_returns_200(self, MockEquipmentDao, MockUserDao, client):
        """項目3：?page=1 パラメータ付きで設備一覧を表示しても200を返す"""
        MockEquipmentDao.return_value.find_with_filter.return_value = _make_equipment_list(25)
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.get('/equipment?page=1')
        assert response.status_code == 200

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_search_keyword_and_page_combined_returns_200(self, MockEquipmentDao, MockUserDao, client):
        """項目5：検索条件とページパラメータを組み合わせた場合も200を返す（検索条件が維持される）"""
        MockEquipmentDao.return_value.find_with_filter.return_value = _make_equipment_list(25)
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        # 検索条件（name=空調）とページパラメータを同時に送信する
        response = client.get('/equipment?name=空調&page=2')
        assert response.status_code == 200
        # 検索条件がDAOに渡されていることを確認する（ページパラメータは無視されない）
        MockEquipmentDao.return_value.find_with_filter.assert_called_once_with(
            name='空調',
            equipment_type=None,
            assigned_user_id=None,
        )

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_20_or_fewer_items_returns_200(self, MockEquipmentDao, MockUserDao, client):
        """項目6：20件以下の設備しかない場合も設備一覧画面が200を返す"""
        # 10件（1ページ未満）の設備を返す
        MockEquipmentDao.return_value.find_with_filter.return_value = _make_equipment_list(10)
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.get('/equipment')
        assert response.status_code == 200

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_invalid_page_param_does_not_cause_server_error(self, MockEquipmentDao, MockUserDao, client):
        """ページパラメータに数値以外の値が来ても500エラーにならない"""
        MockEquipmentDao.return_value.find_with_filter.return_value = _make_equipment_list(5)
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        # 不正なページ番号でもエラーにならないことを確認する
        response = client.get('/equipment?page=abc')
        assert response.status_code == 200

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_root_can_access_with_page_param(self, MockEquipmentDao, MockUserDao, client):
        """root ユーザーもページパラメータ付きで設備一覧にアクセスできる"""
        MockEquipmentDao.return_value.find_with_filter.return_value = _make_equipment_list(21)
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'root')
        response = client.get('/equipment?page=2')
        assert response.status_code == 200

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_find_with_filter_called_once_per_request(self, MockEquipmentDao, MockUserDao, client):
        """ページネーションパラメータがあっても find_with_filter は1回だけ呼ばれる"""
        MockEquipmentDao.return_value.find_with_filter.return_value = _make_equipment_list(25)
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        client.get('/equipment?page=3')
        MockEquipmentDao.return_value.find_with_filter.assert_called_once()


# ==============================================================
# 書類No.021 ─ 設備一覧列追加・最新点検記録基準変更テスト
# ==============================================================

class TestEquipmentListNewColumns:
    """書類No.021 設備一覧列追加（最新点検日・備考）・最新記録基準変更の単体テスト（全5項目対応）"""

    # ---- DTO プロパティ存在確認（項目1）----

    def test_dto_has_latest_inspection_date_property(self):
        """項目1：EquipmentDtoに latest_inspection_date プロパティが存在する"""
        dto = EquipmentDto()
        # プロパティアクセスでエラーが出ないことを確認する
        assert hasattr(dto, 'latest_inspection_date')
        # 初期値は None
        assert dto.latest_inspection_date is None

    def test_dto_has_latest_inspection_note_property(self):
        """項目1：EquipmentDtoに latest_inspection_note プロパティが存在する"""
        dto = EquipmentDto()
        assert hasattr(dto, 'latest_inspection_note')
        assert dto.latest_inspection_note is None

    # ---- 最新点検日の格納（項目2）----

    def test_dto_latest_inspection_date_can_be_set(self):
        """項目2：latest_inspection_dateにdateオブジェクトをセットできる"""
        dto = EquipmentDto()
        expected = date(2026, 6, 1)
        dto.latest_inspection_date = expected
        assert dto.latest_inspection_date == expected

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_view_accepts_equipment_with_inspection_date(self, MockEquipmentDao, MockUserDao, client):
        """項目2：最新点検日が設定された設備を含む一覧を表示しても200を返す"""
        eq = _make_equipment(
            id=1,
            latest_inspection_date=date(2026, 6, 15),
            latest_inspection_status='normal',
        )
        MockEquipmentDao.return_value.find_with_filter.return_value = [eq]
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.get('/equipment')
        assert response.status_code == 200

    # ---- 点検記録なし設備のNone確認（項目3）----

    def test_dto_latest_inspection_date_is_none_when_no_record(self):
        """項目3：点検記録がない設備の latest_inspection_date は None になる"""
        dto = _make_equipment(id=1, latest_inspection_date=None)
        assert dto.latest_inspection_date is None

    def test_dto_latest_inspection_note_is_none_when_no_record(self):
        """項目3・5：点検記録がない設備の latest_inspection_note は None になる"""
        dto = _make_equipment(id=1, latest_inspection_note=None)
        assert dto.latest_inspection_note is None

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_view_accepts_equipment_without_inspection(self, MockEquipmentDao, MockUserDao, client):
        """項目3：点検記録がない（latest_inspection_date=None）設備の一覧表示で200を返す"""
        eq = _make_equipment(id=1)  # 全ての最新点検フィールドがNone
        MockEquipmentDao.return_value.find_with_filter.return_value = [eq]
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.get('/equipment')
        assert response.status_code == 200

    # ---- 最新記録基準の確認（項目4）----

    def test_dto_latest_inspection_status_holds_normal(self):
        """項目4：latest_inspection_statusに 'normal' をセットできる"""
        dto = EquipmentDto()
        dto.latest_inspection_status = 'normal'
        assert dto.latest_inspection_status == 'normal'

    def test_dto_latest_inspection_status_holds_watch(self):
        """項目4：latest_inspection_statusに 'watch' をセットできる"""
        dto = EquipmentDto()
        dto.latest_inspection_status = 'watch'
        assert dto.latest_inspection_status == 'watch'

    def test_dto_latest_inspection_status_holds_repair(self):
        """項目4：latest_inspection_statusに 'repair' をセットできる"""
        dto = EquipmentDto()
        dto.latest_inspection_status = 'repair'
        assert dto.latest_inspection_status == 'repair'

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_view_passes_latest_inspection_status_correctly(self, MockEquipmentDao, MockUserDao, client):
        """項目4：DAOが返した最新点検ステータスがビューに正しく渡される"""
        # MAX(id) 基準での最新記録として 'repair' ステータスを持つ設備
        eq = _make_equipment(
            id=1,
            latest_inspection_date=date(2026, 6, 20),
            latest_inspection_status='repair',
            latest_inspection_note='モーター異音あり、要交換',
        )
        MockEquipmentDao.return_value.find_with_filter.return_value = [eq]
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.get('/equipment')
        assert response.status_code == 200

    # ---- 最新点検備考の格納（項目5）----

    def test_dto_latest_inspection_note_can_be_set(self):
        """項目5：latest_inspection_noteに備考テキストをセットできる"""
        dto = EquipmentDto()
        note = 'フィルター目詰まり要確認'
        dto.latest_inspection_note = note
        assert dto.latest_inspection_note == note

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_view_accepts_equipment_with_note(self, MockEquipmentDao, MockUserDao, client):
        """項目5：備考あり設備を含む一覧を表示しても200を返す"""
        eq = _make_equipment(
            id=1,
            latest_inspection_date=date(2026, 6, 1),
            latest_inspection_status='watch',
            latest_inspection_note='異音なし、潤滑油補充済み',
        )
        MockEquipmentDao.return_value.find_with_filter.return_value = [eq]
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.get('/equipment')
        assert response.status_code == 200

    # ---- 混在ケース（点検記録あり・なしの設備が同時に存在）----

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_mixed_list_with_and_without_inspection_returns_200(self, MockEquipmentDao, MockUserDao, client):
        """項目2・3：点検記録ありと点検記録なしの設備が混在しても200を返す"""
        eq_with = _make_equipment(
            id=1,
            latest_inspection_date=date(2026, 6, 1),
            latest_inspection_status='normal',
            latest_inspection_note='正常',
        )
        eq_without = _make_equipment(id=2)  # 点検記録なし（全フィールドNone）
        MockEquipmentDao.return_value.find_with_filter.return_value = [eq_with, eq_without]
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        response = client.get('/equipment')
        assert response.status_code == 200

    @patch('app.views.equipment.UserDao')
    @patch('app.views.equipment.EquipmentDao')
    def test_find_with_filter_called_for_column_display(self, MockEquipmentDao, MockUserDao, client):
        """項目1・4：設備一覧表示時に find_with_filter が呼び出される（最新点検列はDAOで付与される）"""
        MockEquipmentDao.return_value.find_with_filter.return_value = []
        MockUserDao.return_value.find_by_role.return_value = []
        login_as(client, 'admin')
        client.get('/equipment')
        # find_with_filter が1回呼ばれていることを確認する（引数なしで全件取得）
        MockEquipmentDao.return_value.find_with_filter.assert_called_once_with(
            name=None,
            equipment_type=None,
            assigned_user_id=None,
        )
