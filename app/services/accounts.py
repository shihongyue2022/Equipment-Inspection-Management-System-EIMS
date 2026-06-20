from sqlalchemy import func, or_, select, update
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Equipment, Inspection, User


REQUIRED_NEW = ("employee_no", "last_name", "first_name", "email", "password", "role")
REQUIRED_EDIT = ("employee_no", "last_name", "first_name", "email", "role")

MANAGEMENT_SORT_OPTIONS = {
    "name": "氏名",
    "employee_no": "社員番号",
    "created": "登録日",
}

ROLE_LABELS = {"root": "ROOT", "admin": "管理者", "engineer": "FE"}


def users():
    return db.session.scalars(select(User).order_by(User.id)).all()


def bases():
    return db.session.scalars(
        select(User.base).where(User.base.is_not(None)).distinct().order_by(User.base)
    ).all()


def _apply_user_filters(statement, *, keyword=None, role=None, base=None, exclude=None):
    if keyword:
        pattern = f"%{keyword}%"
        statement = statement.where(
            or_(
                User.employee_no.ilike(pattern),
                User.last_name.ilike(pattern),
                User.first_name.ilike(pattern),
                User.email.ilike(pattern),
            )
        )
    if role and exclude != "role":
        statement = statement.where(User.role == role)
    if base and exclude != "base":
        statement = statement.where(User.base == base)
    return statement


def account_management_filter_options(*, keyword=None, role=None, base=None):
    def counted(column, *, exclude):
        statement = _apply_user_filters(
            select(column.label("value"), func.count(User.id).label("count")),
            keyword=keyword,
            role=role,
            base=base,
            exclude=exclude,
        )
        statement = (
            statement.where(column.is_not(None))
            .group_by(column)
            .order_by(column)
        )
        return [
            {"value": row.value, "count": int(row.count)}
            for row in db.session.execute(statement)
        ]

    roles = counted(User.role, exclude="role")
    for option in roles:
        option["label"] = ROLE_LABELS.get(option["value"], option["value"])
    return {"roles": roles, "bases": counted(User.base, exclude="base")}


def search_users(
    *,
    page=1,
    per_page=50,
    sort_by="name",
    sort_order="asc",
    keyword=None,
    role=None,
    base=None,
):
    statement = _apply_user_filters(
        select(User), keyword=keyword, role=role, base=base
    )
    if sort_by == "employee_no":
        order_columns = (User.employee_no, User.id)
    elif sort_by == "created":
        order_columns = (User.created_at, User.id)
    else:
        order_columns = (User.last_name, User.first_name, User.id)
    if sort_order == "desc":
        order_columns = tuple(column.desc() for column in order_columns)
    statement = statement.order_by(*order_columns)
    return db.paginate(
        statement,
        page=max(page, 1),
        per_page=per_page,
        max_per_page=100,
        error_out=False,
    )


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

