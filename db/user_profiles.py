"""
User profile storage for Aly onboarding.
Each facilitator is identified by their WhatsApp number.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Optional

from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Singleton client — same pattern as SimpleMongoRAG
_client: Optional[MongoClient] = None
_profiles_col = None


def _get_collection():
    global _client, _profiles_col
    if _profiles_col is None:
        _client = MongoClient(os.getenv("MONGODB_URI"))
        db_name = os.getenv("MONGODB_DB_NAME", "puddle")
        _profiles_col = _client[db_name]["user_profiles"]
        # Unique index — safe to call on every startup (idempotent)
        _profiles_col.create_index("whatsapp_number", unique=True)
    return _profiles_col


# Onboarding state machine (linear order)
ONBOARDING_STATES = [
    "awaiting_name",
    "awaiting_gender",
    "awaiting_country",
    "awaiting_region",   # Colombia only — may be skipped
    "awaiting_email",
    "complete",
]


def get_user_profile(whatsapp_number: str) -> Optional[Dict]:
    """Returns full profile doc or None if not found."""
    col = _get_collection()
    return col.find_one({"whatsapp_number": whatsapp_number}, {"_id": 0})


def create_user_profile(whatsapp_number: str) -> Dict:
    """Creates a new profile at the start of onboarding."""
    col = _get_collection()
    now = datetime.utcnow()
    profile = {
        "whatsapp_number": whatsapp_number,
        "name": None,
        "gender_identity": None,
        "country": None,
        "region": None,
        "email": None,
        "onboarding_state": "awaiting_name",
        "created_at": now,
        "updated_at": now,
    }
    col.insert_one(profile)
    profile.pop("_id", None)
    return profile


def get_or_create_profile(whatsapp_number: str) -> Dict:
    """Fetch existing profile or create a new one."""
    profile = get_user_profile(whatsapp_number)
    if profile is None:
        profile = create_user_profile(whatsapp_number)
        logger.info(f"New user profile created: {whatsapp_number}")
    return profile


def update_onboarding_field(
    whatsapp_number: str,
    field: str,
    value: str,
    next_state: str,
) -> Dict:
    """
    Atomically updates a profile field and advances the onboarding_state.
    Uses find_one_and_update to avoid partial writes.
    Returns the updated profile.
    """
    col = _get_collection()
    updated = col.find_one_and_update(
        {"whatsapp_number": whatsapp_number},
        {
            "$set": {
                field: value,
                "onboarding_state": next_state,
                "updated_at": datetime.utcnow(),
            }
        },
        return_document=True,
    )
    if updated is None:
        raise ValueError(f"Profile not found for {whatsapp_number}")
    updated.pop("_id", None)
    return updated


def is_onboarding_complete(profile: Dict) -> bool:
    return profile.get("onboarding_state") == "complete"
