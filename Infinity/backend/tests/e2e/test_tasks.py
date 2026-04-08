"""
E2E tests for Tasks endpoints.
Tests: create → get → list → update → complete → carry-forward → delete
"""

import pytest
from datetime import date, timedelta
from tests.e2e.conftest import assert_ok, TEST_PREFIX


pytestmark = pytest.mark.e2e

FUTURE_DATE = (date.today() + timedelta(days=7)).isoformat()
LATER_DATE  = (date.today() + timedelta(days=14)).isoformat()


@pytest.fixture(scope="module")
def created_task(client):
    """Create a task for this module, delete after all tests."""
    payload = {
        "title": f"{TEST_PREFIX} E2E Task",
        "due_date": FUTURE_DATE,
        "priority": "high",
        "description": "E2E test task",
    }
    resp = client.post("/api/v1/tasks/", json=payload)
    data = assert_ok(resp, 201)
    task_id = data["id"]

    yield data

    # Teardown
    client.delete(f"/api/v1/tasks/{task_id}")


class TestTaskCRUD:

    def test_create_task(self, created_task):
        assert created_task["id"] is not None
        assert created_task["status"] == "pending"
        assert created_task["priority"] == "high"

    def test_get_task(self, client, created_task):
        task_id = created_task["id"]
        resp = client.get(f"/api/v1/tasks/{task_id}")
        body = assert_ok(resp)
        assert body["id"] == task_id

    def test_list_tasks_contains_created(self, client, created_task):
        resp = client.get("/api/v1/tasks/")
        body = assert_ok(resp)
        ids = [t["id"] for t in body["tasks"]]
        assert created_task["id"] in ids

    def test_update_task(self, client, created_task):
        task_id = created_task["id"]
        resp = client.put(
            f"/api/v1/tasks/{task_id}",
            json={"priority": "low"},
        )
        body = assert_ok(resp)
        assert body["priority"] == "low"

    def test_complete_task(self, client, created_task):
        task_id = created_task["id"]
        resp = client.post(f"/api/v1/tasks/{task_id}/complete")
        body = assert_ok(resp)
        assert body["status"] == "completed"
        assert body["completed_at"] is not None

    def test_get_today_tasks(self, client):
        resp = client.get("/api/v1/tasks/today")
        body = assert_ok(resp)
        assert "pending" in body
        assert "completed" in body
        assert "overdue" in body

    def test_get_nonexistent_task_404(self, client):
        resp = client.get("/api/v1/tasks/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestTaskValidation:

    def test_create_task_missing_due_date(self, client):
        resp = client.post(
            "/api/v1/tasks/",
            json={"title": "No date task"},
        )
        assert resp.status_code == 422

    def test_create_task_missing_title(self, client):
        resp = client.post(
            "/api/v1/tasks/",
            json={"due_date": FUTURE_DATE},
        )
        assert resp.status_code == 422

    def test_create_task_invalid_priority(self, client):
        resp = client.post(
            "/api/v1/tasks/",
            json={"title": "Bad prio", "due_date": FUTURE_DATE, "priority": "extreme"},
        )
        assert resp.status_code == 422
