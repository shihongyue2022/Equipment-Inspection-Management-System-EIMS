from app.extensions import db
from app.models import User
from conftest import login_as


def user_form(**overrides):
    values = {
        "employee_no": "TEC-300",
        "last_name": "星野",
        "first_name": "空",
        "email": "new@example.test",
        "password": "new-password",
        "role": "engineer",
        "phone": "",
        "base": "東雲中央サービス拠点",
    }
    values.update(overrides)
    return values


def test_admin_can_create_engineer(client, app):
    login_as(client, "admin")
    response = client.post("/accounts/new", data=user_form())
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(User, 5).employee_no == "TEC-300"


def test_admin_cannot_create_admin(client):
    login_as(client, "admin")
    response = client.post("/accounts/new", data=user_form(role="admin"))
    assert response.status_code == 200
    assert "このロールは指定できません" in response.text


def test_root_can_edit_engineer_role(client, app):
    login_as(client, "root")
    values = user_form(
        employee_no="TEC-201",
        email="engineer@example.test",
        role="admin",
    )
    values.pop("password")
    response = client.post("/accounts/3", data=values)
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(User, 3).role == "admin"


def test_user_with_inspections_cannot_be_deleted(client, inspection_factory):
    inspection_factory()
    login_as(client, "root")
    response = client.post("/accounts/3/delete")
    assert response.status_code == 200
    assert "点検記録が 1 件あるため削除できません" in response.text


def test_engineer_changes_own_password(client, app):
    login_as(client, "engineer")
    response = client.post(
        "/my/password",
        data={
            "current_password": "engineer-password",
            "new_password": "changed-password",
            "confirm_password": "changed-password",
        },
    )
    assert response.status_code == 200
    assert "パスワードを変更しました" in response.text


def test_account_management_combines_search_filters(client):
    login_as(client, "root")

    response = client.get(
        "/accounts?q=朝霧&role=engineer&base=東雲中央サービス拠点"
    )

    assert response.status_code == 200
    assert "1 件一致" in response.text
    assert "朝霧湊" in response.text
    assert "月岡澪" not in response.text


def test_account_management_hides_empty_facet_options(client):
    login_as(client, "root")

    response = client.get("/accounts?base=東雲中央サービス拠点")

    assert response.status_code == 200
    assert "FE（1）" in response.text
    assert "管理者（1）" not in response.text
    assert "水鏡西部サービス拠点（1）" in response.text
