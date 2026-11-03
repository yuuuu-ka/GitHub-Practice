from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


INITIAL_ACTIVITIES = deepcopy(activities)
ACTIVITY_NAME = "Art Club"
ACTIVITY_PATH = quote(ACTIVITY_NAME, safe="")


@pytest.fixture(autouse=True)
def reset_activities():
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))
    yield
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_get_activities_returns_available_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()[ACTIVITY_NAME]["participants"] == []


def test_signup_adds_participant(client):
    email = "student@example.com"

    response = client.post(
        f"/activities/{ACTIVITY_PATH}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {ACTIVITY_NAME}"
    }
    assert email in client.get("/activities").json()[ACTIVITY_NAME]["participants"]


def test_signup_rejects_duplicate_participant(client):
    email = "student@example.com"
    signup_url = f"/activities/{ACTIVITY_PATH}/signup"
    client.post(signup_url, params={"email": email})

    response = client.post(signup_url, params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert client.get("/activities").json()[ACTIVITY_NAME]["participants"] == [email]


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    email = "student@example.com"
    signup_url = f"/activities/{ACTIVITY_PATH}/signup"
    client.post(signup_url, params={"email": email})

    response = client.delete(signup_url, params={"email": email})

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {ACTIVITY_NAME}"
    }
    assert email not in client.get("/activities").json()[ACTIVITY_NAME]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Activity/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_for_unregistered_participant(client):
    response = client.delete(
        f"/activities/{ACTIVITY_PATH}/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"