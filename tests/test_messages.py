async def test_html_body_is_sanitized(client, brevo_headers):
    r = await client.post("/mailboxes")
    data = r.json()
    payload = {
        "items": [
            {
                "From": {"Name": "Evil", "Address": "evil@example.com"},
                "To": [{"Name": None, "Address": data["address"]}],
                "Subject": "hi",
                "RawTextBody": "hi",
                "RawHtmlBody": '<p>hello</p><script>alert(1)</script><img src=x onerror="alert(1)">',
            }
        ]
    }
    await client.post("/webhooks/brevo/inbound", json=payload, headers=brevo_headers)

    auth = {"Authorization": f"Bearer {data['token']}"}
    msgs = (await client.get(f"/mailboxes/{data['id']}/messages", headers=auth)).json()
    msg_id = msgs["messages"][0]["id"]
    detail = (
        await client.get(f"/mailboxes/{data['id']}/messages/{msg_id}", headers=auth)
    ).json()

    html = detail["html_body"]
    assert "<p>hello</p>" in html
    assert "<script" not in html
    assert "onerror" not in html


async def test_list_messages_requires_token(client):
    response = await client.post("/mailboxes")

    mailbox_id = response.json()["id"]
    # запросить письма без токена - 401
    response = await client.get(f"/mailboxes/{mailbox_id}/messages")
    assert response.status_code == 401


async def test_html_only_email(client, brevo_headers):
    r = await client.post("/mailboxes")
    data = r.json()
    payload = {
        "items": [
            {
                "From": {"Name": "S", "Address": "s@example.com"},
                "To": [{"Name": None, "Address": data["address"]}],
                "Subject": "html only",
                "RawTextBody": None,
                "RawHtmlBody": "<p>code: 1234</p><script>alert(1)</script>",
            }
        ]
    }
    await client.post("/webhooks/brevo/inbound", json=payload, headers=brevo_headers)

    auth = {"Authorization": f"Bearer {data['token']}"}
    msgs = (await client.get(f"/mailboxes/{data['id']}/messages", headers=auth)).json()
    msg_id = msgs["messages"][0]["id"]
    detail = (
        await client.get(f"/mailboxes/{data['id']}/messages/{msg_id}", headers=auth)
    ).json()

    assert detail["body"] == ""
    assert "<p>code: 1234</p>" in detail["html_body"]
    assert "<script" not in detail["html_body"]


async def test_list_messages_with_token(client):
    response = await client.post("/mailboxes")
    data = response.json()
    headers = {"Authorization": f"Bearer {data['token']}"}
    response = await client.get(f"/mailboxes/{data['id']}/messages", headers=headers)
    assert response.status_code == 200
    assert response.json()["count"] == 0
