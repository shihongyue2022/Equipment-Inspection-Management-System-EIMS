from datetime import date

from app.extensions import db
from app.models import Equipment, Inspection
from conftest import login_as


def test_engineer_registers_inspection_atomically(client, app):
    login_as(client, "engineer")
    response = client.post(
        "/inspection/new",
        data={
            "equipment_id": "1",
            "inspected_at": "2026-06-20",
            "status": "normal",
            "note": "異常なし",
        },
    )
    assert response.status_code == 302
    with app.app_context():
        assert db.session.query(Inspection).count() == 1
        assert db.session.get(Equipment, 1).next_inspection_date == date(2026, 9, 20)


def test_engineer_cannot_inspect_unassigned_equipment(client, app):
    login_as(client, "engineer")
    response = client.post(
        "/inspection/new",
        data={
            "equipment_id": "2",
            "inspected_at": "2026-06-20",
            "status": "normal",
        },
    )
    assert response.status_code == 302
    with app.app_context():
        assert db.session.query(Inspection).count() == 0
