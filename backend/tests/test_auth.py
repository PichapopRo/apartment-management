def test_bootstrap_admin_and_login(client):
    # Bootstrap admin (first user)
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
    data = res.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"

    # Login with username
    res = client.post(
        "/auth/login",
        data={"username": "admin", "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    assert token


def test_register_closed_after_first_user(client):
    # First admin
    client.post(
        "/auth/register",
        json={
            "username": "admin2",
            "email": "admin2@example.com",
            "full_name": "Admin2",
            "password": "StrongPass123",
            "role": "admin",
        },
    )
    # Second registration should default to resident and succeed
    res = client.post(
        "/auth/register",
        json={
            "username": "resident",
            "email": "r@example.com",
            "full_name": "Resident",
            "password": "StrongPass123",
            "role": "resident",
        },
    )
    assert res.status_code == 200
    assert res.json()["role"] == "resident"
