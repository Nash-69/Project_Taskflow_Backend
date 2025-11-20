# tests/test_app_creation.py
def test_home_endpoint(client):
    rv = client.get("/")
    assert rv.status_code == 200


def test_auth_blueprint_exists(app):
    rules = [r.rule for r in app.url_map.iter_rules()]
    assert '/auth/login' in rules
    assert '/auth/signup' in rules
