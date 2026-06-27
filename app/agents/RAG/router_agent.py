"""
router_agent.py
---------------
The Router Agent for RegWatch.

Takes a MAP text as input, queries ChromaDB, and returns:
  - department name
  - confidence score
  - matched KB snippet (for audit trail)
  - routing decision: auto_route or human_review

This is the file Person B owns. Person C's orchestrator imports
and calls route_map() after MAP extraction is done.

Usage (standalone test):
    python router_agent.py
"""

import os
import json
from dataclasses import dataclass
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ── Config ────────────────────────────────────────────────────────────────────

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_store")
EMBED_MODEL     = "sentence-transformers/all-MiniLM-L6-v2"
AUTO_ROUTE_THRESHOLD  = 0.75  
HUMAN_REVIEW_THRESHOLD = 1.00  # above this distance → definitely needs human review


# ── Return type ───────────────────────────────────────────────────────────────

@dataclass
class RoutingResult:
    """
    What the Router Agent returns for every MAP.
    Person C's orchestrator reads this and decides next pipeline step.
    """
    map_text:           str
    department:         str         # top matched department
    distance:           float       # ChromaDB cosine distance (lower = better match)
    confidence_score:   float       # converted to 0-1 scale (higher = more confident)
    matched_snippet:    str         # first 300 chars of matched KB doc (for audit log)
    source_file:        str         # which KB file matched
    decision:           str         # "auto_route" or "human_review"
    reason:             str         # why this decision was made
    top_2:              list        # both top matches (for split-routing edge cases)


# ── Core Router Agent ─────────────────────────────────────────────────────────

