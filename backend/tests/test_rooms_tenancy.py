def _login(client, username, password):
    res = client.post(
        "/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def _bootstrap_admin(client):
    res = client.post(
        "/auth/register",
        json={
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "Admin",
            "password": "StrongPass123",
            "role": "admin",
        },
    )
    assert res.status_code == 200


def _create_user(client, token, username, email, role):
    res = client.post(
        "/auth/users",
        json={
            "username": username,
            "email": email,
            "full_name": username.title(),
            "password": "StrongPass123",
            "role": role,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    return res.json()


def test_room_create_admin_only_and_public_list(client):
    _bootstrap_admin(client)
    admin_token = _login(client, "admin", "StrongPass123")

    # Admin can create room
    res = client.post(
        "/rooms",
        json={"room_number": "A101", "floor": 1, "rent_rate": 5000, "status": "vacant"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 201

    # Resident can only see public list
    _create_user(client, admin_token, "res1", "res1@example.com", "resident")
    resident_token = _login(client, "res1", "StrongPass123")

    res = client.get("/rooms/public", headers={"Authorization": f"Bearer {resident_token}"})
    assert res.status_code == 200
    public = res.json()
    assert public[0]["room_number"] == "A101"
    assert "status" in public[0]

    # Resident cannot access full list
    res = client.get("/rooms", headers={"Authorization": f"Bearer {resident_token}"})
    assert res.status_code == 403

    # Admin can delete room
    room_id = res = client.post(
        "/rooms",
        json={"room_number": "A103", "floor": 1, "rent_rate": 5000, "status": "vacant"},
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()["id"]
    del_res = client.delete(f"/rooms/{room_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_res.status_code == 204


def test_staff_can_assign_tenancy_with_name_only(client):
    _bootstrap_admin(client)
    admin_token = _login(client, "admin", "StrongPass123")
    _create_user(client, admin_token, "staff1", "staff1@example.com", "staff")

    # Create room
    res = client.post(
        "/rooms",
        json={"room_number": "B202", "floor": 2, "rent_rate": 7000, "status": "vacant"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    room_id = res.json()["id"]

    staff_token = _login(client, "staff1", "StrongPass123")
    res = client.post(
        "/tenancies/assign",
        json={"room_id": room_id, "resident_name": "Walk-in Tenant", "move_in_date": "2026-04-02"},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["resident_name"] == "Walk-in Tenant"
