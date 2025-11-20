def test_signup_and_login_and_get_user(client):
    signup_payload = {"name": "Bob", "email": "bob@example.com", "password": "password123"}
    rv = client.post("/auth/signup", json=signup_payload)
    assert rv.status_code == 201

    login_payload = {"email": "bob@example.com", "password": "password123"}
    rv = client.post("/auth/login", json=login_payload)
    assert rv.status_code == 200

    token = rv.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    rv = client.get("/auth/user", headers=headers)
    assert rv.status_code == 200
    assert rv.get_json()["email"] == "bob@example.com"


def test_signup_duplicate_email_returns_400(client):
    client.post("/auth/signup", json={"name": "Alice", "email": "alice@example.com", "password": "pass"})
    rv = client.post("/auth/signup", json={"name": "Alice2", "email": "alice@example.com", "password": "pass2"})
    assert rv.status_code == 400


def test_wrong_login_returns_401(client):
    rv = client.post("/auth/login", json={"email": "notexists@example.com", "password": "wrong"})
    assert rv.status_code == 401


def test_unauthorized_access_to_protected_route(client):
    rv = client.get("/auth/user")
    assert rv.status_code == 401


def test_google_oauth_callback_creates_user(client, oauth_google_mock, app):
    oauth_google_mock.set_userinfo({
        "email": "googleuser@example.com",
        "name": "Google User",
        "sub": "google123"
    })
    rv = client.get("/auth/login/google/callback")
    assert rv.status_code in (200, 302)

    with app.app_context():
        from app.models.user import User
        user = User.query.filter_by(email="googleuser@example.com").first()
        assert user is not None
        assert user.provider == "google"
        assert user.provider_id == "google123"


def test_github_oauth_callback_creates_user(client, oauth_github_mock, app):
    oauth_github_mock.set_user({
        "id": 999,
        "login": "githubuser",
        "name": "GitHub User"
    })
    oauth_github_mock.set_emails([{"email": "gituser@example.com", "primary": True}])
    rv = client.get("/auth/login/github/callback")
    assert rv.status_code in (200, 302)

    with app.app_context():
        from app.models.user import User
        user = User.query.filter_by(email="gituser@example.com").first()
        assert user is not None
        assert user.provider == "github"
        assert user.provider_id == "999"