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
