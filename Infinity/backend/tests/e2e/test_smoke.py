"""
Smoke tests — public endpoints that need no auth.
These are the fastest sanity checks: is the server alive?
"""

import pytest
from tests.e2e.conftest import assert_ok


pytestmark = pytest.mark.e2e


class TestPublicHealth:

    def test_root(self, anon_client):
        resp = anon_client.get("/")
        body = assert_ok(resp)
        assert body["status"] == "running"

    def test_docs_accessible(self, anon_client):
        resp = anon_client.get("/docs")
        assert resp.status_code == 200


class TestCalculatorsNoAuth:

    def test_sip_calculator(self, anon_client):
        resp = anon_client.post(
            "/api/v1/calculators/sip-lumpsum-goal",
            json={
                "mode": "sip",
                "monthly_sip": 10000,
                "tenure_years": 10,
                "expected_return": 12.0,
            },
        )
        body = assert_ok(resp)
        assert body["sip_corpus"] > 0

    def test_lumpsum_calculator(self, anon_client):
        resp = anon_client.post(
            "/api/v1/calculators/sip-lumpsum-goal",
            json={
                "mode": "lumpsum",
                "lumpsum_amount": 100000,
                "tenure_years": 5,
                "expected_return": 12.0,
            },
        )
        body = assert_ok(resp)
        assert body["lumpsum_corpus"] > 0

    def test_get_investment_products(self, anon_client):
        resp = anon_client.get("/api/v1/calculators/products")
        body = assert_ok(resp)
        assert len(body["products"]) > 0

    def test_get_vacation_destinations(self, anon_client):
        resp = anon_client.get("/api/v1/calculators/destinations")
        body = assert_ok(resp)
        assert len(body["destinations"]) > 0

    def test_get_wedding_pricing(self, anon_client):
        resp = anon_client.get("/api/v1/calculators/wedding-pricing")
        body = assert_ok(resp)
        assert "pricing" in body

    def test_get_loan_types(self, anon_client):
        resp = anon_client.get("/api/v1/calculators/loan-types")
        body = assert_ok(resp)
        assert len(body["loan_types"]) > 0


class TestAuthRequiredReturns401:

    def test_tasks_without_token(self, anon_client):
        resp = anon_client.get("/api/v1/tasks/")
        assert resp.status_code in (401, 403)

    def test_leads_without_token(self, anon_client):
        resp = anon_client.get("/api/v1/leads/")
        assert resp.status_code in (401, 403)

    def test_clients_without_token(self, anon_client):
        resp = anon_client.get("/api/v1/clients/")
        assert resp.status_code in (401, 403)
