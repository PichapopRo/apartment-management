from io import BytesIO

import pandas as pd


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


def test_export_all_wide_format(client):
    _bootstrap_admin(client)
    token = _login(client, "admin", "StrongPass123")

    room = client.post(
        "/rooms",
        json={"room_number": "C101", "floor": 1, "rent_rate": 1000, "status": "occupied"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    client.put(
        "/billing/config",
        json={"water_rate": 10, "electric_rate": 5, "garbage_fee": 30, "late_fee": 300},
        headers={"Authorization": f"Bearer {token}"},
    )

    # readings for two months
    client.post(
        "/billing/readings",
        json={"room_id": room["id"], "billing_month": "2026-03", "water_value": 100, "electric_value": 200},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/billing/readings",
        json={"room_id": room["id"], "billing_month": "2026-04", "water_value": 110, "electric_value": 210},
        headers={"Authorization": f"Bearer {token}"},
    )

    # bill for 2026-04
    bill = client.post(
        "/billing/bills",
        json={
            "room_id": room["id"],
            "billing_month": "2026-04",
            "late_fee_applied": False,
        },
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    # export all
    res = client.get("/reports/export-all", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

    data = BytesIO(res.content)
    bills_df = pd.read_excel(data, sheet_name="Bills")
    water_df = pd.read_excel(data, sheet_name="Water")
    electric_df = pd.read_excel(data, sheet_name="Electric")

    assert "room_number" in bills_df.columns
    assert "2026-04" in bills_df.columns
    row = bills_df[bills_df["room_number"] == "C101"].iloc[0]
    assert float(row["2026-04"]) == float(bill["total_amount"])

    assert "2026-03" in water_df.columns
    assert "2026-04" in water_df.columns
    wrow = water_df[water_df["room_number"] == "C101"].iloc[0]
    assert float(wrow["2026-03"]) == 100.0
    assert float(wrow["2026-04"]) == 110.0

    assert "2026-03" in electric_df.columns
    assert "2026-04" in electric_df.columns
    erow = electric_df[electric_df["room_number"] == "C101"].iloc[0]
    assert float(erow["2026-03"]) == 200.0
    assert float(erow["2026-04"]) == 210.0
