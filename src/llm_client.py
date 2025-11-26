import json
import re
import time
from datetime import date
from typing import Any, Dict, List, Tuple

from google.api_core.exceptions import ResourceExhausted, GoogleAPIError

from .config import MODEL


SYSTEM_PROMPT = """
You are an AI planner for a Personal Expense & Bills Management Agent.

Your job: read the user's natural language request (in English or Vietnamese)
and respond with a **single JSON object** that describes a plan and an action list.

The JSON MUST have the structure:

{
  "plan": "short description of how you will handle the user's request (in English)",
  "actions": [
    {
      "type": "add_expense" | "list_expenses" | "summarize_expenses" |
              "add_bill"    | "list_bills"    | "summarize_bills"    |
              "generate_report_file" | "delete_expense" | "mark_bill_paid" |
              "plan_savings_goal" | "spending_health_check",
      "params": { ... }
    },
    ...
  ]
}

DO NOT return any free-form text outside the JSON.
""".strip()


DETAIL_PROMPT = """
Action details:

1) add_expense
   - Insert a new expense entry.
   - params:
     - amount: float, amount of money (default currency is VND if not specified)
     - currency: string, e.g. "VND" or "USD" (default "VND")
     - category: string category, e.g. "Food", "Transport", "Entertainment"
     - description: short text description
     - date: date string in format YYYY-MM-DD
       If the user does not specify, infer "today" (you must still output a YYYY-MM-DD string).

2) list_expenses
   - List recent expenses.
   - params:
     - limit: integer number of rows (default 10)

3) summarize_expenses
   - Summarize expenses for a given time period.
   - params:
     - period: one of "today" | "this_week" | "this_month" | "all"

4) add_bill
   - Insert a new bill that should be paid in the future.
   - params:
     - name: bill name (e.g. "Electricity")
     - amount: float
     - currency: string, default "VND"
     - due_date: date string YYYY-MM-DD
     - notes: optional additional notes (can be null)

5) list_bills
   - List bills.
   - params:
     - include_paid: boolean (default false) – if false, only unpaid bills are listed.

6) summarize_bills
   - Summarize information about bills.
   - params:
     - include_paid: boolean (default false)

7) generate_report_file
   - Request a Markdown expense report file to be created.
   - params:
     - period: one of "today" | "this_week" | "this_month" | "all"

8) delete_expense  (DESTRUCTIVE)
   - Delete an expense by its ID.
   - params:
     - expense_id: integer ID of the expense to delete.

9) mark_bill_paid  (DESTRUCTIVE)
   - Mark a bill as paid.
   - params:
     - bill_id: integer ID of the bill to mark as paid.

10) plan_savings_goal
   - Plan how much the user should save each month/week/day to reach a goal.
   - params:
     - target_amount: float, total amount the user wants to have.
     - current_savings: float, how much the user already has (default 0).
     - deadline: date string YYYY-MM-DD, when the user wants to reach the goal.

11) spending_health_check
   - Analyse the user's spending pattern for a period and compare to a simple 50/30/20 rule.
   - params:
     - period: one of "today" | "this_week" | "this_month" | "all"

General rules:
- Only use the action types listed above. DO NOT invent new types.
- Always produce valid JSON.
- If the user request is clearly unrelated to expenses or bills, return:
  - a reasonable "plan" explaining that no actions will be executed, and
  - "actions": []

Example (savings goal):

User: "Help me save 20,000,000 VND by June 2026. I already have 5,000,000 VND."

Possible JSON response:

{
  "plan": "Calculate how much the user needs to save per month and per week to reach the savings goal.",
  "actions": [
    {
      "type": "plan_savings_goal",
      "params": {
        "target_amount": 20000000,
        "current_savings": 5000000,
        "deadline": "2026-06-01"
      }
    }
  ]
}
""".strip()


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("LLM output is not valid JSON and no JSON block could be extracted.")
        return json.loads(match.group(0))


def get_actions_from_llm(user_text: str) -> Tuple[str, List[Dict[str, Any]]]:
    today_str = date.today().isoformat()
    dynamic = (
        f"Today's date is {today_str}.\n"
        f"If the user says 'today', you MUST use exactly this date string ('{today_str}') "
        f"for any 'date' field.\n"
        f"For 'this_week' and 'this_month', you may infer ranges based on this date."
    )

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"{DETAIL_PROMPT}\n\n"
        f"{dynamic}\n\n"
        f"User request:\n{user_text}"
    )

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = MODEL.generate_content([prompt])
            break
        except ResourceExhausted as e:
            last_error = e
            time.sleep(2 * (attempt + 1))
            continue
        except GoogleAPIError as e:
            raise RuntimeError(f"LLM API error: {e.message}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected LLM error: {e}") from e
    else:
        raise RuntimeError("LLM rate limit exceeded, please wait and try again.") from last_error

    data = _extract_json(response.text)
    plan = data.get("plan", "")
    actions = data.get("actions", [])
    if not isinstance(actions, list):
        raise ValueError("The 'actions' field in LLM JSON output is not a list.")
    return plan, actions
