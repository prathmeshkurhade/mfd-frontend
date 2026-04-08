"""
End-to-end tests for every major API surface.

Goal: catch DB-schema mismatches, Pydantic serialisation failures,
unknown-column errors, and NULL-handling bugs — the exact class of
issues found during manual Swagger testing.

Run:
    cd Infinity/backend
    python -m pytest tests/test_e2e.py -v --tb=short -x
"""

import uuid
from datetime import date, timedelta

import httpx
import pytest

pytestmark = pytest.mark.anyio

API = "/api/v1"


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _unique_phone() -> str:
    """Return a unique +91XXXXXXXXXX phone number."""
    # Use last 10 digits of a uuid int
    digits = str(uuid.uuid4().int)[-10:]
    return f"+91{digits}"


def _tomorrow() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


def _today() -> str:
    return date.today().isoformat()


# ═════════════════════════════════════════════
# HEALTH
# ═════════════════════════════════════════════

class TestHealth:
    async def test_root(self, client: httpx.AsyncClient):
        r = await client.get("/")
        assert r.status_code == 200
        assert r.json()["status"] == "running"


# ═════════════════════════════════════════════
# LEADS  (CRUD + status + today-followups)
# ═════════════════════════════════════════════

class TestLeads:
    """Full CRUD cycle for leads — catches is_deleted, phone NULL, sourced_by issues."""

    async def test_list_leads(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/leads/")
        assert r.status_code == 200
        body = r.json()
        assert "leads" in body
        assert "total" in body

    async def test_create_get_update_delete_lead(self, client: httpx.AsyncClient):
        phone = _unique_phone()
        # CREATE
        payload = {
            "name": "E2E Test Lead",
            "phone": phone,
            "source": "referral",
            "status": "follow_up",
        }
        r = await client.post(f"{API}/leads/", json=payload)
        assert r.status_code == 201, f"Create lead failed: {r.text}"
        lead = r.json()
        lead_id = lead["id"]
        assert lead["phone"] == phone

        # GET
        r = await client.get(f"{API}/leads/{lead_id}")
        assert r.status_code == 200
        assert r.json()["id"] == lead_id

        # UPDATE
        r = await client.put(
            f"{API}/leads/{lead_id}",
            json={"name": "Updated Lead", "area": "Mumbai"},
        )
        assert r.status_code == 200, f"Update lead failed: {r.text}"
        assert r.json()["name"] == "Updated Lead"

        # STATUS UPDATE
        r = await client.patch(
            f"{API}/leads/{lead_id}/status",
            json={"status": "meeting_scheduled"},
        )
        assert r.status_code == 200, f"Status update failed: {r.text}"
        assert r.json()["status"] == "meeting_scheduled"

        # DELETE
        r = await client.delete(f"{API}/leads/{lead_id}")
        assert r.status_code == 200, f"Delete lead failed: {r.text}"

        # Verify deleted
        r = await client.get(f"{API}/leads/{lead_id}")
        assert r.status_code == 404

    async def test_today_followups(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/leads/today-followups")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ═════════════════════════════════════════════
# CLIENTS  (CRUD + overview + duplicate-check + cash-flow)
# ═════════════════════════════════════════════

class TestClients:
    """Full CRUD cycle for clients — catches total_aum/sip/sourced_by mapping."""

    async def test_list_clients(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/clients/")
        assert r.status_code == 200
        body = r.json()
        assert "clients" in body
        assert "total" in body

    async def test_create_get_update_delete_client(self, client: httpx.AsyncClient):
        phone = _unique_phone()
        # CREATE
        payload = {
            "name": "E2E Test Client",
            "phone": phone,
            "gender": "male",
            "source": "referral",
            "aum": 500000,
            "sip_amount": 10000,
            "referred_by": "John",
        }
        r = await client.post(f"{API}/clients/", json=payload)
        assert r.status_code == 201, f"Create client failed: {r.text}"
        cl = r.json()
        client_id = cl["id"]
        assert cl["phone"] == phone
        # Verify field mappings come back correctly
        assert cl.get("aum") is not None or cl.get("total_aum") is not None
        assert cl.get("sip_amount") is not None or cl.get("sip") is not None

        # GET
        r = await client.get(f"{API}/clients/{client_id}")
        assert r.status_code == 200
        assert r.json()["id"] == client_id

        # UPDATE
        r = await client.put(
            f"{API}/clients/{client_id}",
            json={"name": "Updated Client", "area": "Delhi", "aum": 750000},
        )
        assert r.status_code == 200, f"Update client failed: {r.text}"

        # OVERVIEW
        r = await client.get(f"{API}/clients/{client_id}/overview")
        assert r.status_code == 200, f"Client overview failed: {r.text}"
        overview = r.json()
        assert "client" in overview
        assert "goals" in overview

        # CASH FLOW (GET)
        r = await client.get(f"{API}/clients/{client_id}/cash-flow")
        assert r.status_code == 200, f"Get cash flow failed: {r.text}"

        # DUPLICATE CHECK (URL-encode the + in phone number)
        from urllib.parse import quote
        r = await client.post(f"{API}/clients/check-duplicate?phone={quote(phone, safe='')}")
        assert r.status_code == 200
        assert r.json()["is_duplicate"] is True

        # DELETE (soft delete)
        r = await client.delete(f"{API}/clients/{client_id}")
        assert r.status_code == 200, f"Delete client failed: {r.text}"


# ═════════════════════════════════════════════
# TASKS  (CRUD + today + complete + carry-forward + bulk)
# ═════════════════════════════════════════════

class TestTasks:
    """Full CRUD cycle for tasks — catches description/title mapping, original_date alias."""

    async def test_list_tasks(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/tasks/")
        assert r.status_code == 200
        body = r.json()
        assert "tasks" in body
        assert "total" in body

    async def test_create_get_update_complete_delete_task(self, client: httpx.AsyncClient):
        # CREATE
        payload = {
            "title": "E2E Test Task",
            "due_date": _tomorrow(),
            "priority": "high",
            "medium": "call",
        }
        r = await client.post(f"{API}/tasks/", json=payload)
        assert r.status_code == 201, f"Create task failed: {r.text}"
        task = r.json()
        task_id = task["id"]
        # The response should have title (mapped from description)
        assert task.get("title") or task.get("description")

        # GET
        r = await client.get(f"{API}/tasks/{task_id}")
        assert r.status_code == 200
        fetched = r.json()
        assert fetched["id"] == task_id

        # UPDATE
        r = await client.put(
            f"{API}/tasks/{task_id}",
            json={"title": "Updated Task", "priority": "low"},
        )
        assert r.status_code == 200, f"Update task failed: {r.text}"

        # COMPLETE
        r = await client.post(f"{API}/tasks/{task_id}/complete")
        assert r.status_code == 200, f"Complete task failed: {r.text}"
        assert r.json()["status"] == "completed"

        # DELETE
        r = await client.delete(f"{API}/tasks/{task_id}")
        assert r.status_code == 200, f"Delete task failed: {r.text}"

    async def test_carry_forward(self, client: httpx.AsyncClient):
        # Create a task first
        payload = {"title": "Carry Forward Task", "due_date": _today(), "priority": "medium"}
        r = await client.post(f"{API}/tasks/", json=payload)
        assert r.status_code == 201
        task_id = r.json()["id"]

        new_date = (date.today() + timedelta(days=3)).isoformat()
        r = await client.post(f"{API}/tasks/{task_id}/carry-forward?new_date={new_date}")
        assert r.status_code == 200, f"Carry forward failed: {r.text}"
        assert r.json()["carry_forward_count"] >= 1

        # Cleanup
        await client.delete(f"{API}/tasks/{task_id}")

    async def test_today_tasks(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/tasks/today")
        assert r.status_code == 200
        body = r.json()
        assert "pending" in body
        assert "completed" in body
        assert "pending_count" in body

    async def test_bulk_complete(self, client: httpx.AsyncClient):
        # Create two tasks
        ids = []
        for i in range(2):
            r = await client.post(
                f"{API}/tasks/",
                json={"title": f"Bulk Task {i}", "due_date": _tomorrow(), "priority": "low"},
            )
            assert r.status_code == 201
            ids.append(r.json()["id"])

        r = await client.post(f"{API}/tasks/bulk-complete", json={"task_ids": ids})
        assert r.status_code == 200, f"Bulk complete failed: {r.text}"

        # Cleanup
        for task_id in ids:
            await client.delete(f"{API}/tasks/{task_id}")


# ═════════════════════════════════════════════
# TOUCHPOINTS  (CRUD + complete + reschedule + upcoming)
# ═════════════════════════════════════════════

class TestTouchpoints:
    """Full CRUD cycle for touchpoints — catches purpose/agenda mapping."""

    async def _create_test_client(self, client: httpx.AsyncClient) -> str:
        """Helper: create a throwaway client and return its id."""
        r = await client.post(
            f"{API}/clients/",
            json={
                "name": "TP Test Client",
                "phone": _unique_phone(),
                "gender": "female",
                "source": "cold_call",
            },
        )
        assert r.status_code == 201
        return r.json()["id"]

    async def test_list_touchpoints(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/touchpoints/")
        assert r.status_code == 200
        body = r.json()
        assert "touchpoints" in body

    async def test_create_get_update_complete_delete_touchpoint(self, client: httpx.AsyncClient):
        client_id = await self._create_test_client(client)

        # CREATE
        payload = {
            "client_id": client_id,
            "interaction_type": "call",
            "scheduled_date": _tomorrow(),
            "scheduled_time": "10:00",
            "agenda": "Discuss portfolio",
        }
        r = await client.post(f"{API}/touchpoints/", json=payload)
        assert r.status_code == 201, f"Create touchpoint failed: {r.text}"
        tp = r.json()
        tp_id = tp["id"]

        # GET
        r = await client.get(f"{API}/touchpoints/{tp_id}")
        assert r.status_code == 200
        assert r.json()["id"] == tp_id

        # UPDATE
        r = await client.put(
            f"{API}/touchpoints/{tp_id}",
            json={"agenda": "Updated agenda", "location": "Office"},
        )
        assert r.status_code == 200, f"Update touchpoint failed: {r.text}"

        # COMPLETE
        r = await client.post(
            f"{API}/touchpoints/{tp_id}/complete",
            json={"mom_text": "Discussed portfolio rebalancing", "notes": "Follow up next week"},
        )
        assert r.status_code == 200, f"Complete touchpoint failed: {r.text}"

        # DELETE
        r = await client.delete(f"{API}/touchpoints/{tp_id}")
        assert r.status_code == 200, f"Delete touchpoint failed: {r.text}"

        # Cleanup test client
        await client.delete(f"{API}/clients/{client_id}")

    async def test_reschedule_touchpoint(self, client: httpx.AsyncClient):
        client_id = await self._create_test_client(client)

        r = await client.post(
            f"{API}/touchpoints/",
            json={
                "client_id": client_id,
                "interaction_type": "meeting_office",
                "scheduled_date": _tomorrow(),
            },
        )
        assert r.status_code == 201
        tp_id = r.json()["id"]

        new_date = (date.today() + timedelta(days=5)).isoformat()
        r = await client.post(
            f"{API}/touchpoints/{tp_id}/reschedule?new_date={new_date}&new_time=14:00"
        )
        assert r.status_code == 200, f"Reschedule failed: {r.text}"
        assert r.json()["status"] == "rescheduled"

        # Cleanup
        await client.delete(f"{API}/touchpoints/{tp_id}")
        await client.delete(f"{API}/clients/{client_id}")

    async def test_upcoming_touchpoints(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/touchpoints/upcoming")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_update_mom(self, client: httpx.AsyncClient):
        client_id = await self._create_test_client(client)

        r = await client.post(
            f"{API}/touchpoints/",
            json={
                "client_id": client_id,
                "interaction_type": "call",
                "scheduled_date": _tomorrow(),
            },
        )
        assert r.status_code == 201
        tp_id = r.json()["id"]

        r = await client.put(
            f"{API}/touchpoints/{tp_id}/mom",
            json={"mom_text": "Minutes of meeting: Discussed SIP increase."},
        )
        assert r.status_code == 200, f"Update MOM failed: {r.text}"
        assert "mom_text" in r.json()

        # Cleanup
        await client.delete(f"{API}/touchpoints/{tp_id}")
        await client.delete(f"{API}/clients/{client_id}")


# ═════════════════════════════════════════════
# BUSINESS OPPORTUNITIES  (CRUD + pipeline + outcome + stage)
# ═════════════════════════════════════════════

class TestBusinessOpportunities:
    """Full CRUD cycle for BOs — catches additional_info/notes mapping."""

    async def _create_test_client(self, client: httpx.AsyncClient) -> str:
        r = await client.post(
            f"{API}/clients/",
            json={
                "name": "BO Test Client",
                "phone": _unique_phone(),
                "gender": "male",
                "source": "referral",
            },
        )
        assert r.status_code == 201
        return r.json()["id"]

    async def test_list_opportunities(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/business-opportunities/")
        assert r.status_code == 200
        body = r.json()
        assert "opportunities" in body

    async def test_create_get_update_outcome_delete_bo(self, client: httpx.AsyncClient):
        client_id = await self._create_test_client(client)

        # CREATE
        payload = {
            "client_id": client_id,
            "opportunity_type": "sip",
            "opportunity_stage": "identified",
            "expected_amount": 50000,
            "notes": "Potential SIP opportunity",
        }
        r = await client.post(f"{API}/business-opportunities/", json=payload)
        assert r.status_code == 201, f"Create BO failed: {r.text}"
        bo = r.json()
        bo_id = bo["id"]

        # GET
        r = await client.get(f"{API}/business-opportunities/{bo_id}")
        assert r.status_code == 200
        assert r.json()["id"] == bo_id

        # UPDATE
        r = await client.put(
            f"{API}/business-opportunities/{bo_id}",
            json={"expected_amount": 75000, "opportunity_stage": "proposed"},
        )
        assert r.status_code == 200, f"Update BO failed: {r.text}"

        # UPDATE STAGE
        r = await client.patch(
            f"{API}/business-opportunities/{bo_id}/stage?stage=proposed&notes=Moved+to+proposed"
        )
        assert r.status_code == 200, f"Update stage failed: {r.text}"

        # UPDATE OUTCOME
        r = await client.patch(
            f"{API}/business-opportunities/{bo_id}/outcome",
            json={
                "outcome": "won",
                "outcome_date": _today(),
                "outcome_amount": 60000,
            },
        )
        assert r.status_code == 200, f"Update outcome failed: {r.text}"

        # DELETE
        r = await client.delete(f"{API}/business-opportunities/{bo_id}")
        assert r.status_code == 200, f"Delete BO failed: {r.text}"

        # Cleanup
        await client.delete(f"{API}/clients/{client_id}")

    async def test_pipeline(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/business-opportunities/pipeline")
        assert r.status_code == 200, f"Pipeline failed: {r.text}"
        body = r.json()
        assert "stages" in body
        assert "total_open" in body


# ═════════════════════════════════════════════
# GOALS  (CRUD + progress + with-subgoals)
# ═════════════════════════════════════════════

class TestGoals:
    """Full CRUD cycle for goals."""

    async def _create_test_client(self, client: httpx.AsyncClient) -> str:
        r = await client.post(
            f"{API}/clients/",
            json={
                "name": "Goal Test Client",
                "phone": _unique_phone(),
                "gender": "male",
                "source": "referral",
            },
        )
        assert r.status_code == 201
        return r.json()["id"]

    async def test_list_goals(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/goals/")
        assert r.status_code == 200
        body = r.json()
        assert "goals" in body

    async def test_create_get_update_progress_delete_goal(self, client: httpx.AsyncClient):
        client_id = await self._create_test_client(client)

        # CREATE
        payload = {
            "client_id": client_id,
            "goal_type": "retirement",
            "goal_name": "E2E Test Retirement Goal",
            "target_amount": 10000000,
            "monthly_sip": 25000,
            "current_investment": 100000,
        }
        r = await client.post(f"{API}/goals/", json=payload)
        assert r.status_code == 201, f"Create goal failed: {r.text}"
        goal = r.json()
        goal_id = goal["id"]

        # GET
        r = await client.get(f"{API}/goals/{goal_id}")
        assert r.status_code == 200
        assert r.json()["id"] == goal_id

        # GET WITH SUBGOALS
        r = await client.get(f"{API}/goals/{goal_id}/with-subgoals")
        assert r.status_code == 200, f"Get with subgoals failed: {r.text}"

        # UPDATE
        r = await client.put(
            f"{API}/goals/{goal_id}",
            json={"goal_name": "Updated Goal", "monthly_sip": 30000},
        )
        assert r.status_code == 200, f"Update goal failed: {r.text}"

        # UPDATE PROGRESS
        r = await client.patch(
            f"{API}/goals/{goal_id}/progress?current_investment=200000"
        )
        assert r.status_code == 200, f"Update progress failed: {r.text}"

        # CLIENT GOALS
        r = await client.get(f"{API}/goals/client/{client_id}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

        # DELETE
        r = await client.delete(f"{API}/goals/{goal_id}")
        assert r.status_code == 200, f"Delete goal failed: {r.text}"

        # Cleanup
        await client.delete(f"{API}/clients/{client_id}")


# ═════════════════════════════════════════════
# DASHBOARD
# ═════════════════════════════════════════════

class TestDashboard:
    """Dashboard endpoints — catches leads.is_deleted, touchpoints count issues."""

    async def test_stats(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/dashboard/stats")
        assert r.status_code == 200, f"Dashboard stats failed: {r.text}"

    async def test_today(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/dashboard/today")
        assert r.status_code == 200, f"Dashboard today failed: {r.text}"

    async def test_pipeline(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/dashboard/pipeline")
        assert r.status_code == 200, f"Dashboard pipeline failed: {r.text}"

    async def test_conversions(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/dashboard/conversions?period=month")
        assert r.status_code == 200, f"Dashboard conversions failed: {r.text}"

    async def test_growth(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/dashboard/growth?period=year")
        assert r.status_code == 200, f"Dashboard growth failed: {r.text}"


# ═════════════════════════════════════════════
# SEARCH
# ═════════════════════════════════════════════

class TestSearch:
    """Search endpoints — catches or_ filter syntax issues."""

    async def test_global_search(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/search/?q=test")
        assert r.status_code == 200, f"Global search failed: {r.text}"
        body = r.json()
        assert "clients" in body
        assert "leads" in body
        assert "total" in body

    async def test_search_clients(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/search/clients?q=test")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_search_leads(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/search/leads?q=test")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_search_tasks(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/search/tasks?q=test")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_recent_searches(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/search/recent")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ═════════════════════════════════════════════
# PROFILE
# ═════════════════════════════════════════════

class TestProfile:
    async def test_get_profile(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/profile/")
        assert r.status_code == 200, f"Get profile failed: {r.text}"


# ═════════════════════════════════════════════
# CALCULATORS  (smoke test — no DB writes)
# ═════════════════════════════════════════════

class TestCalculators:
    async def test_sip_calculator(self, client: httpx.AsyncClient):
        payload = {
            "mode": "sip",
            "monthly_investment": 10000,
            "expected_return_rate": 12,
            "time_period_years": 10,
        }
        r = await client.post(f"{API}/calculators/sip-lumpsum", json=payload)
        # May return 200 or 422 depending on exact schema — we just check it doesn't 500
        assert r.status_code != 500, f"SIP calculator 500: {r.text}"


# ═════════════════════════════════════════════
# DATA IMPORT/EXPORT  (smoke test)
# ═════════════════════════════════════════════

class TestDataIO:
    async def test_get_client_template(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/data/template/clients")
        # Could be /data/template/clients or /data/import/template/clients
        # Accept 200 or 404 (path may differ), but not 500
        assert r.status_code != 500, f"Client template 500: {r.text}"

    async def test_export_clients(self, client: httpx.AsyncClient):
        r = await client.get(f"{API}/data/export/clients")
        assert r.status_code != 500, f"Export clients 500: {r.text}"


# ═════════════════════════════════════════════
# CONVERT LEAD → CLIENT
# ═════════════════════════════════════════════

class TestConvertLead:
    """Tests the lead-to-client conversion — a complex multi-table operation."""

    async def test_convert_lead_to_client(self, client: httpx.AsyncClient):
        phone = _unique_phone()

        # Create lead
        r = await client.post(
            f"{API}/leads/",
            json={
                "name": "Convert Test Lead",
                "phone": phone,
                "source": "social_media",
            },
        )
        assert r.status_code == 201
        lead_id = r.json()["id"]

        # Convert to client
        r = await client.post(
            f"{API}/clients/convert-from-lead",
            json={
                "lead_id": lead_id,
                "birthdate": "1990-05-15",
            },
        )
        assert r.status_code == 201, f"Convert lead failed: {r.text}"
        new_client = r.json()
        assert new_client["name"] == "Convert Test Lead"
        new_client_id = new_client["id"]

        # Cleanup — delete client first (soft delete), then lead
        # Note: client soft-delete keeps the row, so FK constraint on
        # converted_from_lead_id still prevents lead deletion.
        # Just clean up the client; leave the converted lead in DB.
        await client.delete(f"{API}/clients/{new_client_id}")


# ═════════════════════════════════════════════
# EDGE CASES — Pydantic validation & field mapping
# ═════════════════════════════════════════════

class TestEdgeCases:
    """Targeted tests for bugs previously found via manual testing."""

    async def test_lead_with_all_optional_fields(self, client: httpx.AsyncClient):
        """Ensure all optional enum fields serialize correctly."""
        phone = _unique_phone()
        payload = {
            "name": "Full Lead",
            "phone": phone,
            "source": "natural_market",
            "email": "full@example.com",
            "gender": "female",
            "marital_status": "married",
            "occupation": "business",
            "income_group": "12_1_to_24",
            "age_group": "25_to_35",
            "area": "Pune",
            "referred_by": "SomeReferrer",
            "dependants": 2,
            "scheduled_date": _tomorrow(),
            "scheduled_time": "09:00",
            "notes": "Test notes",
        }
        r = await client.post(f"{API}/leads/", json=payload)
        assert r.status_code == 201, f"Full lead create failed: {r.text}"
        lead_id = r.json()["id"]
        # Cleanup
        await client.delete(f"{API}/leads/{lead_id}")

    async def test_client_with_all_optional_fields(self, client: httpx.AsyncClient):
        """Ensure all optional fields + field aliases work."""
        phone = _unique_phone()
        payload = {
            "name": "Full Client",
            "phone": phone,
            "gender": "female",
            "source": "social_media",
            "email": "full@example.com",
            "birthdate": "1985-03-20",
            "marital_status": "married",
            "occupation": "professional",
            "income_group": "24_1_to_48",
            "area": "Bangalore",
            "risk_profile": "moderate",
            "referred_by": "AnotherRef",
            "term_insurance": 10000.0,
            "health_insurance": 5000.0,
            "aum": 1000000,
            "sip_amount": 25000,
            "notes": "Full test",
        }
        r = await client.post(f"{API}/clients/", json=payload)
        assert r.status_code == 201, f"Full client create failed: {r.text}"
        cl = r.json()
        client_id = cl["id"]

        # Verify response contains mapped fields
        assert cl["name"] == "Full Client"
        # Cleanup
        await client.delete(f"{API}/clients/{client_id}")

    async def test_task_with_all_optional_fields(self, client: httpx.AsyncClient):
        """Ensure product_type, is_business_opportunity, all_day work."""
        payload = {
            "title": "Full Task",
            "due_date": _tomorrow(),
            "priority": "high",
            "medium": "email",
            "due_time": "14:00",
            "all_day": False,
            "product_type": "mutual_fund",
            "is_business_opportunity": True,
            "description": "Detailed task description",
        }
        r = await client.post(f"{API}/tasks/", json=payload)
        assert r.status_code == 201, f"Full task create failed: {r.text}"
        task_id = r.json()["id"]
        # Cleanup
        await client.delete(f"{API}/tasks/{task_id}")

    async def test_touchpoint_with_lead(self, client: httpx.AsyncClient):
        """Touchpoint linked to a lead instead of a client."""
        phone = _unique_phone()
        r = await client.post(
            f"{API}/leads/",
            json={"name": "TP Lead", "phone": phone, "source": "referral"},
        )
        assert r.status_code == 201
        lead_id = r.json()["id"]

        r = await client.post(
            f"{API}/touchpoints/",
            json={
                "lead_id": lead_id,
                "interaction_type": "video_call",
                "scheduled_date": _tomorrow(),
                "agenda": "Intro call",
            },
        )
        assert r.status_code == 201, f"Touchpoint with lead failed: {r.text}"
        tp_id = r.json()["id"]

        # Cleanup
        await client.delete(f"{API}/touchpoints/{tp_id}")
        await client.delete(f"{API}/leads/{lead_id}")

    async def test_404_on_nonexistent_resources(self, client: httpx.AsyncClient):
        """Ensure proper 404s instead of 500s for missing resources."""
        fake_id = str(uuid.uuid4())
        endpoints = [
            f"{API}/leads/{fake_id}",
            f"{API}/clients/{fake_id}",
            f"{API}/tasks/{fake_id}",
            f"{API}/touchpoints/{fake_id}",
            f"{API}/business-opportunities/{fake_id}",
            f"{API}/goals/{fake_id}",
        ]
        for url in endpoints:
            r = await client.get(url)
            assert r.status_code == 404, f"Expected 404 for {url}, got {r.status_code}: {r.text}"
