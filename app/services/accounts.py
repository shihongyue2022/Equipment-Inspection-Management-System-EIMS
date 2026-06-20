from sqlalchemy import func, select, update
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Equipment, Inspection, User


REQUIRED_NEW = ("employee_no", "last_name", "first_name", "email", "password", "role")
REQUIRED_EDIT = ("employee_no", "last_name", "first_name", "email", "role")


def users():
    return db.session.scalars(select(User).order_by(User.id)).all()


def bases():
    return db.session.scalars(
        select(User.base).where(User.base.is_not(None)).distinct().order_by(User.base)
    ).all()


def parse_user(form, *, editing=False):
    required = REQUIRED_EDIT if editing else REQUIRED_NEW
    values = {field: form.get(field, "").strip() for field in required}
    if not all(values.values()):
        return None, "入力情報に誤りがあります。必須項目をすべて入力してください。"
    if "@" not in values["email"]:
        return None, "メールアドレスが正しくありません。"
    values["phone"] = form.get("phone", "").strip() or None
    values["base"] = form.get("base", "").strip() or None
    return values, None


def duplicate_error(values, *, exclude_id=None):
    employee = db.session.scalar(
        select(User).where(User.employee_no == values["employee_no"])
    )
    if employee and employee.id != exclude_id:
        return "この社員番号は既に使用されています。"
    email = db.session.scalar(select(User).where(User.email == values["email"]))
    if email and email.id != exclude_id:
        return "このメールアドレスは既に使用されています。"
    return None


def create_user(values):
    values = dict(values)
    values["password"] = generate_password_hash(values["password"])
    user = User(**values)
    db.session.add(user)
    db.session.commit()
    return user


def update_user(user, values):
    for field, value in values.items():
        setattr(user, field, value)
    db.session.commit()
    return user


def change_password(user, password):
    user.password = generate_password_hash(password)
    db.session.commit()


def inspection_count(user_id):
    return db.session.scalar(
        select(func.count(Inspection.id)).where(Inspection.engineer_id == user_id)
    )


def delete_user(user):
    db.session.execute(
        update(Equipment)
        .where(Equipment.assigned_user_id == user.id)
        .values(assigned_user_id=None)
    )
    db.session.delete(user)
    db.session.commit()

