"""Checkpointed progress for modular pipeline stages."""
import json
import os
from datetime import datetime, timezone

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATE_PATH = os.path.join(PROJECT_DIR, "work", "state.json")


def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_state():
    if not os.path.exists(STATE_PATH):
        return {
            "current_stage": "idle",
            "map": None,
            "region": None,
            "status": "idle",
            "attempt": 0,
            "checkpoint": None,
            "last_successful_output": None,
            "last_error": None,
            "updated_at": _utc_now(),
        }
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(**kwargs):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    state = load_state()
    state.update(kwargs)
    state["updated_at"] = _utc_now()
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    return state
