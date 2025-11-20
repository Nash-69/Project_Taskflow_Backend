import os
import sys
import uuid
import pytest
from unittest.mock import patch, MagicMock
from flask_jwt_extended import create_access_token
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db, oauth
from app.models.user import User


class DummyResp:
    def __init__(self, data):
        self._data = data
    def json(self):
        return self._data


@pytest.fixture(scope="session")
def app():
    os.environ.setdefault("FLASK_ENV", "testing")
    # DO NOT patch OAuth.register — it breaks client access
    with patch("app.notifications.scheduler.start_scheduler"):
        _app = create_app()
        _app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_ENGINE_OPTIONS={
                "poolclass": StaticPool,
                "connect_args": {"check_same_thread": False},
            },
            WTF_CSRF_ENABLED=False,
            SERVER_NAME="localhost"
        )

        with _app.app_context():
            db.create_all()
            # Pre-register OAuth client keys to avoid "No such client" error
            oauth._clients.setdefault("google", None)
            oauth._clients.setdefault("github", None)

        yield _app

        with _app.app_context():
            db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


@pytest.fixture()
def create_test_user(app):
    def _create_user(email=None, name="Test User", password="password"):
        if email is None:
            email = f"test_{uuid.uuid4().hex}@example.com"  # unique email
        with app.app_context():
            user = User(name=name, email=email)
            if password:
                user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return user.user_id
    return _create_user


@pytest.fixture()
def auth_header(app, create_test_user):
    user_id = create_test_user()
    with app.app_context():
        token = create_access_token(identity=str(user_id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def mock_sns(monkeypatch):
    mock = MagicMock()
    subscriptions = []

    def fake_boto3_client(service, region_name=None):
        return mock

    def fake_subscribe(**kwargs):
        sub_arn = "arn:aws:sns:123:sub-xyz"
        subscriptions.append({
            "SubscriptionArn": sub_arn,
            "Protocol": kwargs.get("Protocol"),
            "Endpoint": kwargs.get("Endpoint"),
            "TopicArn": kwargs.get("TopicArn")
        })
        return {"SubscriptionArn": sub_arn}

    def fake_list_subscriptions_by_topic(TopicArn):
        return {"Subscriptions": [s for s in subscriptions if s.get("TopicArn") == TopicArn]}

    monkeypatch.setattr("boto3.client", fake_boto3_client)
    mock.create_topic.return_value = {"TopicArn": "arn:aws:sns:us-east-1:123:test-topic"}
    mock.get_topic_attributes.return_value = {}
    mock.subscribe.side_effect = fake_subscribe
    mock.list_subscriptions_by_topic.side_effect = fake_list_subscriptions_by_topic
    mock.publish.return_value = {}
    return mock


@pytest.fixture()
def oauth_google_mock(app):
    class GoogleMock:
        def __init__(self):
            self._token = {"access_token": "dummy_token"}
            self._userinfo = {}
        def authorize_access_token(self):
            return self._token
        def get(self, path):
            return DummyResp(self._userinfo)
        def set_userinfo(self, data):
            self._userinfo = data
    mock = GoogleMock()
    with app.app_context():
        oauth._clients["google"] = mock
    return mock


@pytest.fixture()
def oauth_github_mock(app):
    class GitHubMock:
        def __init__(self):
            self._token = {"access_token": "gh_dummy"}
            self._user = {}
            self._emails = []
        def authorize_access_token(self):
            return self._token
        def get(self, path):
            if path == "user":
                return DummyResp(self._user)
            if path == "user/emails":
                return DummyResp(self._emails)
            return DummyResp({})
        def set_user(self, data):
            self._user = data
        def set_emails(self, emails):
            self._emails = emails
    mock = GitHubMock()
    with app.app_context():
        oauth._clients["github"] = mock
    return mock