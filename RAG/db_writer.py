"""
db_writer.py
------------
Handles all database writes after the Router Agent makes a decision.
Person C's orchestrator calls these functions.

Two main jobs:
1. create_task()       — insert a row into tasks table
2. log_routing_action() — insert a row into audit_log
"""

import json
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     os.getenv("DB_PORT",     "5432"),
    "dbname":   os.getenv("DB_NAME",     "regwatch"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_sla_days(department_id: int, circular_source: str) -> int:
    """
    Looks up SLA days from the slas table.
    Returns 14 as a safe default if no SLA rule found.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT days_to_complete
                FROM slas
                WHERE department_id = %s AND circular_source = %s
            """, (department_id, circular_source))
            row = cur.fetchone()
            return row[0] if row else 14


def get_department_id(department_name: str) -> int | None:
    """
    Looks up department id by name.
    Returns None if department not found.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM departments WHERE name = %s",
                (department_name,)
            )
            row = cur.fetchone()
            return row[0] if row else None


def create_task(
    map_id:           int,
    department_name:  str,
    circular_source:  str,  # 'RBI', 'SEBI', or 'MCA'
    notes:            str = "",
) -> int | None:
    """
    Creates a task row in the tasks table.
    Automatically computes due_at from SLA rules.

    Returns the new task id, or None on failure.
    """
    department_id = get_department_id(department_name)
    if not department_id:
        print(f"ERROR: Department '{department_name}' not found in DB")
        return None

    sla_days = get_sla_days(department_id, circular_source)
    assigned_at = datetime.now()
    due_at      = assigned_at + timedelta(days=sla_days)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tasks
                    (map_id, department_id, assigned_at, due_at, status, notes)
                VALUES
                    (%s, %s, %s, %s, 'assigned', %s)
                RETURNING id
            """, (map_id, department_id, assigned_at, due_at, notes))
            task_id = cur.fetchone()[0]
        conn.commit()

    print(f"  Task created: id={task_id}, dept='{department_name}', due={due_at.date()}")
    return task_id


def update_map_status(map_id: int, new_status: str):
    """Updates the status of a MAP after routing decision."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE maps SET status = %s WHERE id = %s",
                (new_status, map_id)
            )
        conn.commit()


def push_to_human_review(map_id: int, reason: str):
    """
    Inserts a row into human_review_queue when confidence is low.
    Also updates the MAP status to 'pending_review'.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO human_review_queue (map_id, reason, created_at)
                VALUES (%s, %s, NOW())
            """, (map_id, reason))
        conn.commit()

    update_map_status(map_id, "pending_review")
    print(f"  MAP {map_id} pushed to human review queue: {reason[:80]}")


def log_routing_action(
    map_id:         int,
    routing_result: dict,   # the dict from router_agent.route_map_to_dict()
    task_id:        int | None = None,
):
    """
    Writes a full routing event to the audit_log table.
    This is what makes the system auditable — every routing decision
    is recorded with the full evidence (snippet, score, reason).
    """
    payload = {
        "department":       routing_result["department"],
        "confidence_score": routing_result["confidence_score"],
        "distance":         routing_result["distance"],
        "decision":         routing_result["decision"],
        "reason":           routing_result["reason"],
        "matched_snippet":  routing_result["matched_snippet"],
        "source_file":      routing_result["source_file"],
        "top_2":            routing_result["top_2"],
        "task_id":          task_id,
    }

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO audit_log
                    (entity_type, entity_id, action, actor, timestamp, payload)
                VALUES
                    ('map', %s, 'routing_decision', 'router_agent', NOW(), %s)
            """, (map_id, json.dumps(payload)))
        conn.commit()

    print(f"  Audit log written for MAP {map_id}")
