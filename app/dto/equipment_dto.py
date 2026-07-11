class EquipmentDto:
    """equipmentテーブルの1行を表すDTO。"""

    def __init__(self):
        self._id = None
        self._name = None
        self._location = None
        self._equipment_type = None 
        self._manufacturer = None
        self._model_number = None
        self._installed_at = None
        self._inspection_interval_months = None
        self._assigned_user_id = None
        self._assigned_user_name = None
        self._area = None
        self._next_inspection_date = None
        self._deadline_status = None
        self._latest_inspection_status = None
        self._latest_inspection_date = None
        self._latest_inspection_note = None
        self._deleted_at = None
        self._deleted_by_name = None

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self._location = value

    @property
    def equipment_type(self):
        return self._equipment_type

    @equipment_type.setter
    def equipment_type(self, value):
        self._equipment_type = value

    @property
    def manufacturer(self):
        return self._manufacturer

    @manufacturer.setter
    def manufacturer(self, value):
        self._manufacturer = value

    @property
    def model_number(self):
        return self._model_number

    @model_number.setter
    def model_number(self, value):
        self._model_number = value

    @property
    def installed_at(self):
        return self._installed_at

    @installed_at.setter
    def installed_at(self, value):
        self._installed_at = value

    @property
    def inspection_interval_months(self):
        return self._inspection_interval_months

    @inspection_interval_months.setter
    def inspection_interval_months(self, value):
        self._inspection_interval_months = value

    @property
    def assigned_user_id(self):
        return self._assigned_user_id

    @assigned_user_id.setter
    def assigned_user_id(self, value):
        self._assigned_user_id = value

    @property
    def assigned_user_name(self):
        return self._assigned_user_name

    @assigned_user_name.setter
    def assigned_user_name(self, value):
        self._assigned_user_name = value

    @property
    def area(self):
        return self._area

    @area.setter
    def area(self, value):
        self._area = value

    @property
    def next_inspection_date(self):
        return self._next_inspection_date

    @next_inspection_date.setter
    def next_inspection_date(self, value):
        self._next_inspection_date = value

    @property
    def deadline_status(self):
        return self._deadline_status

    @deadline_status.setter
    def deadline_status(self, value):
        self._deadline_status = value

    @property
    def latest_inspection_status(self):
        return self._latest_inspection_status

    @latest_inspection_status.setter
    def latest_inspection_status(self, value):
        self._latest_inspection_status = value

    @property
    def latest_inspection_date(self):
        return self._latest_inspection_date

    @latest_inspection_date.setter
    def latest_inspection_date(self, value):
        self._latest_inspection_date = value

    @property
    def latest_inspection_note(self):
        return self._latest_inspection_note

    @latest_inspection_note.setter
    def latest_inspection_note(self, value):
        self._latest_inspection_note = value

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
