from typing import Any, Dict

from .llm_client import get_actions_from_llm
from .actions import execute_actions
from .safety import (
    actions_require_confirmation,
    log_actions,
    validate_actions,
)


def handle_user_input(user_text: str, *, ask_confirmation: bool = True) -> Dict[str, Any]:
    plan, actions = get_actions_from_llm(user_text)

    validate_actions(actions)

    if ask_confirmation and actions_require_confirmation(actions):
        print("[WARNING] There are potentially destructive actions in this plan.")
        ans = input("Are you sure you want to continue? (yes/no): ").strip().lower()
        if ans not in ("y", "yes"):
            return {
                "plan": plan + " (CANCELLED because the user did not confirm).",
                "results": ["Execution cancelled by user."],
            }

    log_actions(user_text, actions)
    results = execute_actions(actions)
    return {"plan": plan, "results": results}
