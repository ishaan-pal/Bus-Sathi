def test_fare_calculate(client):
    routes = client.get("/api/v1/buses/routes/all").json()
    route = routes[0]
    stops = route["stops"]
    resp = client.post(
        "/api/v1/tickets/fare/calculate",
        json={
            "route_id": route["id"],
            "boarding_stop": stops[0]["stop_name"],
            "destination_stop": stops[-1]["stop_name"],
            "adult_count": 1,
            "child_count": 0,
            "senior_count": 0,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["fare"]["total_fare_rupees"] > 0


def test_booking_flow(client, verified_user_token):
    search = client.post(
        "/api/v1/buses/search",
        json={
            "boarding_stop": "Chandigarh ISBT",
            "destination_stop": "Ambala City",
        },
    )
    results = search.json()["buses"]
    assert len(results) >= 1
    bus_id = results[0]["bus_id"]

    book = client.post(
        "/api/v1/tickets/book",
        json={
            "bus_id": bus_id,
            "boarding_stop": "Chandigarh ISBT",
            "destination_stop": "Ambala City",
            "adult_count": 1,
        },
        headers={"Authorization": f"Bearer {verified_user_token}"},
    )
    assert book.status_code == 200, book.text
    ticket_id = book.json()["ticket_id"]

    confirm = client.post(
        "/api/v1/tickets/confirm-payment",
        json={
            "ticket_id": ticket_id,
            "payment_id": "pay_demo_test",
            "razorpay_signature": "demo_sig",
        },
        headers={"Authorization": f"Bearer {verified_user_token}"},
    )
    assert confirm.status_code == 200

    active = client.get(
        "/api/v1/tickets/active",
        headers={"Authorization": f"Bearer {verified_user_token}"},
    )
    assert active.status_code == 200
    assert active.json()["total"] >= 1
