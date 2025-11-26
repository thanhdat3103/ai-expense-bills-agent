from typing import List

import streamlit as st

from src import db
from src.agent import handle_user_input
from src.config import LOG_DIR, REPORTS_DIR


def read_last_logs(max_lines: int = 20) -> List[str]:
    log_file = LOG_DIR / "agent.log"
    if not log_file.exists():
        return []
    lines = log_file.read_text(encoding="utf-8").splitlines()
    return lines[-max_lines:]


def split_results(results: List[str]):
    expense_summary = []
    bill_summary = []
    savings_plan = []
    health_check = []
    report_info = []
    other = []

    for r in results:
        if "Expense summary" in r:
            expense_summary.append(r)
        elif r.startswith("Bill summary"):
            bill_summary.append(r)
        elif r.startswith("Savings goal plan"):
            savings_plan.append(r)
        elif r.startswith("Spending health check"):
            health_check.append(r)
        elif r.startswith("Created report at"):
            report_info.append(r)
        else:
            other.append(r)

    return {
        "expense_summary": "\n".join(expense_summary) if expense_summary else "",
        "bill_summary": "\n".join(bill_summary) if bill_summary else "",
        "savings_plan": "\n".join(savings_plan) if savings_plan else "",
        "health_check": "\n".join(health_check) if health_check else "",
        "report_info": "\n".join(report_info) if report_info else "",
        "other": other,
    }


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    db.init_db()

    st.set_page_config(
        page_title="AI Expense & Bills Agent",
        page_icon="💰",
        layout="wide",
    )

    header_left, header_right = st.columns([3, 1])
    with header_left:
        st.title("💰 AI Expense & Bills Agent")
        st.caption(
            "An AI planner & executor for personal expenses and bills. "
            "Describe what you want in natural language and let the agent "
            "infer actions, update the database, and generate reports."
        )
    with header_right:
        if st.button("View job history"):
            with st.expander("Recent job history", expanded=True):
                logs = read_last_logs()
                if not logs:
                    st.write("No logs yet.")
                else:
                    for line in logs:
                        st.code(line, language="json")

    left, right = st.columns([2, 3])

    with left:
        st.subheader("Job Request")
        st.write(
            "Describe what you want the agent to do: add expenses, summarize spending, "
            "manage bills, plan savings goals, or run a spending health check."
        )

        with st.form(key="agent_form"):
            user_text = st.text_area(
                "Request",
                height=220,
                placeholder=(
                    "Examples:\n"
                    "- Add an expense of 120000 VND for coffee with friends in entertainment category today.\n"
                    "- Show me a summary of my expenses for this month.\n"
                    "- Add an electricity bill of 800000 VND due on 2025-12-10.\n"
                    "- List my unpaid bills.\n"
                    "- Help me save 20000000 VND by June 2026, I already have 5000000 VND.\n"
                    "- Check my spending health for this month.\n"
                ),
            )
            run_agent = st.form_submit_button("Run agent")

    with right:
        st.subheader("Execution Steps")

        if run_agent and user_text.strip():
            try:
                result = handle_user_input(user_text=user_text, ask_confirmation=False)
                plan = result.get("plan", "(no plan)")
                results = result.get("results", [])

                st.markdown("#### Plan")
                st.write(plan)

                grouped = split_results(results)

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("##### Expense Summary")
                    if grouped["expense_summary"]:
                        st.code(grouped["expense_summary"], language="text")
                    else:
                        st.caption("Run an expense summary to see results here.")

                    st.markdown("##### Savings Goal Plan")
                    if grouped["savings_plan"]:
                        st.code(grouped["savings_plan"], language="text")
                    else:
                        st.caption("Ask for a savings goal plan to populate this section.")

                with col2:
                    st.markdown("##### Bills Overview")
                    if grouped["bill_summary"]:
                        st.code(grouped["bill_summary"], language="text")
                    else:
                        st.caption("Run a bill summary or list bills to see results here.")

                    st.markdown("##### Spending Health Check")
                    if grouped["health_check"]:
                        st.code(grouped["health_check"], language="text")
                    else:
                        st.caption("Ask for a spending health check to populate this section.")

                st.markdown("##### Report & Other Messages")
                if grouped["report_info"]:
                    st.success(grouped["report_info"])
                for msg in grouped["other"]:
                    st.write(f"- {msg}")

            except Exception as e:
                st.error(f"Error while running agent: {e}")
        else:
            st.info("No run yet. Submit a job description on the left to see the plan and execution steps here.")


if __name__ == "__main__":
    main()
