"""Fill the tracker with fake expenses so you can try reports and charts.

Run from the project folder:  python examples/sample_data.py
It refuses to run if you already have expenses, so your real data is never mixed with fake data.
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # find expense_tracker.py

import expense_tracker as et  # noqa: E402

# (category, description, min amount, max amount)
TEMPLATES = [
    ("Food", "Groceries", 20, 80),
    ("Food", "Lunch", 8, 18),
    ("Food", "Coffee", 3, 6),
    ("Transport", "Bus pass", 10, 30),
    ("Transport", "Fuel", 25, 50),
    ("Shopping", "Clothes", 25, 120),
    ("Bills", "Electricity", 40, 90),
    ("Bills", "Internet", 45, 60),
    ("Entertainment", "Movie", 10, 25),
    ("Entertainment", "Games", 5, 40),
    ("Other", "Misc", 5, 30),
]


def add_samples(conn, month="2026-10", count=30, seed=1):
    random.seed(seed)
    insert = et.insert_expense
    insert(conn, f"{month}-01", "Rent", "Monthly rent", 900)
    for _ in range(count):
        category, description, low, high = random.choice(TEMPLATES)
        day = random.randint(1, 28)
        insert(conn, f"{month}-{day:02d}", category, description, round(random.uniform(low, high), 2))


if __name__ == "__main__":
    connection = et.connect()
    if not et.load_expenses(connection).empty:
        print("You already have expenses saved, so sample data was not added.")
    else:
        add_samples(connection)
        print("Added sample expenses for 2026-10. Try the monthly report with month 2026-10.")
    connection.close()
