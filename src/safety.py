import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .config import LOG_DIR

ALLOWED_ACTIONS = {
    "add_expense",
    "list_expenses",
    "summarize_expenses",
    "add_bill",
    "list_bills",
    "summarize_bills",
    "generate_report_file",
    "delete_expense",
    "mark_bill_paid",
    "plan_savings_goal",
    "spending_health_check",
}

DESTRUCTIVE_ACTIONS = {
    "delete_expense",
    "mark_bill_paid",
}


def validate_actions(actions: List[Dict[str, Any]]) -> None:
    for action in actions:
        atype = action.get("type")
        if atype not in ALLOWED_ACTIONS:
            raise ValueError(f"Action type not allowed: {atype}")


def actions_require_confirmation(actions: List[Dict[str, Any]]) -> bool:
    for action in actions:
        if action.get("type") in DESTRUCTIVE_ACTIONS:
            return True
    return False


def log_actions(user_text: str, actions: List[Dict[str, Any]]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
        "user_text": user_text,
        "actions": actions,
    }
    log_file: Path = LOG_DIR / "agent.log"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
