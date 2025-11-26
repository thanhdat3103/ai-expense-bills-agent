import sqlite3
from datetime import date
from typing import List, Optional

from .config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'VND',
            category TEXT,
            description TEXT,
            created_at TEXT NOT NULL
        );
        '''
    )

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'VND',
            due_date TEXT NOT NULL,
            is_paid INTEGER NOT NULL DEFAULT 0,
            notes TEXT
        );
        '''
    )

    conn.commit()
    conn.close()


def add_expense(
    amount: float,
    currency: str = "VND",
    category: Optional[str] = None,
    description: Optional[str] = None,
    date_str: Optional[str] = None,
) -> int:
    if not date_str:
        date_str = date.today().isoformat()

    from datetime import datetime

    now = datetime.utcnow().isoformat(timespec="seconds")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        '''
        INSERT INTO expenses (date, amount, currency, category, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''',
        (date_str, amount, currency, category, description, now),
    )
    conn.commit()
    expense_id = cur.lastrowid
    conn.close()
    return expense_id


def list_expenses(limit: int = 20):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        '''
        SELECT * FROM expenses
        ORDER BY date DESC, id DESC
        LIMIT ?
        ''',
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_expenses(
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    conn = get_connection()
    cur = conn.cursor()

    if start_date and end_date:
        cur.execute(
            '''
            SELECT * FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC
            ''',
            (start_date, end_date),
        )
    elif period == "today":
        today = date.today().isoformat()
        cur.execute(
            '''
            SELECT * FROM expenses
            WHERE date = ?
            ORDER BY date ASC
            ''',
            (today,),
        )
    elif period == "this_week":
        today = date.today()
        iso = today.isocalendar()
        monday = date.fromisocalendar(iso.year, iso.week, 1)
        sunday = date.fromisocalendar(iso.year, iso.week, 7)
        cur.execute(
            '''
            SELECT * FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC
            ''',
            (monday.isoformat(), sunday.isoformat()),
        )
    elif period == "this_month":
        today = date.today()
        first = today.replace(day=1)
        if today.month == 12:
            next_month_first = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month_first = today.replace(month=today.month + 1, day=1)
        cur.execute(
            '''
            SELECT * FROM expenses
            WHERE date >= ? AND date < ?
            ORDER BY date ASC
            ''',
            (first.isoformat(), next_month_first.isoformat()),
        )
    else:
        cur.execute(
            '''
            SELECT * FROM expenses
            ORDER BY date ASC
            '''
        )

    rows = cur.fetchall()
    conn.close()
    return rows


def delete_expense(expense_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


def add_bill(
    name: str,
    amount: float,
    currency: str = "VND",
    due_date: str = "",
    notes: Optional[str] = None,
) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        '''
        INSERT INTO bills (name, amount, currency, due_date, notes)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (name, amount, currency, due_date, notes),
    )
    conn.commit()
    bill_id = cur.lastrowid
    conn.close()
    return bill_id


def list_bills(include_paid: bool = False):
    conn = get_connection()
    cur = conn.cursor()
    if include_paid:
        cur.execute(
            '''
            SELECT * FROM bills
            ORDER BY due_date ASC
            '''
        )
    else:
        cur.execute(
            '''
            SELECT * FROM bills
            WHERE is_paid = 0
            ORDER BY due_date ASC
            '''
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def mark_bill_paid(bill_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        'UPDATE bills SET is_paid = 1 WHERE id = ? AND is_paid = 0',
        (bill_id,),
    )
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated
