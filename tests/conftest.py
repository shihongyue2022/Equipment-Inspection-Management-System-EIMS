from datetime import date

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Equipment, Inspection, User


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )
    with application.app_context():
        db.create_all()
        root = User(
            id=1,
            employee_no="SYS-001",
            last_name="統括",
            first_name="管理者",
            email="root@example.test",
            password=generate_password_hash("root-password"),
            role="root",
        )
        admin = User(
            id=2,
            employee_no="ADM-101",
            last_name="運用",
            first_name="管理者",
            email="admin@example.test",
            password=generate_password_hash("admin-password"),
            role="admin",
        )
        engineer = User(
            id=3,
            employee_no="TEC-201",
            last_name="朝霧",
            first_name="湊",
            email="engineer@example.test",
            password=generate_password_hash("engineer-password"),
            role="engineer",
            base="東雲中央サービス拠点",
        )
        other = User(
            id=4,
            employee_no="TEC-202",
            last_name="月岡",
            first_name="澪",
            email="other@example.test",
            password=generate_password_hash("other-password"),
            role="engineer",
            base="水鏡西部サービス拠点",
        )
        equipment = Equipment(
            id=1,
            name="中央棟サーバー室冷房機",
            location="蒼葉テクノセンター 中央棟2F",
            equipment_type="空調機",
            manufacturer="北辰空調工業",
            model_number="HC-720A",
            installed_at=date(2020, 4, 1),
            inspection_interval_months=3,
            assigned_user=engineer,
            next_inspection_date=date(2026, 8, 1),
        )
        other_equipment = Equipment(
            id=2,
            name="地下搬入口換気ユニット",
            location="蒼葉テクノセンター 地下1F",
            equipment_type="換気設備",
            manufacturer="雲雀設備製作所",
            model_number="HV-32S",
            installed_at=date(2021, 5, 1),
            inspection_interval_months=6,
            assigned_user=other,
            next_inspection_date=date(2026, 12, 1),
        )
        db.session.add_all([root, admin, engineer, other, equipment, other_equipment])
        db.session.commit()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login_as(client, role, user_id=None):
    ids = {"root": 1, "admin": 2, "engineer": 3}
    with client.session_transaction() as flask_session:
        flask_session["user"] = {
            "id": user_id or ids[role],
            "last_name": "テスト",
            "first_name": "利用者",
            "name": "テスト利用者",
            "role": role,
        }


@pytest.fixture
def inspection_factory():
    def create(engineer_id=3, equipment_id=1):
        record = Inspection(
            equipment_id=equipment_id,
            engineer_id=engineer_id,
            inspected_at=date(2026, 6, 20),
            status="normal",
            note="テスト点検",
        )
        db.session.add(record)
        db.session.commit()
        return record

    return create

