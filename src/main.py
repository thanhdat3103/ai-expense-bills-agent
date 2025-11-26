from . import db
from .agent import handle_user_input
from .config import LOG_DIR, REPORTS_DIR


HELP_TEXT = """Examples of commands you can try:

- Add an expense of 120000 VND for coffee with friends in entertainment category today.
- Show me a summary of my expenses for today.
- Summarize my expenses for this month.
- Add an electricity bill of 800000 VND due on 2025-12-10.
- List my unpaid bills.
- Mark bill 2 as paid.
- Delete expense number 3.
- Help me save 20000000 VND by June 2026, I already have 5000000 VND.
- Check my spending health for this month.
- Generate an expense report for this month.
"""


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    db.init_db()

    print("=== AI Expense & Bills Agent (Gemini, Advanced) ===")
    print("Type natural language commands to manage your expenses and bills.")
    print("Type 'help' for examples. Type 'exit' or 'quit' to leave.\n")

    while True:
        user_input = input("> User: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "help":
            print("\n" + HELP_TEXT + "\n")
            continue

        try:
            result = handle_user_input(user_text=user_input, ask_confirmation=True)
            print("\n[Plan]")
            print(result.get("plan", "(no plan)"))

            print("\n[Results]")
            for r in result.get("results", []):
                print(f"- {r}")
            print()
        except Exception as e:
            print(f"[Error] {e}\n")


if __name__ == "__main__":
    main()
