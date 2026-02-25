import copy

import pytest
from fastapi.testclient import TestClient

from src import app as application

# fixture to provide a TestClient instance
@pytest.fixture

def client():
    return TestClient(application.app)

# autouse fixture: keeps the activities dict fresh for every test
@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(application.activities)
    yield
    application.activities.clear()
    application.activities.update(copy.deepcopy(original))


def test_root_redirect(client):
    # Arrange -- nothing special to set up

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all(client):
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == application.activities


def test_signup_for_activity_success(client):
    # Arrange
    activity = "Chess Club"
    new_email = "newstudent@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": new_email})

    # Assert
    assert response.status_code == 200
    assert "Signed up" in response.json()["message"]
    assert new_email in application.activities[activity]["participants"]


def test_signup_for_activity_already_signed(client):
    # Arrange
    activity = "Chess Club"
    existing = "michael@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": existing})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_for_nonexistent_activity(client):
    # Arrange

    # Act
    response = client.post("/activities/NoSuch/signup", params={"email": "foo@bar.com"})

    # Assert
    assert response.status_code == 404
    # FastAPI returns a generic signature when path not matched
    # just ensure we didn't accidentally allow the request
    assert response.json().get("detail") in ("Activity not found", "Not Found")


def test_remove_participant_success(client):
    # Arrange
    activity = "Chess Club"
    to_remove = "michael@mergington.edu"
    assert to_remove in application.activities[activity]["participants"]

    # Act
    response = client.delete(f"/activities/{activity}/participants", params={"email": to_remove})

    # Assert
    assert response.status_code == 200
    assert "Removed" in response.json()["message"]
    assert to_remove not in application.activities[activity]["participants"]


def test_remove_participant_not_in_activity(client):
    # Arrange
    activity = "Chess Club"
    missing = "ghost@mergington.edu"
    assert missing not in application.activities[activity]["participants"]

    # Act
    response = client.delete(f"/activities/{activity}/participants", params={"email": missing})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in activity"


def test_remove_from_nonexistent_activity(client):
    # Arrange

    # Act
    response = client.delete("/activities/NoActivity/participants", params={"email": "foo@bar.com"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"