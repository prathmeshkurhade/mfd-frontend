"""
E2E tests for Leads endpoints.
Tests: create → get → update → update status → delete
All records are prefixed with TEST_PREFIX and deleted in teardown.
"""

import pytest
from tests.e2e.conftest import assert_ok, TEST_PREFIX


pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def created_lead(client):
    """Create a lead once for this test module, delete it after."""
    payload = {
        "name": f"{TEST_PREFIX} Lead User",
        "phone": "+919000000001",
        "email": "e2e_lead@testmail.com",
        "status": "follow_up",
        "source": "referral",
        "notes": "Created by E2E test",
    }
    resp = client.post("/api/v1/leads/", json=payload)
    data = assert_ok(resp, 201)
    lead_id = data["id"]

    yield data

    # Teardown: delete the lead
    client.delete(f"/api/v1/leads/{lead_id}")


class TestLeadCRUD:

    def test_create_lead(self, created_lead):
        assert created_lead["id"] is not None
        assert TEST_PREFIX in created_lead["name"]
        assert created_lead["phone"] == "+919000000001"
        assert created_lead["status"] == "follow_up"

    def test_get_lead(self, client, created_lead):
        lead_id = created_lead["id"]
        resp = client.get(f"/api/v1/leads/{lead_id}")
        body = assert_ok(resp)
        assert body["id"] == lead_id

    def test_list_leads_contains_created(self, client, created_lead):
        resp = client.get("/api/v1/leads/")
        body = assert_ok(resp)
        ids = [l["id"] for l in body["leads"]]
        assert created_lead["id"] in ids

    def test_update_lead(self, client, created_lead):
        lead_id = created_lead["id"]
        resp = client.put(
            f"/api/v1/leads/{lead_id}",
            json={"notes": "Updated by E2E test"},
        )
        body = assert_ok(resp)
        assert body["notes"] == "Updated by E2E test"

    def test_update_lead_status(self, client, created_lead):
        lead_id = created_lead["id"]
        resp = client.patch(
            f"/api/v1/leads/{lead_id}/status",
            json={"status": "meeting_scheduled"},
        )
        body = assert_ok(resp)
        assert body["status"] == "meeting_scheduled"

    def test_get_nonexistent_lead_404(self, client):
        resp = client.get("/api/v1/leads/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestLeadValidation:

    def test_create_lead_invalid_phone(self, client):
        resp = client.post(
            "/api/v1/leads/",
            json={"name": "Bad Phone", "phone": "9999"},
        )
        assert resp.status_code == 422

    def test_create_lead_missing_required(self, client):
        resp = client.post("/api/v1/leads/", json={"name": "No Phone"})
        assert resp.status_code == 422
