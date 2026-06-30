# RegWatch RAG — Router Agent Setup

## File Structure

```
regwatch_rag/
├── requirements.txt        # pip install this first
├── .env.example            # copy to .env, fill DB password
├── build_vectorstore.py    # run ONCE to embed KB docs into ChromaDB
├── router_agent.py         # RouterAgent class — Person B owns this
├── db_writer.py            # DB write helpers — Person C integrates this
├── pipeline.py             # process_map() — Person C calls this
└── chroma_store/           # auto-created by build_vectorstore.py
```

## Run Order (do exactly this)

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```
First run downloads the all-MiniLM-L6-v2 model (~90MB). Takes 2-3 mins.
Subsequent runs are instant — model is cached at ~/.cache/huggingface.

### Step 2 — Set up .env
```bash
cp .env.example .env
# Edit .env with your PostgreSQL password
```

### Step 3 — Build the vector store (run ONCE)
```bash
python build_vectorstore.py
```
Expected output:
```
Loading KB documents...
  Loaded: Treasury & Investments
  Loaded: KYC / AML
  ... (9 total)
Loaded 9 documents

Initialising HuggingFace embeddings (all-MiniLM-L6-v2)...
Embeddings ready

Building ChromaDB vector store...
Persisted to ./chroma_store
Done. 9 documents embedded.

Sanity check — querying: 'banks must maintain CRR at 4.5 percent'
  → Treasury & Investments (score: 0.3421)
  → Credit Risk (score: 0.6234)
```
The CRR query should return Treasury as top match. If it doesn't, check KB docs loaded correctly.

### Step 4 — Test the Router Agent standalone
```bash
python router_agent.py
```
Runs 6 test MAPs through the router with no DB writes. Safe to run anytime.

### Step 5 — Test the full pipeline (needs seeded DB)
```bash
python pipeline.py
```
Runs 2 pending MAPs from seed data through the full pipeline including DB writes.

## What Each File Does

| File | Purpose | Who touches it |
|------|---------|----------------|
| build_vectorstore.py | Embeds KB docs → ChromaDB | Person B (run once) |
| router_agent.py | Routing logic only, no DB | Person B owns |
| db_writer.py | All DB writes after routing | Person C integrates |
| pipeline.py | Ties router + DB together | Person C calls this |

## How Person C Integrates This

In the orchestrator, after MAP extraction:

```python
from pipeline import process_map

# Called for each MAP that comes out of Person A's extractor
result = process_map(
    map_id=extracted_map.id,
    map_text=extracted_map.map_text,
    circular_source=circular.source   # 'RBI', 'SEBI', or 'MCA'
)

if result["decision"] == "auto_route":
    # Task created, map status = 'assigned'
    # Trigger Notifier Agent with result["task_id"]
    pass
else:
    # MAP is in human_review_queue
    # Dashboard shows it for human decision
    pass
```

## Threshold Tuning

In router_agent.py, two thresholds control routing decisions:

```python
AUTO_ROUTE_THRESHOLD  = 0.55   # distance ≤ this → auto route
HUMAN_REVIEW_THRESHOLD = 0.75  # distance > this → definitely human review
```

After testing with real circulars in Week 2, you may need to adjust these.
Lower AUTO_ROUTE_THRESHOLD = stricter auto-routing (more goes to human review).
Run router_agent.py standalone to test without touching the DB.

## Rebuilding the Vector Store

Only needed if you edit the KB .txt files:
```bash
rm -rf chroma_store/
python build_vectorstore.py
```
