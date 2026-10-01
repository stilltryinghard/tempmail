from app.config import settings


async def test_create_mailbox(client):
    response = await client.post("/mailboxes")

    assert response.status_code == 201

    data = response.json()
    # проверка что в ответе есть нужные поля
    assert "id" in data
    assert "address" in data
    assert "token" in data
    assert "expires_at" in data
    assert "is_extended" in data

    assert data["address"].endswith("@" + settings.mail_domain)
    assert data["is_extended"] is False
    assert data["token"]


async def test_authorization(client):
    response = await client.post("/mailboxes")

    mailbox_id = response.json()["id"]
    headers = {"Authorization": "Bearer wrongtoken"}
    response = await client.get(f"/mailboxes/{mailbox_id}/messages", headers=headers)
    assert response.status_code == 401
