import sqlite3
from datetime import datetime, timezone
from typing import Optional
from .models import EntryStatus


class LuckyDrawDB:

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lucky_draw_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_no INTEGER UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    email TEXT NOT NULL,
                    transaction_amount REAL NOT NULL,
                    confidence_level REAL NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('approved', 'pending', 'rejected', 'applied')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_at TIMESTAMP
                )
            """)

    def find_approved_by_phone(self, phone_number: str) -> Optional[dict]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM lucky_draw_entries WHERE phone_number = ? AND status = ?",
                (phone_number, EntryStatus.APPROVED.value)
            ).fetchone()
            return dict(row) if row else None

    def insert_entry(
        self,
        receipt_no: int,
        name: str,
        phone_number: str,
        email: str,
        transaction_amount: float,
        confidence_level: float,
        status: EntryStatus,
    ) -> int:
        approved_at = None
        if status == EntryStatus.APPROVED:
            approved_at = datetime.now(timezone.utc).isoformat()

        with self._get_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO lucky_draw_entries
                   (receipt_no, name, phone_number, email, transaction_amount,
                    confidence_level, status, approved_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (receipt_no, name, phone_number, email, transaction_amount,
                 confidence_level, status.value, approved_at)
            )
            return cursor.lastrowid

    def get_max_receipt_no(self) -> int:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(receipt_no), 0) as max_no FROM lucky_draw_entries"
            ).fetchone()
            return row["max_no"]
