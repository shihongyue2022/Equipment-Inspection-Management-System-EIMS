def test_login_success_sets_session(client):
    response = client.post(
        "/login",
        data={"employee_no": "TEC-201", "password": "engineer-password"},
    )
    assert response.status_code == 302
    assert response.location.endswith("/dashboard")
    with client.session_transaction() as flask_session:
        assert flask_session["user"]["id"] == 3


def test_login_rejects_wrong_password(client):
    response = client.post(
        "/login", data={"employee_no": "TEC-201", "password": "wrong"}
    )
    assert response.status_code == 200
    assert "社員番号またはパスワードに誤りがあります" in response.text


def test_protected_route_redirects_to_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert response.location.endswith("/login")


def test_logout_uses_post_and_clears_session(client):
    with client.session_transaction() as flask_session:
        flask_session["user"] = {"id": 3, "role": "engineer"}
    assert client.get("/logout").status_code == 405
    response = client.post("/logout")
    assert response.status_code == 302
    with client.session_transaction() as flask_session:
        assert "user" not in flask_session
