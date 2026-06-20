from datetime import date, timedelta

from conftest import login_as

from app.extensions import db
from app.models import Equipment, Inspection
from app.services.dashboard import dashboard_summary, grouped_equipment_summary
from app.services.equipment import dashboard_filter_options


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
                "normal_count": 0,
                "watch_count": 0,
                "repair_status_count": 0,
                "uninspected_count": 1,
            }
        ]


def test_dashboard_rejects_unknown_group_and_renders_controls(client):
    login_as(client, "root")

    response = client.get("/dashboard?group_by=not-a-real-column")

    assert response.status_code == 200
    assert "グループ別集計" in response.text
    assert 'value="base" selected' in response.text
    assert 'class="group-chart-item"' in response.text
    assert 'class="group-chart-summary"' in response.text
    assert 'class="group-chart-detail"' in response.text
    assert 'class="group-status-track"' in response.text
    assert "未点検 <strong>100.0%</strong>" in response.text
    assert 'id="sortBy"' in response.text
    assert 'id="sortOrder"' in response.text
    assert 'value="total" selected' in response.text
    assert 'value="desc" selected' in response.text
    assert "点検超過 0件" in response.text
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


def test_grouped_summary_sorts_by_status_rate(app):
    with app.app_context():
        db.session.add_all(
            [
                Inspection(
                    equipment_id=1,
                    engineer_id=3,
                    inspected_at=date(2026, 6, 20),
                    status="normal",
                ),
                Inspection(
                    equipment_id=2,
                    engineer_id=4,
                    inspected_at=date(2026, 6, 20),
                    status="repair",
                ),
            ]
        )
        db.session.commit()

        repair_first = grouped_equipment_summary(
            "base", sort_by="repair_rate", sort_order="desc"
        )
        normal_first = grouped_equipment_summary(
            "base", sort_by="normal_rate", sort_order="desc"
        )

        assert repair_first[0]["group_name"] == "水鏡西部サービス拠点"
        assert normal_first[0]["group_name"] == "東雲中央サービス拠点"


def test_pagination_preserves_group_sorting(app, client):
    with app.app_context():
        db.session.add_all(
            [
                Equipment(
                    name=f"並び替えページ設備{i:02d}",
                    location="試験拠点",
                    equipment_type="試験設備",
                    manufacturer="試験メーカー",
                    model_number=f"SORT-{i:02d}",
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
    response = client.get(
        "/dashboard?group_by=engineer&sort_by=repair_rate&sort_order=asc"
    )

    assert response.status_code == 200
    assert "sort_by=repair_rate" in response.text
    assert "sort_order=asc" in response.text


def test_combined_filters_narrow_scope_and_change_redundant_group(app, client):
    with app.app_context():
        summary = dashboard_summary(
            base="東雲中央サービス拠点",
            equipment_type="空調機",
            manufacturer="北辰空調工業",
            engineer_id=3,
        )
        assert summary["total_count"] == 1
        assert (
            dashboard_summary(
                base="東雲中央サービス拠点",
                equipment_type="空調機",
                manufacturer="雲雀設備製作所",
                engineer_id=3,
            )["total_count"]
            == 0
        )

    login_as(client, "root")
    response = client.get(
        "/dashboard?base=東雲中央サービス拠点"
        "&equipment_type=空調機"
        "&manufacturer=北辰空調工業"
        "&engineer_id=3"
        "&group_by=base"
    )

    assert response.status_code == 200
    assert "4 条件" in response.text
    assert 'value="status" selected' in response.text
    assert "全 1 件" in response.text
    assert "中央棟サーバー室冷房機" in response.text
    assert "地下搬入口換気ユニット" not in response.text


def test_faceted_filters_exclude_options_without_matching_records(app, client):
    with app.app_context():
        options = dashboard_filter_options(base="東雲中央サービス拠点")

        assert options["equipment_types"] == [{"value": "空調機", "count": 1}]
        assert options["manufacturers"] == [
            {"value": "北辰空調工業", "count": 1}
        ]
        assert options["engineers"] == [
            {"id": 3, "name": "朝霧湊", "count": 1}
        ]
        assert all(
            option["count"] > 0
            for facet in options.values()
            for option in facet
        )

    login_as(client, "root")
    response = client.get("/dashboard?base=東雲中央サービス拠点")

    assert response.status_code == 200
    assert "北辰空調工業（1）" in response.text
    assert "雲雀設備製作所（1）" not in response.text


def test_group_chart_collapses_groups_after_twelve(app, client):
    with app.app_context():
        db.session.add_all(
            [
                Equipment(
                    name=f"分類表示試験設備{i:02d}",
                    location="試験拠点",
                    equipment_type=f"分類{i:02d}",
                    manufacturer="試験メーカー",
                    model_number=f"GROUP-{i:02d}",
                    installed_at=date(2020, 1, 1),
                    inspection_interval_months=12,
                    assigned_user_id=3,
                    next_inspection_date=date(2027, 1, 1),
                )
                for i in range(13)
            ]
        )
        db.session.commit()

    login_as(client, "root")
    response = client.get("/dashboard?group_by=equipment_type")

    assert response.status_code == 200
    assert 'class="group-chart-more"' in response.text
    assert "残り 3 グループを表示" in response.text
