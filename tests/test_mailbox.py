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


async def test_list_messages_requires_token(client):
    response = await client.post("/mailboxes")

    mailbox_id = response.json()["id"]
    # запросить письма без токена - 401
    response = await client.get(f"/mailboxes/{mailbox_id}/messages")
    assert response.status_code == 401


async def test_authorization(client):
    response = await client.post("/mailboxes")

    mailbox_id = response.json()["id"]
    headers = {"Authorization": "Bearer wrongtoken"}
    response = await client.get(f"/mailboxes/{mailbox_id}/messages", headers=headers)
    assert response.status_code == 401


async def test_list_messages_with_token(client):
    response = await client.post("/mailboxes")
    data = response.json()
    mailbox_id = data["id"]
    token = data["token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get(f"/mailboxes/{mailbox_id}/messages", headers=headers)
    assert response.status_code == 200
    assert response.json()["count"] == 0


async def test_webhook_receives_email(client, brevo_headers):
    response = await client.post("/mailboxes")
    assert response.status_code == 201, response.text
    data = response.json()

    payload = {
        "items": [
            {
                "From": {"Name": "Sender", "Address": "sender@example.com"},
                "To": [{"Name": None, "Address": data["address"]}],
                "Subject": "Test subject",
                "RawTextBody": "Test body",
                "RawHtmlBody": None,
            }
        ]
    }
    response = await client.post(
        "/webhooks/brevo/inbound", json=payload, headers=brevo_headers
    )
    assert response.status_code == 200, response.text

    mailbox_headers = {"Authorization": f"Bearer {data['token']}"}
    response = await client.get(
        f"/mailboxes/{data['id']}/messages", headers=mailbox_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["messages"][0]["subject"] == "Test subject"


async def test_webhook_without_token(client):
    response = await client.post("/webhooks/brevo/inbound", json={})
    assert response.status_code == 401


async def test_webhook_wrong_token(client):
    response = await client.post(
        "/webhooks/brevo/inbound", json={}, headers={"Authorization": "Bearer wrong"}
    )
    assert response.status_code == 401
