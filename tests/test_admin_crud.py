from __future__ import annotations


def _admin_headers(client) -> dict[str, str]:
    response = client.post(
        "/auth/login-admin",
        json={"email": "admin@lojacontrol.local", "password": "admin123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_product_crud_and_pagination(client):
    headers = _admin_headers(client)

    create_response = client.post(
        "/admin/produtos",
        headers=headers,
        json={"nome": "Mouse Gamer", "descricao": "RGB", "preco": 199.9},
    )
    assert create_response.status_code == 200
    product_id = create_response.json()["id"]

    update_response = client.patch(
        f"/admin/produtos/{product_id}",
        headers=headers,
        json={"preco": 179.9},
    )
    assert update_response.status_code == 200
    assert update_response.json()["preco"] == 179.9

    paginated = client.get(
        "/admin/produtos/paginated?page=1&size=10&search=mouse&min_preco=100",
        headers=headers,
    )
    assert paginated.status_code == 200
    payload = paginated.json()
    assert payload["page"] == 1
    assert payload["size"] == 10
    assert payload["total"] >= 1
    assert any("Mouse" in item["nome"] for item in payload["items"])

    delete_response = client.delete(f"/admin/produtos/{product_id}", headers=headers)
    assert delete_response.status_code == 200
