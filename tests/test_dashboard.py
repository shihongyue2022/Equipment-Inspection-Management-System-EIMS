from datetime import date, timedelta

from conftest import login_as

from app.extensions import db
from app.models import Equipment, Inspection
from app.services.dashboard import dashboard_summary, grouped_equipment_summary


def test_dashboard_summary_uses_latest_inspection_and_deadlines(app):
    today = date.today()
    with app.app_context():
        first = db.session.get(Equipment, 1)
        second = db.session.get(Equipment, 2)
        first.next_inspection_date = today - timedelta(days=1)
        second.next_inspection_date = today + timedelta(days=7)
        db.session.add_all(
            [
                Inspection(
                    equipment_id=1,
                    engineer_id=3,
                    inspected_at=today - timedelta(days=2),
                    status="repair",
                ),
                Inspection(
                    equipment_id=1,
                    engineer_id=3,
                    inspected_at=today - timedelta(days=1),
                    status="normal",
                ),
                Inspection(
                    equipment_id=2,
                    engineer_id=4,
                    inspected_at=today,
                    status="repair",
                ),
            ]
        )
        db.session.commit()

        assert dashboard_summary() == {
            "total_count": 2,
            "overdue_count": 1,
            "soon_count": 1,
            "repair_count": 1,
        }
        grouped = {
            row["group_name"]: row for row in grouped_equipment_summary("status")
        }
        assert grouped["正常"]["total_count"] == 1
        assert grouped["要修理"]["total_count"] == 1
        assert grouped["要修理"]["repair_count"] == 1


def test_dashboard_grouping_respects_user_scope(app):
    with app.app_context():
        db.session.get(Equipment, 1).next_inspection_date = date.today() + timedelta(
            days=30
        )
        db.session.commit()
        assert dashboard_summary(user_id=3)["total_count"] == 1
        rows = grouped_equipment_summary("base", user_id=3)
        assert rows == [
            {
                "group_name": "東雲中央サービス拠点",
                "total_count": 1,
                "overdue_count": 0,
                "soon_count": 0,
                "repair_count": 0,
            }
        ]


def test_dashboard_rejects_unknown_group_and_renders_controls(client):
    login_as(client, "root")

    response = client.get("/dashboard?group_by=not-a-real-column")

    assert response.status_code == 200
    assert "グループ別集計" in response.text
    assert 'value="base" selected' in response.text
    assert "東雲中央サービス拠点" in response.text
    assert "水鏡西部サービス拠点" in response.text


def test_dashboard_paginates_equipment_at_fifty_items(app, client):
    with app.app_context():
        db.session.add_all(
            [
                Equipment(
                    name=f"ページング試験設備{i:02d}",
                    location="試験拠点",
                    equipment_type="試験設備",
                    manufacturer="試験メーカー",
                    model_number=f"PAGE-{i:02d}",
                    installed_at=date(2020, 1, 1),
                    inspection_interval_months=12,
                    assigned_user_id=3,
                    next_inspection_date=date(2027, 1, 1),
                )
                for i in range(50)
            ]
        )
        db.session.commit()

    login_as(client, "root")
    first_page = client.get("/dashboard")
    second_page = client.get("/dashboard?page=2")

    assert first_page.status_code == 200
    assert "全 52 件・1 / 2 ページ" in first_page.text
    assert "次へ" in first_page.text
    assert second_page.status_code == 200
    assert "全 52 件・2 / 2 ページ" in second_page.text
    assert "ページング試験設備49" in second_page.text
