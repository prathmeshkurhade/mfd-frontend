"""
E2E tests for Clients endpoints.
Tests: create → get → update → delete (soft delete)
All records are prefixed with TEST_PREFIX and deleted in teardown.
"""

import pytest
from tests.e2e.conftest import assert_ok, TEST_PREFIX


pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def created_client(client):
    """Create a client once for this test module, delete after."""
    payload = {
        "name": f"{TEST_PREFIX} Test Client",
        "phone": "+919100000001",
        "email": "e2e_client@testmail.com",
        "gender": "male",
        "source": "referral",
    }
    resp = client.post("/api/v1/clients/", json=payload)
    data = assert_ok(resp, 201)
    client_id = data["id"]

    yield data

    # Teardown
    client.delete(f"/api/v1/clients/{client_id}")


class TestClientCRUD:

    def test_create_client(self, created_client):
        assert created_client["id"] is not None
        assert TEST_PREFIX in created_client["name"]
        assert created_client["phone"] == "+919100000001"

    def test_get_client(self, client, created_client):
        client_id = created_client["id"]
        resp = client.get(f"/api/v1/clients/{client_id}")
        body = assert_ok(resp)
        assert body["id"] == client_id
        assert body["name"] == created_client["name"]

    def test_list_clients_contains_created(self, client, created_client):
        resp = client.get("/api/v1/clients/")
        body = assert_ok(resp)
        ids = [c["id"] for c in body["clients"]]
        assert created_client["id"] in ids

    def test_update_client(self, client, created_client):
        client_id = created_client["id"]
        resp = client.put(
            f"/api/v1/clients/{client_id}",
            json={"area": "Mumbai E2E"},
        )
        body = assert_ok(resp)
        assert body["area"] == "Mumbai E2E"

    def test_get_nonexistent_client_404(self, client):
        resp = client.get("/api/v1/clients/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestClientValidation:

    def test_create_client_invalid_phone(self, client):
        resp = client.post(
            "/api/v1/clients/",
            json={"name": "Bad Phone", "phone": "9999"},
        )
        assert resp.status_code == 422

    def test_create_client_missing_required(self, client):
        resp = client.post("/api/v1/clients/", json={"name": "No Phone"})
        assert resp.status_code == 422
