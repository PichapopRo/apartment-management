def _bootstrap_admin(client):
    client.post(
        "/auth/register",
        json={
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "Admin",
            "password": "StrongPass123",
            "role": "admin",
        },
    )


def _login(client, username, password):
    res = client.post(
        "/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return res.json()["access_token"]


def test_bill_calculation_with_late_fee(client):
    _bootstrap_admin(client)
    token = _login(client, "admin", "StrongPass123")

    # create room with rates
    room = client.post(
        "/rooms",
        json={"room_number": "C101", "floor": 1, "rent_rate": 5000, "status": "occupied"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    # set global rates
    client.put(
        "/billing/config",
        json={"water_rate": 20, "electric_rate": 7, "garbage_fee": 30, "late_fee": 300},
        headers={"Authorization": f"Bearer {token}"},
    )

    # previous month reading
    client.post(
        "/billing/readings",
        json={"room_id": room["id"], "billing_month": "2026-03", "water_value": 100, "electric_value": 200},
        headers={"Authorization": f"Bearer {token}"},
    )

    # current month reading
    client.post(
        "/billing/readings",
        json={"room_id": room["id"], "billing_month": "2026-04", "water_value": 120, "electric_value": 230},
        headers={"Authorization": f"Bearer {token}"},
    )

    bill = client.post(
        "/billing/bills",
        json={
            "room_id": room["id"],
            "billing_month": "2026-04",
            "late_fee_applied": True,
            "water_units_override": 15,
            "electric_units_override": 20,
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    assert float(bill["water_units"]) == 15
    assert float(bill["electric_units"]) == 20
    assert float(bill["water_amount"]) == 300  # 15 * 20
    assert float(bill["electric_amount"]) == 140  # 20 * 7
    assert float(bill["garbage_fee"]) == 30
    assert float(bill["late_fee"]) == 300
    assert float(bill["total_amount"]) == 5270
