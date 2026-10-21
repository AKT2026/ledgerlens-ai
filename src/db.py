"""SQLite audit database for LedgerLens AI review workflow."""

import sqlite3
from typing import List, Dict, Any

DB_PATH = "reconciliation_audit.db"


def init_db(db_path: str = DB_PATH) -> None:
    """Initialize the audit review table if not already created."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_reviews (
                reference_id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                order_amount REAL,
                payment_amount REAL,
                variance REAL,
                status TEXT,
                system_notes TEXT,
                review_status TEXT DEFAULT 'PENDING_REVIEW',
                reviewer_notes TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def save_reconciliation_results(results: List[Any], db_path: str = DB_PATH) -> None:
    """Upsert reconciliation results without overwriting manual human notes."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for r in results:
            o_amt = r.order_amount if r.order_amount is not None else 0.0
            p_amt = r.payment_amount if r.payment_amount is not None else 0.0
            variance = round(p_amt - o_amt, 2)
            st_val = r.status.value if r.status else "N/A"

            cursor.execute("""
                INSERT INTO audit_reviews (
                    reference_id, category, order_amount, payment_amount, variance, status, system_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(reference_id) DO UPDATE SET
                    category = excluded.category,
                    order_amount = excluded.order_amount,
                    payment_amount = excluded.payment_amount,
                    variance = excluded.variance,
                    status = excluded.status,
                    system_notes = excluded.system_notes
            """, (r.reference_id, r.category.value, r.order_amount, r.payment_amount, variance, st_val, r.system_notes))
        conn.commit()


def get_all_reviews(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Fetch all audit records ordered by most recent update."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_reviews ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def update_review_status(reference_id: str, review_status: str, notes: str, db_path: str = DB_PATH) -> None:
    """Record a human reviewer's disposition and audit notes."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE audit_reviews
            SET review_status = ?, reviewer_notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE reference_id = ?
        """, (review_status, notes, reference_id))
        conn.commit()
