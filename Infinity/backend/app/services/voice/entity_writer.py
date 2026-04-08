"""
Entity Writer — config-driven intent → Supabase table routing.
Matches existing service behavior (original_date for tasks, etc.)
"""

from datetime import datetime, timedelta

from app.database import supabase
from app.utils.voice_logger import log_event
from app.database import supabase_admin as supabase

INTENT_CONFIG = {
    "schedule_touchpoint": {
        "table": "touchpoints",
        "required_entity_fields": [],
        "field_mapping": {
            "client_id": "client_id",
            "interaction_type": ("interaction_type", "meeting_office"),
            "location": "location",
            "purpose": "purpose",
            "scheduled_date": "scheduled_date",
            "scheduled_time": "scheduled_time",
        },
        "defaults": {"status": "scheduled"},
    },
    "create_task": {
        "table": "tasks",
        "required_entity_fields": [],
        "field_mapping": {
            "client_id": "client_id",
            "description": ("description", ""),
            "medium": "medium",
            "product_type": "product_type",
            "priority": ("priority", "medium"),
            "due_date": "due_date",
            "due_time": "due_time",
        },
        "defaults": {"status": "pending"},
    },
    "create_business_opportunity": {
        "table": "business_opportunities",
        "required_entity_fields": [],
        "field_mapping": {
            "client_id": "client_id",
            "opportunity_type": ("opportunity_type", "sip"),
            "expected_amount": "expected_amount",
            "opportunity_source": ("opportunity_source", "client_servicing"),
            "additional_info": "additional_info",
            "due_date": "due_date",
            "due_time": "due_time",
        },
        "defaults": {},
    },
    "add_lead": {
        "table": "leads",
        "required_entity_fields": [],
        "field_mapping": {
            "name": ("name", "Unknown"),
            "phone": "phone",
            "email": "email",
            "area": "area",
            "age_group": "age_group",
            "gender": "gender",
            "occupation": "occupation",
            "income_group": "income_group",
            "source": ("source", "referral"),
            "source_description": "source_description",
            "sourced_by": "sourced_by",
            "notes": "notes",
            "scheduled_date": "scheduled_date",
        },
        "defaults": {"status": "follow_up"},
    },
}


def _build_insert_payload(
    config: dict,
    user_id: str,
    entities: dict,
) -> dict:
    payload = {"user_id": user_id}

    for db_column, mapping in config["field_mapping"].items():
        if isinstance(mapping, tuple):
            entity_key, default = mapping
            value = entities.get(entity_key, default)
        else:
            entity_key = mapping
            value = entities.get(entity_key)

        if value is not None:
            payload[db_column] = value

    for key, value in config.get("defaults", {}).items():
        if key not in payload:
            payload[key] = value

    # ── Match existing service behavior ──

    # Task: set original_date = due_date (task_service.py does this)
    if config["table"] == "tasks" and payload.get("due_date"):
        payload["original_date"] = payload["due_date"]

    # BO: default due_date to 7 days from now if missing
    if config["table"] == "business_opportunities" and not payload.get("due_date"):
        payload["due_date"] = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    # BO: ensure opportunity_source is set (bo_service.py does this)
    if config["table"] == "business_opportunities" and not payload.get("opportunity_source"):
        payload["opportunity_source"] = "client_servicing"

    return payload


def write_entity(
    intent: str,
    user_id: str,
    entities: dict,
    trace_id: str,
) -> tuple[str, str]:
    config = INTENT_CONFIG.get(intent)
    if not config:
        raise ValueError(f"No config for intent: {intent}")

    for field in config["required_entity_fields"]:
        if not entities.get(field):
            raise ValueError(f"Missing required field '{field}' for intent '{intent}'")

    payload = _build_insert_payload(config, user_id, entities)

    result = supabase.table(config["table"]).insert(payload).execute()
    entity_id = result.data[0]["id"]
    entity_type = config["table"]

    log_event(trace_id, "entity_write", f"{entity_type}_created", entity_id=entity_id)

    return entity_type, entity_id