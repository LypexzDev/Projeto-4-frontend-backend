from __future__ import annotations

import uuid


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def test_user_can_buy_product_and_balance_is_updated(client):
    admin_login = client.post(
        "/auth/login-admin",
        json={"email": "admin@lojacontrol.local", "password": "admin123"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["token"]

    create_product = client.post(
        "/admin/produtos",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"nome": "Teclado", "descricao": "Mecanico", "preco": 120.0},
    )
    assert create_product.status_code == 200
    product_id = create_product.json()["id"]

    user_email = _unique_email("comprador")
    register_user = client.post(
        "/auth/register-user",
        json={
            "nome": "Comprador Teste",
            "email": user_email,
            "password": "senha123",
            "saldo_inicial": 200.0,
        },
    )
    assert register_user.status_code == 200

    login_user = client.post("/auth/login-user", json={"email": user_email, "password": "senha123"})
    assert login_user.status_code == 200
    user_token = login_user.json()["token"]

    checkout_response = client.post(
        "/shop/pedidos",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"produtos_ids": [product_id]},
    )
    assert checkout_response.status_code == 200
    checkout_data = checkout_response.json()
    assert checkout_data["total"] == 120.0
    assert len(checkout_data["produtos"]) == 1

    profile_response = client.get("/shop/me", headers={"Authorization": f"Bearer {user_token}"})
    assert profile_response.status_code == 200
    assert profile_response.json()["saldo"] == 80.0

