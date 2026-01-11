import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "truebudget.sqlite3"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS income_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            frequency TEXT NOT NULL CHECK (frequency IN ('weekly','biweekly','monthly')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            frequency TEXT NOT NULL CHECK (frequency IN ('weekly','biweekly','monthly')),
            category TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            location TEXT,
            savings_goal_type TEXT NOT NULL CHECK (savings_goal_type IN ('amount','percent')),
            savings_goal_value REAL NOT NULL,
            focus_categories TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


# ---------- Income CRUD ----------
def add_income(name: str, amount: float, frequency: str) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO income_sources (name, amount, frequency) VALUES (?, ?, ?)",
        (name, amount, frequency),
    )
    conn.commit()
    conn.close()


def delete_income(income_id: int) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM income_sources WHERE id = ?", (income_id,))
    conn.commit()
    conn.close()


def list_income() -> List[Dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM income_sources ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- Expense CRUD ----------
def add_expense(name: str, amount: float, frequency: str, category: str) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO expenses (name, amount, frequency, category) VALUES (?, ?, ?, ?)",
        (name, amount, frequency, category),
    )
    conn.commit()
    conn.close()


def delete_expense(expense_id: int) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()


def list_expenses() -> List[Dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM expenses ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- Profile ----------
def upsert_profile(location: Optional[str], savings_goal_type: str, savings_goal_value: float, focus_categories: str) -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO profile (id, location, savings_goal_type, savings_goal_value, focus_categories)
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            location=excluded.location,
            savings_goal_type=excluded.savings_goal_type,
            savings_goal_value=excluded.savings_goal_value,
            focus_categories=excluded.focus_categories
        """,
        (location, savings_goal_type, savings_goal_value, focus_categories),
    )
    conn.commit()
    conn.close()


def get_profile() -> Optional[Dict[str, Any]]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else None
