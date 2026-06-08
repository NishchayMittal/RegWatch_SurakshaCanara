"""
build_vectorstore.py
--------------------
Run this ONCE to embed all 9 KB docs and persist them into ChromaDB.
After this runs, you never need to re-embed unless KB docs change.

Usage:
    python build_vectorstore.py

Expected output:
    Loading KB documents...
    Loaded 9 documents
    Initialising HuggingFace embeddings (all-MiniLM-L6-v2)...
    Building ChromaDB vector store...
    Persisted to ./chroma_store
    Done. 9 documents embedded.
"""

import os
from pathlib import Path
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
# ── Config ────────────────────────────────────────────────────────────────────

KB_DIR        = Path("../KnowledgeBase")   # folder with your 9 .txt filesKB_DIR = Path("../KnowlegeBase")

CHROMA_DIR    = "./chroma_store"         # where ChromaDB persists on disk
EMBED_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"

# Map each filename to its department name
# This metadata is what gets returned when a MAP is routed
FILENAME_TO_DEPT = {
    "01_treasury_investments.txt":      "Treasury & Investments",
    "02_kyc_aml.txt":                   "KYC / AML",
    "03_credit_risk.txt":               "Credit Risk",
    "04_retail_banking_compliance.txt": "Retail Banking Compliance",
    "05_it_cybersecurity.txt":          "IT & Cybersecurity",
    "06_hr_conduct.txt":                "HR & Conduct",
    "07_legal_regulatory_affairs.txt":  "Legal & Regulatory Affairs",
    "08_trade_finance.txt":             "Trade Finance",
    "09_audit_inspection.txt":          "Audit & Inspection",
}

# ── Step 1: Load KB docs as LangChain Documents ───────────────────────────────

def load_kb_documents() -> list[Document]:
    """
    Reads each .txt file from KB_DIR and wraps it in a LangChain Document.
    The metadata dict carries the department name — this is what the
    Router Agent reads after retrieval.
    """
    print("Loading KB documents...")
    docs = []

    for filename, dept_name in FILENAME_TO_DEPT.items():
        filepath = KB_DIR / filename

        if not filepath.exists():
            print(f"  WARNING: {filename} not found — skipping")
            continue

        content = filepath.read_text(encoding="utf-8")

        doc = Document(
            page_content=content,
            metadata={
                "department":  dept_name,
                "source_file": filename,
            }
        )
        docs.append(doc)
        print(f"  Loaded: {dept_name}")

    print(f"Loaded {len(docs)} documents\n")
    return docs


# ── Step 2: Initialise embeddings ─────────────────────────────────────────────

def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Loads all-MiniLM-L6-v2 locally via sentence-transformers.
    First run downloads ~90MB model to ~/.cache/huggingface.
    Subsequent runs load from cache — no internet needed.
    """
    print(f"Initialising HuggingFace embeddings ({EMBED_MODEL})...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"},       # change to "cuda" if you have GPU
        encode_kwargs={"normalize_embeddings": True},
    )
    print("Embeddings ready\n")
    return embeddings


# ── Step 3: Build and persist ChromaDB ───────────────────────────────────────

def build_vectorstore(docs, embeddings):
    print("Building ChromaDB vector store...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    split_docs = splitter.split_documents(docs)
    print(f"Split {len(docs)} docs into {len(split_docs)} chunks")

    vectorstore = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name="regwatch_kb",
    )

    print(f"Persisted to {CHROMA_DIR}")
    print(f"Done. {len(split_docs)} chunks embedded.\n")
    return vectorstore


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    docs        = load_kb_documents()
    embeddings  = get_embeddings()
    vectorstore = build_vectorstore(docs, embeddings)

    # Quick sanity check — test one query immediately after building
    print("Sanity check — querying: 'banks must maintain CRR at 4.5 percent'")
    results = vectorstore.similarity_search_with_score(
        "banks must maintain CRR at 4.5 percent", k=2
    )
    for doc, score in results:
        print(f"  → {doc.metadata['department']} (score: {score:.4f})")
