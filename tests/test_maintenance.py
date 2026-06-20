from datetime import date

from app.extensions import db
from app.models import Maintenance
from conftest import login_as


def test_repair_inspection_creates_planned_maintenance(client, app):
    login_as(client, "engineer")

    response = client.post(
        "/inspection/new",
        data={
            "equipment_id": "1",
            "inspected_at": "2026-06-20",
            "status": "repair",
            "note": "軸受けから異音を確認",
        },
    )

    assert response.status_code == 302
    with app.app_context():
        maintenance = db.session.query(Maintenance).one()
        assert maintenance.status == "planned"
        assert maintenance.source_inspection_id is not None
        assert maintenance.action == "点検で検出した不具合の修理対応"


def test_engineer_completes_maintenance_and_timeline_renders(client, app):
    login_as(client, "engineer")
    client.post(
        "/inspection/new",
        data={
            "equipment_id": "1",
            "inspected_at": "2026-06-10",
            "status": "repair",
            "note": "制御センサー異常",
        },
    )
    with app.app_context():
        maintenance_id = db.session.query(Maintenance.id).scalar()

    response = client.post(
        f"/maintenance/{maintenance_id}/edit",
        data={
            "equipment_id": "1",
            "source_inspection_id": "1",
            "status": "completed",
            "action": "制御センサー交換と校正",
            "started_at": "2026-06-11",
            "completed_at": "2026-06-12",
            "result": "交換後の試運転で正常値を確認",
            "note": "",
        },
    )

    assert response.status_code == 302
    with app.app_context():
        maintenance = db.session.get(Maintenance, maintenance_id)
        assert maintenance.status == "completed"
        assert maintenance.completed_at == date(2026, 6, 12)

    detail = client.get("/equipment/1")
    assert detail.status_code == 200
    assert "点検・修理タイムライン" in detail.text
    assert "修理対応が完了" in detail.text
    assert "交換後の試運転で正常値を確認" in detail.text
    assert detail.text.index("修理対応が完了") < detail.text.index("点検：要修理")


def test_engineer_cannot_edit_other_engineers_maintenance(client, app):
    with app.app_context():
        maintenance = Maintenance(
            equipment_id=2,
            engineer_id=4,
            status="planned",
            action="他担当者の修理",
        )
        db.session.add(maintenance)
        db.session.commit()
        maintenance_id = maintenance.id

    login_as(client, "engineer")
    response = client.get(f"/maintenance/{maintenance_id}/edit")

    assert response.status_code == 302
    assert response.location.endswith("/dashboard")


def test_completed_maintenance_requires_dates(client, app):
    login_as(client, "engineer")

    response = client.post(
        "/maintenance/new",
        data={
            "equipment_id": "1",
            "status": "completed",
            "action": "部品交換",
            "started_at": "",
            "completed_at": "",
        },
    )

    assert response.status_code == 200
    assert "着手日を入力してください" in response.text
    with app.app_context():
        assert db.session.query(Maintenance).count() == 0
