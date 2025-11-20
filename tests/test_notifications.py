def test_notifications_subscribe_unsubscribe(client, auth_header, mock_sns, app):
    # Subscribe
    rv = client.post("/notifications/subscribe", headers=auth_header)
    assert rv.status_code in (200, 201)

    # Unsubscribe
    rv = client.post("/notifications/unsubscribe", headers=auth_header)
    assert rv.status_code in (200, 204)