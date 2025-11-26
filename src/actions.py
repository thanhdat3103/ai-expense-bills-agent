from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List

from . import db
from .config import REPORTS_DIR


def execute_actions(actions: List[Dict[str, Any]]) -> List[str]:
    results: List[str] = []

    for action in actions:
        atype = action.get("type")
        params: Dict[str, Any] = action.get("params") or {}

        if atype == "add_expense":
            results.append(_handle_add_expense(params))
        elif atype == "list_expenses":
            results.append(_handle_list_expenses(params))
        elif atype == "summarize_expenses":
            results.append(_handle_summarize_expenses(params))
        elif atype == "add_bill":
            results.append(_handle_add_bill(params))
        elif atype == "list_bills":
            results.append(_handle_list_bills(params))
        elif atype == "summarize_bills":
            results.append(_handle_summarize_bills(params))
        elif atype == "generate_report_file":
            results.append(_handle_generate_report_file(params))
        elif atype == "delete_expense":
            results.append(_handle_delete_expense(params))
        elif atype == "mark_bill_paid":
            results.append(_handle_mark_bill_paid(params))
        elif atype == "plan_savings_goal":
            results.append(_handle_plan_savings_goal(params))
        elif atype == "spending_health_check":
            results.append(_handle_spending_health_check(params))
        else:
            results.append(f"Skipping unsupported action type: {atype}")

    return results


def _handle_add_expense(params: Dict[str, Any]) -> str:
    amount = float(params.get("amount", 0))
    currency = params.get("currency", "VND")
    category = params.get("category")
    description = params.get("description")
    date_str = params.get("date")

    expense_id = db.add_expense(
        amount=amount,
        currency=currency,
        category=category,
        description=description,
        date_str=date_str,
    )
    return (
        f"Added expense #{expense_id}: {amount} {currency}, "
        f"category='{category}', description='{description}'."
    )


def _handle_list_expenses(params: Dict[str, Any]) -> str:
    limit = int(params.get("limit", 10))
    rows = db.list_expenses(limit=limit)

    if not rows:
        return "There are currently no recorded expenses."

    lines = ["Recent expenses:"]
    for r in rows:
        lines.append(
            f"- #{r['id']} | {r['date']} | {r['amount']} {r['currency']} | "
            f"{r['category'] or 'N/A'} | {r['description'] or ''}"
        )
    return "\n".join(lines)


def _handle_summarize_expenses(params: Dict[str, Any]) -> str:
    period = params.get("period", "this_month")
    rows = db.get_expenses(period=period, start_date=None, end_date=None)

    if not rows:
        return f"No expenses found for period '{period}'."

    total = 0.0
    by_category: Dict[str, float] = {}

    for r in rows:
        amt = float(r["amount"])
        total += amt
        cat = r["category"] or "Other"
        by_category[cat] = by_category.get(cat, 0.0) + amt

    lines = [
        f"Expense summary (period='{period}'):" ,
        f"- Number of expenses: {len(rows)}",
        f"- Total amount: {total:.0f} VND",
        "- By category:",
    ]
    for cat, value in by_category.items():
        lines.append(f"  * {cat}: {value:.0f} VND")
    return "\n".join(lines)


def _handle_add_bill(params: Dict[str, Any]) -> str:
    name = params.get("name") or "Bill"
    amount = float(params.get("amount", 0))
    currency = params.get("currency", "VND")
    due_date = params.get("due_date") or ""
    notes = params.get("notes")

    bill_id = db.add_bill(
        name=name, amount=amount, currency=currency, due_date=due_date, notes=notes
    )
    return f"Added bill #{bill_id}: {name}, {amount} {currency}, due {due_date}."


def _handle_list_bills(params: Dict[str, Any]) -> str:
    include_paid = bool(params.get("include_paid", False))
    rows = db.list_bills(include_paid=include_paid)

    if not rows:
        if include_paid:
            return "There are no bills in the system."
        return "There are no unpaid bills."

    lines = ["Bills:"]
    for r in rows:
        status = "Paid" if r["is_paid"] else "Unpaid"
        lines.append(
            f"- #{r['id']} | {r['name']} | {r['amount']} {r['currency']} | "
            f"Due: {r['due_date']} | {status}"
        )
    return "\n".join(lines)


def _handle_summarize_bills(params: Dict[str, Any]) -> str:
    include_paid = bool(params.get("include_paid", False))
    rows = db.list_bills(include_paid=include_paid)

    if not rows:
        return "There are no bills to summarize."

    total = 0.0
    unpaid_count = 0
    for r in rows:
        total += float(r["amount"])
        if not r["is_paid"]:
            unpaid_count += 1

    lines = [
        "Bill summary:",
        f"- Total bills (include_paid={include_paid}): {len(rows)}",
        f"- Total amount (all bills): {total:.0f} VND",
        f"- Number of unpaid bills: {unpaid_count}",
    ]
    return "\n".join(lines)


