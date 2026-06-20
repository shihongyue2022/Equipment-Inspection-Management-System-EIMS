from app.extensions import db
from app.models import Equipment
from conftest import login_as


def equipment_form(**overrides):
    values = {
        "name": "研究棟空調機",
        "location": "架空研究棟1F",
        "equipment_type": "空調機",
        "manufacturer": "北辰空調工業",
        "model_number": "HC-100",
        "installed_at": "2024-01-01",
        "inspection_interval_months": "3",
        "assigned_user_id": "3",
    }
    values.update(overrides)
    return values


def test_admin_can_list_and_create_equipment(client, app):
    login_as(client, "admin")
    assert client.get("/equipment").status_code == 200
    response = client.post("/equipment/new", data=equipment_form())
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Equipment, 3).name == "研究棟空調機"


def test_engineer_cannot_open_admin_equipment_list(client):
    login_as(client, "engineer")
    response = client.get("/equipment")
    assert response.status_code == 302
    assert response.location.endswith("/dashboard")


def test_engineer_can_only_open_assigned_equipment(client):
    login_as(client, "engineer")
    assert client.get("/equipment/1").status_code == 200
    response = client.get("/equipment/2")
    assert response.status_code == 302
    assert response.location.endswith("/dashboard")


def test_admin_can_edit_equipment(client, app):
    login_as(client, "admin")
    response = client.post(
        "/equipment/1/edit", data=equipment_form(name="更新済み設備")
    )
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Equipment, 1).name == "更新済み設備"
