"""
migrate_validator.py — Piece 1: DB Migration for Validator Flow
================================================================
Adds evidence tracking columns to the existing `tasks` table
and creates a new `validator_log` table.

Safe to run multiple times — uses ADD COLUMN IF NOT EXISTS pattern
via try/except so it won't crash on an already-migrated DB.

Run:
    python migrate_validator.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("regwatch.db")

# ── colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"; YELLOW = "\033[93m"; BOLD = "\033[1m"
CYAN   = "\033[96m"; RESET  = "\033[0m";  DIM  = "\033[2m"

def ok(text):   print(f"  {GREEN}✔{RESET}  {text}")
def warn(text): print(f"  {YELLOW}⚠{RESET}  {text}")
def info(text): print(f"  {DIM}→{RESET}  {text}")


def add_column_if_missing(conn, table: str, column: str, definition: str):
    """
    SQLite has no ADD COLUMN IF NOT EXISTS — this is the standard workaround.
    Checks existing columns before attempting the ALTER.
    """
    cur = conn.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cur.fetchall()}   # row[1] = column name

    if column in existing:
        warn(f"{table}.{column} already exists — skipping.")
        return

    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    conn.commit()
    ok(f"Added {table}.{column}  ({definition})")


def create_validator_log(conn):
    """
    validator_log — one row per validation decision.
    This is the audit trail you show judges/auditors:
    every MAP that was submitted, who reviewed it, what was decided, and why.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS validator_log (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id          INTEGER NOT NULL,
            map_text         TEXT,
            department_name  TEXT,
            evidence_text    TEXT,
            decision         TEXT NOT NULL,   -- 'APPROVED' | 'REJECTED'
            reason           TEXT,            -- why it was approved/rejected
            confidence       REAL,            -- 0.0 – 1.0 match score
            decided_at       TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)
    conn.commit()
    ok("Created table: validator_log")


def verify_migration(conn):
    """Print the final schema of tasks and validator_log so you can confirm."""
    print(f"\n  {BOLD}tasks columns after migration:{RESET}")
    for row in conn.execute("PRAGMA table_info(tasks)"):
        col_id, name, dtype, notnull, default, pk = row
        print(f"  {DIM}  {name:<25} {dtype:<10} "
              f"{'NOT NULL' if notnull else 'nullable':<10} "
              f"default={default}{RESET}")

    print(f"\n  {BOLD}validator_log columns:{RESET}")
    for row in conn.execute("PRAGMA table_info(validator_log)"):
        col_id, name, dtype, notnull, default, pk = row
        print(f"  {DIM}  {name:<25} {dtype:<10} "
              f"{'NOT NULL' if notnull else 'nullable':<10} "
              f"default={default}{RESET}")


def main():
    if not DB_PATH.exists():
        print(f"\n  {YELLOW}⚠  {DB_PATH} not found.")
        print(f"  Run python run_demo.py first to create the DB, then re-run this.{RESET}\n")
        return

    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  RegWatch — Validator DB Migration{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}\n")

    conn = sqlite3.connect(str(DB_PATH))

    # ── New columns on tasks ──────────────────────────────────────────────────
    print(f"  {BOLD}Migrating: tasks table{RESET}")

    # Who submitted the evidence and when
    add_column_if_missing(conn, "tasks", "reviewer",         "TEXT DEFAULT ''")
    add_column_if_missing(conn, "tasks", "evidence_text",    "TEXT DEFAULT ''")
    add_column_if_missing(conn, "tasks", "evidence_at",      "TEXT DEFAULT ''")

    # Why it was rejected (empty if approved)
    add_column_if_missing(conn, "tasks", "rejection_reason", "TEXT DEFAULT ''")

    # Validator confidence score for the submission (0.0 – 1.0)
    add_column_if_missing(conn, "tasks", "validator_score",  "REAL DEFAULT 0.0")

    # ── New table ─────────────────────────────────────────────────────────────
    print(f"\n  {BOLD}Creating: validator_log table{RESET}")
    create_validator_log(conn)

    # ── Verify ────────────────────────────────────────────────────────────────
    verify_migration(conn)

    # ── Log the migration itself ──────────────────────────────────────────────
    conn.execute(
        "INSERT INTO audit_log (event, detail, created_at) VALUES (?,?,?)",
        ("DB_MIGRATION", "validator_flow columns + validator_log table added",
         datetime.now().isoformat()),
    )
    conn.commit()
    ok("\nMigration event written to audit_log.")

    conn.close()

    print(f"\n  {GREEN}{BOLD}Migration complete.{RESET}")
    print(f"  {DIM}Next: python -c \"from app.agents.validator import ValidatorAgent\"{RESET}\n")


if __name__ == "__main__":
    main()