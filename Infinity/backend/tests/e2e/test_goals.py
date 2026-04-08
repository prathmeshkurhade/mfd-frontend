"""
E2E tests for Goals endpoints.
Goals require a client_id, so we create a client first.
Tests: create → get → update progress → delete
"""

import pytest
from tests.e2e.conftest import assert_ok, TEST_PREFIX


pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def goal_test_client(client):
    """Create a temporary client to attach goals to."""
    payload = {
        "name": f"{TEST_PREFIX} Goals Test Client",
        "phone": "+919200000001",
        "gender": "male",
        "source": "referral",
    }
    resp = client.post("/api/v1/clients/", json=payload)
    data = assert_ok(resp, 201)
    client_id = data["id"]

    yield client_id

    # Teardown
    client.delete(f"/api/v1/clients/{client_id}")


@pytest.fixture(scope="module")
def created_goal(client, goal_test_client):
    """Create a goal for this module, delete after."""
    client_id = goal_test_client
    payload = {
        "client_id": client_id,
        "goal_type": "retirement",
        "goal_name": f"{TEST_PREFIX} Retirement Goal",
        "target_amount": 5000000,
        "target_date": "2045-01-01",
        "current_investment": 100000,
        "monthly_sip": 10000,
        "expected_return_rate": 12.0,
    }
    resp = client.post("/api/v1/goals/", json=payload)
    data = assert_ok(resp, 201)
    goal_id = data["id"]

    yield data

    # Teardown
    client.delete(f"/api/v1/goals/{goal_id}")


class TestGoalCRUD:

    def test_create_goal(self, created_goal):
        assert created_goal["id"] is not None
        assert created_goal["goal_type"] == "retirement"
        assert created_goal["target_amount"] == 5000000
        assert created_goal["status"] == "active"

    def test_get_goal(self, client, created_goal):
        goal_id = created_goal["id"]
        resp = client.get(f"/api/v1/goals/{goal_id}")
        body = assert_ok(resp)
        assert body["id"] == goal_id
        assert body["goal_type"] == "retirement"

    def test_list_goals_contains_created(self, client, created_goal):
        resp = client.get("/api/v1/goals/")
        body = assert_ok(resp)
        ids = [g["id"] for g in body["goals"]]
        assert created_goal["id"] in ids

    def test_update_goal_progress(self, client, created_goal):
        goal_id = created_goal["id"]
        resp = client.patch(
            f"/api/v1/goals/{goal_id}/progress",
            params={"current_investment": 250000},
        )
        body = assert_ok(resp)
        assert body["current_investment"] == 250000
        assert body["progress_percent"] == 5.0  # 250000/5000000 * 100

    def test_update_goal(self, client, created_goal):
        goal_id = created_goal["id"]
        resp = client.put(
            f"/api/v1/goals/{goal_id}",
            json={"monthly_sip": 15000},
        )
        body = assert_ok(resp)
        assert body["monthly_sip"] == 15000

    def test_get_goals_by_client(self, client, goal_test_client, created_goal):
        client_id = goal_test_client
        resp = client.get(f"/api/v1/goals/client/{client_id}")
        body = assert_ok(resp)
        assert isinstance(body, list)
        ids = [g["id"] for g in body]
        assert created_goal["id"] in ids

    def test_get_nonexistent_goal_404(self, client):
        resp = client.get("/api/v1/goals/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestGoalValidation:

    def test_create_goal_negative_target(self, client, goal_test_client):
        resp = client.post(
            "/api/v1/goals/",
            json={
                "client_id": goal_test_client,
                "goal_type": "retirement",
                "goal_name": "Bad Goal",
                "target_amount": -100,
            },
        )
        assert resp.status_code == 422

    def test_create_goal_missing_client_id(self, client):
        resp = client.post(
            "/api/v1/goals/",
            json={
                "goal_type": "retirement",
                "goal_name": "No client",
                "target_amount": 1000000,
            },
        )
        assert resp.status_code == 422
