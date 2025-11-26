# AI Expense & Bills Agent (Gemini, Advanced Edition)

> Final project for a Prompt Engineering / AI Agent course.  
> An LLM-powered personal finance assistant that plans actions with Google Gemini and executes them on a local database, file system, and analytical modules.

---

## 1. Problem & Motivation

Many students and early-career professionals struggle with:

- Tracking daily expenses across different categories.
- Remembering upcoming bills and due dates.
- Understanding whether their spending is “healthy” (e.g., 50/30/20 rule).
- Planning savings goals (e.g., saving for tuition, a trip, or a new laptop).

The goal of this project is to build an **AI Agent** that can:

1. Understand natural language requests about personal finances.
2. Use an LLM to **plan** what to do.
3. Safely **execute** concrete actions on a local system:
   - Update a database.
   - Generate files (Markdown reports).
   - Perform financial analysis (savings plan, spending health check).

---

## 2. High-Level Overview

The agent has three major parts:

1. **LLM Planner (Google Gemini)**  
   - Takes the user’s natural language request.
   - Produces a **JSON plan** containing:
     - A human-readable `plan` string.
     - A list of `actions` with `type` and `params`.

2. **Action Interpreter & Executor**  
   - Validates the action list (whitelist).
   - Optionally asks for confirmation for destructive actions.
   - Executes each action against:
     - A **SQLite** database (`expenses`, `bills`).
     - The **file system** (Markdown reports, JSON logs).
     - Analytical utilities (savings goal plan, spending health check).

3. **User Interfaces**  
   - **Terminal (CLI)** for fast, script-like interaction.
   - **Streamlit Web UI** with a layout inspired by “Concrete Companion”:
     - Left: Job Request.
     - Right: Execution Steps (Plan, Expense Summary, Bills Overview, Savings Plan, Spending Health Check).
     - Job history viewer based on JSON logs.

---

## 3. Features

### 3.1 Expense Management

- `add_expense`  
  Add a new expense with:
  - amount, currency (default `VND`),
  - category (e.g., Food, Transport, Entertainment),
  - description,
  - date (YYYY-MM-DD; “today” is automatically resolved by the planner).

- `list_expenses`  
  List the most recent expenses (default 10).

- `summarize_expenses`  
  Summarize expenses for a given period:
  - `today`, `this_week`, `this_month`, or `all`.
  - Shows number of expenses, total amount, and breakdown by category.

### 3.2 Bill Management

- `add_bill`  
  Add a bill with:
  - name, amount, currency, due_date, and optional notes.

- `list_bills`  
  List unpaid bills or all bills (depending on `include_paid`).

- `summarize_bills`  
  Show total number, total amount, and count of unpaid bills.

- `mark_bill_paid` **(destructive)**  
  Mark a bill as paid.

### 3.3 Advanced “Agent” Features

- `generate_report_file`  
  Generate a Markdown expense report for a period (e.g., `this_month`) and save it to the `reports/` folder.

- `plan_savings_goal`  
  Given:
  - `target_amount`,
  - `current_savings`,
  - `deadline` (YYYY-MM-DD),
  
  the agent computes how much the user should save **per month, per week, and per day**.  
  It also produces warnings if the required monthly saving is unrealistically high.

- `spending_health_check`  
  For a chosen period (e.g., `this_month`), the agent:

  - Maps categories into **Needs**, **Wants**, and **Other** using a simple mapping.
  - Computes the percentage split (Needs %, Wants %, Other %).
  - Compares with the **50/30/20** guideline.
  - Produces human-readable feedback:
    - “Your Wants spending is quite high…”
    - “Your Needs spending is relatively low…”

This turns the agent into a lightweight **financial coach**, not just CRUD on a database.

---

## 4. Architecture

### 4.1 Files & Modules

```text
src/
├─ config.py      # Gemini config, paths to DB, logs, reports
├─ db.py          # SQLite models and queries (expenses, bills)
├─ safety.py      # Allowed actions, destructive actions, logging
├─ llm_client.py  # System prompt, Gemini call, JSON parsing, retries
├─ actions.py     # Concrete implementations of all action types
├─ agent.py       # Orchestrator: planner → safety → executor
└─ main.py        # Terminal (CLI) interface

web_app.py        # Streamlit web UI
logs/             # JSON logs (agent.log)
reports/          # Markdown expense reports
```

### 4.2 Data Model (SQLite)

- **expenses**
  - `id` (PK), `date`, `amount`, `currency`,
  - `category`, `description`,
  - `created_at`.

- **bills**
  - `id` (PK), `name`, `amount`, `currency`,
  - `due_date`, `is_paid`, `notes`.

---

