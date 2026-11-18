"""Simple Expense Tracker: add, view, and summarize expenses (SQLite + Pandas + Matplotlib)."""

import sqlite3
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Always store the database next to this script, no matter where it is run from.
BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "expenses.db"
CATEGORIES = ["Food", "Transport", "Rent", "Shopping", "Bills", "Entertainment", "Other"]


# ---------- Database ----------

def connect(db_file=DB_FILE):
    """Open the database and make sure the table exists."""
    conn = sqlite3.connect(db_file)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS expenses (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               date TEXT NOT NULL,
               category TEXT NOT NULL,
               description TEXT NOT NULL DEFAULT '',
               amount REAL NOT NULL CHECK (amount > 0)
           )"""
    )
    return conn


def insert_expense(conn, day, category, description, amount):
    conn.execute(
        "INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)",
        (day, category, description, round(amount, 2)),
    )
    conn.commit()


def delete_by_id(conn, expense_id):
    """Delete an expense. Returns True if something was deleted."""
    cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    return cur.rowcount > 0


def load_expenses(conn):
    """Return all expenses as a Pandas DataFrame."""
    df = pd.read_sql_query("SELECT * FROM expenses ORDER BY date, id", conn)
    df["date"] = pd.to_datetime(df["date"])
    return df


def month_summary(df, month):
    """Return (rows for that month, total per category) for a 'YYYY-MM' string."""
    rows = df[df["date"].dt.strftime("%Y-%m") == month]
    by_category = rows.groupby("category")["amount"].sum().sort_values(ascending=False)
    return rows, by_category


# ---------- Input helpers (keep asking until the answer is valid) ----------

def ask_date():
    while True:
        text = input("Date (YYYY-MM-DD, Enter for today): ").strip() or str(date.today())
        try:
            date.fromisoformat(text)
            return text
        except ValueError:
            print("  Invalid date. Example: 2026-11-18")


def ask_category():
    print("Categories:")
    for i, name in enumerate(CATEGORIES, 1):
        print(f"  {i}. {name}")
    while True:
        text = input("Pick a category number: ").strip()
        if text.isdigit() and 1 <= int(text) <= len(CATEGORIES):
            return CATEGORIES[int(text) - 1]
        print(f"  Enter a number from 1 to {len(CATEGORIES)}.")


def ask_amount():
    while True:
        try:
            amount = float(input("Amount: ").strip())
        except ValueError:
            print("  Amount must be a number.")
            continue
        if amount <= 0 or amount != amount or amount == float("inf"):
            print("  Amount must be greater than 0.")
            continue
        return amount


def ask_month():
    while True:
        text = input("Month (YYYY-MM, Enter for current): ").strip() or date.today().strftime("%Y-%m")
        try:
            date.fromisoformat(text + "-01")
            return text
        except ValueError:
            print("  Invalid month. Example: 2026-11")


# ---------- Menu actions ----------

def add_expense(conn):
    day = ask_date()
    category = ask_category()
    description = input("Description (optional): ").strip()
    amount = ask_amount()
    insert_expense(conn, day, category, description, amount)
    print("Expense added.")


def view_expenses(conn):
    df = load_expenses(conn)
    if df.empty:
        print("No expenses yet.")
        return
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    print(df.to_string(index=False))
    print(f"\nTotal: {df['amount'].sum():.2f}")


def delete_expense(conn):
    text = input("ID of the expense to delete: ").strip()
    if not text.isdigit():
        print("Enter a number.")
        return
    print("Deleted." if delete_by_id(conn, int(text)) else "No expense with that ID.")


def monthly_report(conn):
    month = ask_month()
    rows, by_category = month_summary(load_expenses(conn), month)
    if rows.empty:
        print(f"No expenses found for {month}.")
        return
    print(f"\n--- Report for {month} ---")
    print(by_category.round(2).to_string())
    print(f"\nTotal spent: {rows['amount'].sum():.2f}")
    print(f"Biggest category: {by_category.idxmax()}")


def show_charts(conn):
    month = ask_month()
    rows, by_category = month_summary(load_expenses(conn), month)
    if rows.empty:
        print(f"No expenses found for {month}.")
        return
    by_day = rows.groupby(rows["date"].dt.day)["amount"].sum()

    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4))
    left.pie(by_category, labels=by_category.index, autopct="%1.0f%%")
    left.set_title(f"Spending by category ({month})")
    right.bar(by_day.index, by_day.values)
    right.set_title(f"Spending per day ({month})")
    right.set_xlabel("Day of month")
    right.set_ylabel("Amount")
    fig.tight_layout()

    path = BASE_DIR / f"report_{month}.png"
    fig.savefig(path)
    print(f"Chart saved to {path}")
    try:
        plt.show()  # may not work on machines without a display; the PNG is already saved
    except Exception:
        pass
    plt.close(fig)


# ---------- Main loop ----------

def main():
    try:
        conn = connect()
    except sqlite3.Error as err:
        print(f"Could not open the database: {err}")
        return

    actions = {
        "1": ("Add expense", add_expense),
        "2": ("View all expenses", view_expenses),
        "3": ("Delete an expense", delete_expense),
        "4": ("Monthly report", monthly_report),
        "5": ("Show charts", show_charts),
    }
    try:
        while True:
            print("\n=== Expense Tracker ===")
            for key, (label, _) in actions.items():
                print(f"{key}. {label}")
            print("0. Exit")
            choice = input("Choose: ").strip()
            if choice == "0":
                break
            if choice not in actions:
                print("Invalid choice.")
                continue
            try:
                actions[choice][1](conn)
            except sqlite3.Error as err:  # one bad action should not crash the app
                print(f"Database error: {err}")
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