def _handle_generate_report_file(params: Dict[str, Any]) -> str:
    period = params.get("period", "this_month")
    rows = db.get_expenses(period=period, start_date=None, end_date=None)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path: Path = REPORTS_DIR / f"expense_report_{period}.md"

    with report_path.open("w", encoding="utf-8") as f:
        f.write(f"# Expense Report - {period}\n\n")
        if not rows:
            f.write("_No expenses found for this period._\n")
        else:
            total = sum(float(r["amount"]) for r in rows)
            f.write(f"- Number of expenses: {len(rows)}\n")
            f.write(f"- Total amount: {total:.0f} VND\n\n")
            f.write("## Details\n\n")
            for r in rows:
                f.write(
                    f"- {r['date']}: {r['amount']} {r['currency']} | "
                    f"{r['category'] or 'N/A'} | "
                    f"{r['description'] or ''}\n"
                )
    return f"Created report at: {report_path}"


def _handle_delete_expense(params: Dict[str, Any]) -> str:
    expense_id = int(params.get("expense_id", 0))
    if expense_id <= 0:
        return "Cannot delete expense: invalid or missing expense_id."

    deleted = db.delete_expense(expense_id)
    if not deleted:
        return f"Expense #{expense_id} does not exist. Nothing was deleted."
    return f"Deleted expense #{expense_id}."


def _handle_mark_bill_paid(params: Dict[str, Any]) -> str:
    bill_id = int(params.get("bill_id", 0))
    if bill_id <= 0:
        return "Cannot mark bill as paid: invalid or missing bill_id."

    updated = db.mark_bill_paid(bill_id)
    if not updated:
        return f"Bill #{bill_id} either does not exist or is already marked as paid."
    return f"Marked bill #{bill_id} as paid."


def _handle_plan_savings_goal(params: Dict[str, Any]) -> str:
    target = float(params.get("target_amount", 0))
    current = float(params.get("current_savings", 0))
    deadline_str = params.get("deadline")

    if not deadline_str:
        return "Savings goal plan: missing deadline date (YYYY-MM-DD)."

    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
    except ValueError:
        return "Savings goal plan: invalid deadline format, expected YYYY-MM-DD."

    today = date.today()
    if deadline <= today:
        return "Savings goal plan: deadline is in the past or today; cannot compute a forward-looking plan."

    remaining = max(target - current, 0.0)
    days_left = (deadline - today).days
    months_left = max(days_left / 30.0, 0.1)
    weeks_left = days_left / 7.0

    per_month = remaining / months_left
    per_week = remaining / weeks_left if weeks_left > 0 else remaining
    per_day = remaining / days_left if days_left > 0 else remaining

    lines = [
        "Savings goal plan:",
        f"- Target amount: {target:.0f} VND",
        f"- Current savings: {current:.0f} VND",
        f"- Remaining amount: {remaining:.0f} VND",
        f"- Deadline: {deadline_str} (in {days_left} days)",
        f"- Suggested saving per month: {per_month:.0f} VND",
        f"- Suggested saving per week: {per_week:.0f} VND",
        f"- Suggested saving per day: {per_day:.0f} VND",
    ]

    if per_month <= 0:
        lines.append("- You already reached or exceeded the target amount!")
    elif per_month > target * 0.5:
        lines.append(
            "- Warning: required monthly saving is very high compared to the target; "
            "you may need to extend the deadline or lower the goal."
        )
    return "\n".join(lines)


def _handle_spending_health_check(params: Dict[str, Any]) -> str:
    period = params.get("period", "this_month")
    rows = db.get_expenses(period=period, start_date=None, end_date=None)

    if not rows:
        return f"Spending health check: no expenses found for period '{period}'."

    NEEDS_CATS = {
        "Food", "Groceries", "Rent", "Housing", "Utilities", "Electricity",
        "Water", "Internet", "Transport", "Transportation", "Healthcare",
        "Medicine", "Insurance"
    }
    WANTS_CATS = {
        "Entertainment", "Shopping", "Travel", "Games", "Dining Out",
        "Coffee", "Movies"
    }

    total = 0.0
    needs = 0.0
    wants = 0.0

    for r in rows:
        amt = float(r["amount"])
        total += amt
        cat_raw = (r["category"] or "").strip()
        cat = cat_raw.title()

        if cat in NEEDS_CATS:
            needs += amt
        elif cat in WANTS_CATS:
            wants += amt

    other = max(total - needs - wants, 0.0)

    def pct(x: float) -> float:
        return (x / total * 100.0) if total > 0 else 0.0

    needs_pct = pct(needs)
    wants_pct = pct(wants)
    other_pct = pct(other)

    lines = [
        f"Spending health check (period='{period}')",
        f"- Total spending: {total:.0f} VND",
        f"- Needs: {needs:.0f} VND ({needs_pct:.1f}%)",
        f"- Wants: {wants:.0f} VND ({wants_pct:.1f}%)",
        f"- Other: {other:.0f} VND ({other_pct:.1f}%)",
        "",
        "Guideline (50/30/20 rule):",
        "- Needs ~ 50% of income, Wants ~ 30%, Savings/Debt repayment ~ 20%.",
    ]

    if needs_pct > 55:
        lines.append("- Your Needs spending is above 50%. Consider optimising fixed costs if possible.")
    elif needs_pct < 40:
        lines.append("- Your Needs spending is relatively low; this may allow more room for savings.")

    if wants_pct > 35:
        lines.append("- Your Wants spending is quite high. You may want to reduce optional purchases.")
    elif wants_pct < 20:
        lines.append("- Your Wants spending is modest; good job keeping lifestyle expenses under control.")

    lines.append(
        "- Note: this is a rough check based only on recorded expenses; "
        "it does not include your savings or income information."
    )
    return "\n".join(lines)