## 5. LLM Prompting & Planning

The planner uses **Google Gemini** (e.g., `gemini-2.5-pro`) via the `google-generativeai` SDK.

Key ideas:

- The system prompt defines a strict **JSON schema** with:
  - `plan` (string),
  - `actions` (list of objects with `type` and `params`).
- Allowed `type` values are enumerated:
  - `add_expense`, `list_expenses`, `summarize_expenses`,
  - `add_bill`, `list_bills`, `summarize_bills`,
  - `generate_report_file`, `delete_expense`, `mark_bill_paid`,
  - `plan_savings_goal`, `spending_health_check`.
- The prompt includes:
  - Detailed parameter descriptions for every action.
  - Example JSON outputs for typical user requests.
  - Dynamic context: *“Today’s date is YYYY-MM-DD…”* to normalize “today / this month / this week”.

The output is parsed as JSON (with a fallback regex extraction if the model accidentally adds extra formatting).

---

## 6. Safety, Error Handling & Logging

### 6.1 Safety

- **Whitelist** of allowed actions (`ALLOWED_ACTIONS`).
- **Destructive actions** (e.g., `delete_expense`, `mark_bill_paid`) are listed in `DESTRUCTIVE_ACTIONS`.

In the **CLI**:

- Before running a plan that includes destructive actions, the agent prints a warning and asks the user to confirm with `yes/no`.

In the **Web UI**:

- Destructive actions are assumed to be intentional (because there is no easy interactive prompt). This is clearly documented and can be discussed in the report.

### 6.2 Error Handling

- LLM API calls:
  - Retry with exponential backoff for `ResourceExhausted` (rate limiting).
  - Catch `GoogleAPIError` and unexpected exceptions, and surface user-friendly messages.
- Database & file operations:
  - Defensive checks for invalid IDs (e.g., deleting a non-existent expense).

### 6.3 Logging (Auditability)

- Every run is logged to `logs/agent.log` as a **JSON line**:
  - `timestamp`, `user_text`, and the list of `actions`.
- The Web UI includes a **“View job history”** button that shows recent log entries for transparency and debugging.

---

## 7. User Interfaces

### 7.1 CLI Usage

```bash
python -m src.main
```

Examples:

```text
Add an expense of 120000 VND for coffee with friends in entertainment category today.
Show me a summary of my expenses for this month.
Add an electricity bill of 800000 VND due on 2025-12-10.
List my unpaid bills.
Help me save 20000000 VND by June 2026, I already have 5000000 VND.
Check my spending health for this month.
Generate an expense report for this month.
Delete expense number 1.
Mark bill 1 as paid.
```

The CLI displays:

- `[Plan]` – the high-level plan from the LLM.
- `[Results]` – the results of executing each action.

### 7.2 Web UI (Streamlit)

```bash
streamlit run web_app.py
```

Layout:

- **Left: Job Request**
  - Text area for natural language input.
  - Examples to guide the user.
- **Right: Execution Steps**
  - Plan section.
  - Expense Summary.
  - Bills Overview.
  - Savings Goal Plan.
  - Spending Health Check.
  - Report & Other Messages.

A **“View job history”** button shows recent JSON log entries so users (and instructors) can inspect what the agent is doing.

The app is ready to be deployed to **Streamlit Community Cloud** for a public, shareable demo link.

---

## 8. Installation & Setup

### 8.1 Dependencies

See `requirements.txt`:

- `google-generativeai`
- `python-dotenv`
- `streamlit`

### 8.2 Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=YOUR_REAL_KEY_HERE
GEMINI_MODEL=gemini-2.5-pro
```

### 8.3 Running Locally

```bash
python -m venv venv
venv\Scripts\activate   # on Windows
pip install -r requirements.txt

# Initialize DB and run CLI
python -m src.main

# Or run the web app
streamlit run web_app.py
```

---

## 9. Mapping to Assignment Requirements

- **LLM Integration Module**
  - Uses Google Gemini (`google-generativeai`).
  - Structured prompts, JSON outputs, retry & error handling.

- **Action Interpreter / Executor**
  - Parses LLM JSON, validates actions, executes them against SQLite, the file system, and analytical logic.

- **User Interface**
  - Terminal-based CLI.
  - Streamlit web UI (with potential cloud deployment for bonus).

- **Error Handling & Safety**
  - Whitelist & destructive action confirmation.
  - Comprehensive JSON logging.
  - Graceful handling of LLM and system errors.

---

## 10. Future Work

Possible extensions:

- Multi-currency support with exchange-rate lookup.
- User authentication and multi-user database.
- Integration with bank APIs or CSV import/export.
- More sophisticated categorization and budget recommendations.
