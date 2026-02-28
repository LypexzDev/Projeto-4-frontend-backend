from __future__ import annotations

import uuid


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def test_register_login_and_me(client):
    email = _unique_email("user-auth")
    register_payload = {
        "nome": "Usuario Teste",
        "email": email,
        "password": "senha123",
        "saldo_inicial": 50,
    }
    register_response = client.post("/auth/register-user", json=register_payload)
    assert register_response.status_code == 200
    register_data = register_response.json()
    assert register_data["account"]["email"] == email
    assert register_data["account"]["role"] == "user"

    login_response = client.post(
        "/auth/login-user",
        json={"email": email, "password": "senha123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    assert token
    assert "lc_refresh_token=" in login_response.headers.get("set-cookie", "")

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    me_data = me_response.json()["account"]
    assert me_data["email"] == email
    assert me_data["role"] == "user"

    refresh_response = client.post("/auth/refresh")
    assert refresh_response.status_code == 200
    assert refresh_response.json().get("access_token")

    logout_response = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_response.status_code == 200

    refresh_after_logout = client.post("/auth/refresh")
    assert refresh_after_logout.status_code == 401


def test_admin_can_login_and_create_product(client):
    admin_login_response = client.post(
        "/auth/login-admin",
        json={"email": "admin@lojacontrol.local", "password": "admin123"},
    )
    assert admin_login_response.status_code == 200
    admin_token = admin_login_response.json()["token"]

    create_response = client.post(
        "/admin/produtos",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"nome": "Produto Admin", "descricao": "Criado em teste", "preco": 29.9},
    )
    assert create_response.status_code == 200
    data = create_response.json()
    assert data["nome"] == "Produto Admin"
    assert data["preco"] == 29.9
