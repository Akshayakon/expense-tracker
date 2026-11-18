"""Basic tests. Run with:  python -m unittest"""

import sqlite3
import unittest

import expense_tracker as et


class ExpenseTrackerTests(unittest.TestCase):
    def setUp(self):
        self.conn = et.connect(":memory:")  # throwaway database, nothing touches expenses.db

    def tearDown(self):
        self.conn.close()

    def test_add_and_load(self):
        et.insert_expense(self.conn, "2026-11-02", "Food", "lunch", 12.5)
        df = et.load_expenses(self.conn)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.loc[0, "amount"], 12.5)

    def test_monthly_summary_only_counts_that_month(self):
        et.insert_expense(self.conn, "2026-11-02", "Food", "", 10)
        et.insert_expense(self.conn, "2026-11-09", "Food", "", 5)
        et.insert_expense(self.conn, "2026-11-10", "Rent", "", 100)
        et.insert_expense(self.conn, "2026-10-30", "Food", "", 999)
        rows, by_category = et.month_summary(et.load_expenses(self.conn), "2026-11")
        self.assertEqual(len(rows), 3)
        self.assertEqual(by_category["Food"], 15)
        self.assertEqual(by_category.idxmax(), "Rent")

    def test_delete(self):
        et.insert_expense(self.conn, "2026-11-02", "Food", "", 10)
        self.assertTrue(et.delete_by_id(self.conn, 1))
        self.assertFalse(et.delete_by_id(self.conn, 1))

    def test_database_rejects_non_positive_amount(self):
        with self.assertRaises(sqlite3.IntegrityError):
            et.insert_expense(self.conn, "2026-11-02", "Food", "", -5)

    def test_empty_database_loads_cleanly(self):
        self.assertTrue(et.load_expenses(self.conn).empty)


if __name__ == "__main__":
    unittest.main()
