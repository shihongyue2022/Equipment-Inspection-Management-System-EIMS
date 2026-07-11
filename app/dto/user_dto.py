class UserDto:
    """Employeeテーブルの1行を表すDTO。"""

    def __init__(self):
        self._id = None
        self._employee_no = None
        self._last_name = None
        self._first_name = None
        self._email = None
        self._password = None
        self._role = None
        self._phone = None
        self._base = None
        self._deleted_at = None
        self._deleted_by_name = None

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def employee_no(self):
        return self._employee_no

    @employee_no.setter
    def employee_no(self, value):
        self._employee_no = value

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, value):
        self._last_name = value

    @property
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, value):
        self._first_name = value

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        self._email = value

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._password = value

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, value):
        self._role = value

    @property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, value):
        self._phone = value

    @property
    def base(self):
        return self._base

    @base.setter
    def base(self, value):
        self._base = value

    @property
    def full_name(self):
        """画面表示用の氏名（苗字＋名前）を返す。"""
        return f"{self._last_name}{self._first_name}"

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
