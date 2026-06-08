"""
pipeline.py
-----------
The entry point that Person C's orchestrator calls.

This ties everything together:
    Router Agent → DB Writer → Audit Log

Person C imports process_map() and calls it for each MAP
that comes out of Person A's MAP Extractor.

Usage:
    from pipeline import process_map

    result = process_map(
        map_id=1,
        map_text="Banks shall maintain CRR at 4.5% of NDTL",
        circular_source="RBI"
    )
"""

from router_agent import RouterAgent
from db_writer import (
    create_task,
    update_map_status,
    push_to_human_review,
    log_routing_action,
)

# Instantiate once at module load — not per call
# This keeps embedding model in memory across all requests
_router = RouterAgent()


def process_map(
    map_id:          int,
    map_text:        str,
    circular_source: str,   # 'RBI', 'SEBI', or 'MCA'
) -> dict:
    """
    Full routing pipeline for a single MAP.

    Steps:
    1. RouterAgent queries ChromaDB → gets department + confidence + snippet
    2. If auto_route  → create task, update map status, write audit log
    3. If human_review → push to review queue, write audit log

    Args:
        map_id:          The id of the MAP row in the maps table
        map_text:        The extracted MAP text from Person A's extractor
        circular_source: Source regulator — used for SLA lookup

    Returns:
        dict with routing outcome, for Person C's orchestrator to use
    """

    print(f"\nProcessing MAP {map_id}:")
    print(f"  Text: {map_text[:100]}...")

    # ── Step 1: Route ─────────────────────────────────────────────────────────
    routing = _router.route_map_to_dict(map_text)

    print(f"  → Department  : {routing['department']}")
    print(f"  → Confidence  : {routing['confidence_score']:.2%}")
    print(f"  → Decision    : {routing['decision'].upper()}")
    print(f"  → Reason      : {routing['reason']}")

    task_id = None

    # ── Step 2a: Auto-route ───────────────────────────────────────────────────
    if routing["decision"] == "auto_route":

        task_id = create_task(
            map_id=map_id,
            department_name=routing["department"],
            circular_source=circular_source,
            notes=f"Auto-routed by RouterAgent. Confidence: {routing['confidence_score']:.2%}. "
                  f"Matched KB: {routing['source_file']}",
        )

        update_map_status(map_id, "assigned")

    # ── Step 2b: Human review ─────────────────────────────────────────────────
    else:
        push_to_human_review(
            map_id=map_id,
            reason=routing["reason"],
        )
        # map status is set to 'pending_review' inside push_to_human_review()

    # ── Step 3: Audit log ─────────────────────────────────────────────────────
    log_routing_action(
        map_id=map_id,
        routing_result=routing,
        task_id=task_id,
    )

    # Return summary for orchestrator
    return {
        "map_id":       map_id,
        "department":   routing["department"],
        "confidence":   routing["confidence_score"],
        "decision":     routing["decision"],
        "task_id":      task_id,
        "snippet":      routing["matched_snippet"],
        "reason":       routing["reason"],
    }


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":

    # These map_ids must exist in your seeded database
    # Using MAPs 11 and 12 which are currently 'pending_review' in seed data

    test_cases = [
        {
        "map_id": 10,
        "map_text": "Establish and disclose a whistleblower/vigil mechanism on the company website. "
                    "Compliance Officer must be designated as a Key Managerial Personnel.",
        "circular_source": "SEBI",
    },
        {
            "map_id": 11,
            "map_text": "All directors with DIN allotted on or before 31st March 2024 "
                        "must file DIR-3 KYC or DIR-3 KYC-Web on MCA21 portal.",
            "circular_source": "MCA",
        },
        {
            "map_id": 12,
            "map_text": "Companies shall ensure all their directors complete DIR-3 KYC "
                        "filing before the deadline to avoid DIN deactivation.",
            "circular_source": "MCA",
        },
    ]

    print("=" * 70)
    print("PIPELINE — END TO END TEST")
    print("Running router → DB write → audit log for 2 pending MAPs")
    print("=" * 70)

    for case in test_cases:
        result = process_map(**case)
        print(f"\n  RESULT: {result}\n")
        print("-" * 70)
