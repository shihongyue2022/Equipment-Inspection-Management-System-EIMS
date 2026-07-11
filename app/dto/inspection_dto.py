class InspectionDto:
    """inspection_recordsテーブルの1行を表すDTO。"""

    def __init__(self):
        self._id = None
        self._equipment_id = None
        self._engineer_id = None
        self._inspected_at = None
        self._expected_inspection_date = None
        self._status = None
        self._note = None
        self._created_at = None
        # 画面表示用の補助プロパティ
        self._equipment_name = None
        self._engineer_name = None
        self._engineer_deleted = False
        self._deleted_at = None
        self._deleted_by_name = None

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def equipment_id(self):
        return self._equipment_id

    @equipment_id.setter
    def equipment_id(self, value):
        self._equipment_id = value

    @property
    def engineer_id(self):
        return self._engineer_id

    @engineer_id.setter
    def engineer_id(self, value):
        self._engineer_id = value

    @property
    def inspected_at(self):
        return self._inspected_at

    @inspected_at.setter
    def inspected_at(self, value):
        self._inspected_at = value

    @property
    def expected_inspection_date(self):
        """点検登録時点でのnext_inspection_date。期限遵守の履歴追跡用。"""
        return self._expected_inspection_date

    @expected_inspection_date.setter
    def expected_inspection_date(self, value):
        self._expected_inspection_date = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def note(self):
        return self._note

    @note.setter
    def note(self, value):
        self._note = value

    @property
    def created_at(self):
        return self._created_at

    @created_at.setter
    def created_at(self, value):
        self._created_at = value

    @property
    def equipment_name(self):
        """画面表示用の設備名。DAOでJOINして取得する。"""
        return self._equipment_name

    @equipment_name.setter
    def equipment_name(self, value):
        self._equipment_name = value

    @property
    def engineer_name(self):
        """画面表示用の点検者名。DAOでJOINして取得する。"""
        return self._engineer_name

    @engineer_name.setter
    def engineer_name(self, value):
        self._engineer_name = value

    @property
    def engineer_deleted(self):
        """点検者アカウントが論理削除済みかどうか。削除済みの場合はTrueになる。"""
        return self._engineer_deleted

    @engineer_deleted.setter
    def engineer_deleted(self, value):
        self._engineer_deleted = bool(value)

    @property
    def status_label(self):
        """ステータスコードを日本語ラベルに変換して返す。"""
        labels = {
            'normal': '正常',
            'watch':  '要観察',
            'repair': '要修理',
        }
        return labels.get(self._status, '不明')

    @property
    def deleted_at(self):
        """論理削除日時。ゴミ箱一覧でのみ使用する。"""
        return self._deleted_at

    @deleted_at.setter
    def deleted_at(self, value):
        self._deleted_at = value

    @property
    def deleted_by_name(self):
        """削除者の氏名。ゴミ箱一覧でのみ使用する。"""
        return self._deleted_by_name

    @deleted_by_name.setter
    def deleted_by_name(self, value):
        self._deleted_by_name = value
