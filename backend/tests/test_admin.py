def test_dashboard(client, admin_token):
    resp = client.get(
        "/api/v1/admin/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    stats = resp.json()["stats"]
    assert "users" in stats
    assert "buses" in stats


def test_dashboard_forbidden_for_user(client, user_token):
    resp = client.get(
        "/api/v1/admin/dashboard",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


def test_live_monitor(client, admin_token):
    resp = client.get(
        "/api/v1/admin/monitor/live",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert "buses" in resp.json()
