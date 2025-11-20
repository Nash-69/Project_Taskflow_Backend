from datetime import datetime, timedelta

def test_tasks_crud_flow(client, create_test_user, app):
    user_id = create_test_user(email="taskuser@example.com")
    with app.app_context():
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=str(user_id))
    headers = {"Authorization": f"Bearer {token}"}

    due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    # CREATE (as form data, UPPERCASE enums)
    data = {
        "title": "Test Task",
        "description": "Testing task flow",
        "priority": "HIGH",
        "due_date": due_date
    }
    rv = client.post("/user/tasks/", data=data, headers=headers)
    assert rv.status_code == 201
    response_json = rv.get_json()
    task_id = response_json["data"]["task_id"]  # wrapped in "data"

    # GET
    rv = client.get(f"/user/tasks/{task_id}", headers=headers)
    assert rv.status_code == 200
    assert rv.get_json()["data"]["title"] == "Test Task"

    # UPDATE
    data = {"title": "Updated Task", "priority": "LOW"}
    rv = client.put(f"/user/tasks/{task_id}", data=data, headers=headers)
    assert rv.status_code == 200

    # DELETE
    rv = client.delete(f"/user/tasks/{task_id}", headers=headers)
    assert rv.status_code == 200


def test_unauthorized_task_access(client):
    rv = client.post("/user/tasks/", data={"title": "Secret", "due_date": "2025-12-31"})
    assert rv.status_code == 401

    rv = client.get("/user/tasks/999999")  # no trailing slash
    assert rv.status_code == 401


def test_create_task_with_invalid_data(client, auth_header):
    rv = client.post("/user/tasks/", data={"title": ""}, headers=auth_header)
    assert rv.status_code == 400


def test_get_nonexistent_task(client, auth_header):
    rv = client.get("/user/tasks/999999", headers=auth_header)
    assert rv.status_code == 404