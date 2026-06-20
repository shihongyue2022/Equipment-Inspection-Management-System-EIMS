from conftest import login_as


def test_login_uses_local_tabler_assets(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert "/static/vendor/tabler/css/tabler.min.css" in response.text
    assert "/static/vendor/tabler/js/tabler.min.js" in response.text
    assert "/static/vendor/tabler-icons/tabler-icons.min.css" in response.text
    assert "cdn.jsdelivr.net" not in response.text


def test_authenticated_layout_renders_tabler_sidebar(client):
    login_as(client, "root")

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert 'class="navbar navbar-vertical navbar-expand-lg"' in response.text
    assert "設備管理" in response.text
    assert "アカウント管理" in response.text


def test_tabler_static_files_are_served(client):
    paths = (
        "/static/vendor/tabler/css/tabler.min.css",
        "/static/vendor/tabler/js/tabler.min.js",
        "/static/vendor/tabler-icons/tabler-icons.min.css",
        "/static/vendor/tabler-icons/fonts/tabler-icons.woff2",
    )

    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.data, path