class RouterAgent:
    """
    Loads the persisted ChromaDB vector store and provides
    a route_map() method that Person C's orchestrator calls.

    Instantiate once at app startup — don't re-instantiate per request.
    Embedding model loading takes ~3 seconds; doing it per request kills performance.
    """

    def __init__(self):
        print("RouterAgent: Loading embeddings...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        print(f"RouterAgent: Loading ChromaDB from {CHROMA_DIR}...")
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        print(f"  Collections in store: {[c.name for c in client.list_collections()]}")

        self.vectorstore = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=self.embeddings,
    collection_name="regwatch_kb",
)
        print("RouterAgent: Ready\n")


    def route_map(self, map_text: str) -> RoutingResult:
        """
        Main method. Takes extracted MAP text, returns RoutingResult.

        Args:
            map_text: The MAP text extracted by Person A's MAP Extractor.
                      e.g. "Banks shall maintain CRR at 4.5% of NDTL effective Q3"

        Returns:
            RoutingResult with department, score, snippet, and decision.
        """

        # Query ChromaDB — get top 2 matches with distances
        results = self.vectorstore.similarity_search_with_score(
            map_text, k=2
        )

        if not results:
            # Should never happen if vectorstore has 9 docs, but handle gracefully
            return RoutingResult(
                map_text=map_text,
                department="Unknown",
                distance=1.0,
                confidence_score=0.0,
                matched_snippet="",
                source_file="",
                decision="human_review",
                reason="ChromaDB returned no results — vectorstore may be empty",
                top_2=[],
            )

        # ── Top match ────────────────────────────────────────────────────────
        top_doc,    top_distance    = results[0]
        second_doc, second_distance = results[1] if len(results) > 1 else (None, 1.0)

        top_dept    = top_doc.metadata["department"]
        top_file    = top_doc.metadata["source_file"]

        # Convert distance to a confidence score (0.0 to 1.0)
        # ChromaDB cosine distance: 0.0 = identical, 2.0 = opposite
        # We invert and scale: confidence = 1 - (distance / 2)
        confidence  = round(1 - (top_distance / 2), 4)

        # First 300 chars of the matched doc — stored in audit log
        # so humans can verify WHY this department was chosen
        snippet     = top_doc.page_content[:300].replace("\n", " ").strip()

        # ── Routing decision ─────────────────────────────────────────────────
        if top_distance <= AUTO_ROUTE_THRESHOLD:
            decision = "auto_route"
            reason   = (
                f"Strong match to '{top_dept}' "
                f"(distance: {top_distance:.4f}, confidence: {confidence:.2%})"
            )

        elif top_distance <= HUMAN_REVIEW_THRESHOLD:
            # Ambiguous — send to human review queue
            decision = "human_review"
            reason   = (
                f"Ambiguous match — top: '{top_dept}' (distance: {top_distance:.4f}), "
                f"second: '{second_doc.metadata['department'] if second_doc else 'N/A'}' "
                f"(distance: {second_distance:.4f}). "
                f"Gap too small for auto-routing."
            )

        else:
            # Very poor match — definitely needs human
            decision = "human_review"
            reason   = (
                f"Poor retrieval quality (distance: {top_distance:.4f}). "
                f"MAP text may reference a regulation not in KB. "
                f"Human review required."
            )

        # ── Build top_2 summary for audit log ────────────────────────────────
        top_2 = [
            {
                "department": top_doc.metadata["department"],
                "distance":   round(top_distance, 4),
                "confidence": confidence,
            }
        ]
        if second_doc:
            top_2.append({
                "department": second_doc.metadata["department"],
                "distance":   round(second_distance, 4),
                "confidence": round(1 - (second_distance / 2), 4),
            })

        return RoutingResult(
            map_text=map_text,
            department=top_dept,
            distance=top_distance,
            confidence_score=confidence,
            matched_snippet=snippet,
            source_file=top_file,
            decision=decision,
            reason=reason,
            top_2=top_2,
        )


    def route_map_to_dict(self, map_text: str) -> dict:
        """
        Convenience wrapper — returns dict instead of dataclass.
        Easier for Person C to store in DB and audit log directly.
        """
        result = self.route_map(map_text)
        return {
            "map_text":         result.map_text,
            "department":       result.department,
            "distance":         result.distance,
            "confidence_score": result.confidence_score,
            "matched_snippet":  result.matched_snippet,
            "source_file":      result.source_file,
            "decision":         result.decision,
            "reason":           result.reason,
            "top_2":            result.top_2,
        }


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":

    agent = RouterAgent()

    # Test MAPs — one clear, one ambiguous, one boundary case
    test_maps = [
        # Should → Treasury & Investments (clear)
        "Banks shall maintain CRR at 4.5% of Net Demand and Time Liabilities (NDTL) "
        "with effect from the fortnight beginning October 2024.",

        # Should → KYC / AML (clear)
        "All regulated entities shall file Suspicious Transaction Reports (STRs) "
        "with FIU-IND within 7 days of concluding a transaction is suspicious.",

        # Should → Credit Risk (clear)
        "Banks shall classify accounts as SMA-0 when principal or interest payment "
        "is overdue between 1 to 30 days and report to CRILC on weekly basis.",

        # Should → Legal & Regulatory Affairs (clear)
        "Listed entities shall submit quarterly corporate governance compliance report "
        "to stock exchanges within 21 days of quarter end signed by Compliance Officer.",

        # Ambiguous — spans HR & Conduct AND Legal (should go to human review)
        "The Compliance Officer shall be designated as Key Managerial Personnel. "
        "Board shall establish a vigil mechanism for directors and employees "
        "to report genuine concerns with direct access to Audit Committee chairperson.",

        # Should → Trade Finance (clear)
        "Authorised Dealer banks shall ensure export proceeds are repatriated "
        "to India within 9 months from date of shipment and report via EDPMS.",
    ]

    print("=" * 70)
    print("ROUTER AGENT — TEST RESULTS")
    print("=" * 70)

    for i, map_text in enumerate(test_maps, 1):
        result = agent.route_map(map_text)
        print(f"\nTest {i}:")
        print(f"  MAP     : {map_text[:80]}...")
        print(f"  Dept    : {result.department}")
        print(f"  Distance: {result.distance:.4f}  |  Confidence: {result.confidence_score:.2%}")
        print(f"  Decision: {result.decision.upper()}")
        print(f"  Reason  : {result.reason}")
        print(f"  Snippet : {result.matched_snippet[:120]}...")
        if len(result.top_2) > 1:
            print(f"  Top 2   : {result.top_2[0]['department']} ({result.top_2[0]['distance']:.4f}) "
                  f"vs {result.top_2[1]['department']} ({result.top_2[1]['distance']:.4f})")
        print()
