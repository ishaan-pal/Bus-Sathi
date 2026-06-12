def test_list_routes(client):
    resp = client.get("/api/v1/buses/routes/all")
    assert resp.status_code == 200
    routes = resp.json()
    assert len(routes) >= 1


def test_list_stops(client):
    resp = client.get("/api/v1/buses/stops/all")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 10
    assert "Chandigarh ISBT" in data["stops"]


def test_search_buses(client):
    resp = client.post(
        "/api/v1/buses/search",
        json={
            "boarding_stop": "Chandigarh ISBT",
            "destination_stop": "Ambala City",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["buses"], list)


def test_admin_list_buses(client, admin_token):
    resp = client.get(
        "/api/v1/buses/admin/all",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
