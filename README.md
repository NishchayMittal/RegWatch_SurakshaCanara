# RegWatch: Autonomous Regulatory Compliance Pipeline

**RegWatch** (SurakshaCanara) is an intelligent, multi-agent AI pipeline designed to automate the regulatory compliance process for financial institutions. It handles the continuous flow of circulars issued by RBI, SEBI, and MCA, from regulation identification and text extraction to semantic deduplication, RAG task routing, and validation tracking—ensuring no critical compliance deadline is missed.

---

## 🏆 Offline Constraints & Architecture

In strict adherence to the project guidelines, **this entire solution operates 100% offline.** 
No external LLM APIs (like OpenAI or Anthropic) are invoked, and the solution requires zero internet connectivity once the dependencies are installed.

To achieve state-of-the-art AI routing and deduplication offline, the system relies on local **Vector Embeddings** and **Semantic Search**:
1. **Watcher Agent**: Scans local directories for incoming circular PDFs and offline JSON data, extracting raw text robustly.
2. **MAP Extractor Agent**: Uses a robust offline Rule-Based NLP engine to extract Mandatory Action Points (MAPs) (e.g., sentences with "shall", "must", "mandated") without requiring 16GB+ of RAM for a local generative LLM. *(Note: Code for a local Ollama LLM extraction is provided in `map_extractor.py` and can be enabled if desired).*
3. **Dedup Agent**: Uses local `sentence-transformers` embeddings (via HuggingFace) and Cosine Similarity to semantically detect duplicated circulars, even if they are worded differently.
4. **Router Agent**: Utilizes **RAG** (Retrieval-Augmented Generation) powered by local embeddings and ChromaDB to semantically route the extracted MAPs to the correct internal department based on the company's knowledge base.
5. **Notifier Agent**: Dispatches simulated Email/Slack alerts directly to department queues and escalates validation failures.
6. **Validator Agent**: Checks compliance descriptions and files uploaded by departments, closing the loop on task execution or trigger re-escalation alerts.

---

## 🚀 How to Run the Demo

### 1. Execute the Pipeline
To demonstrate the pipeline functioning from start to finish, run the automated demo script. This will reset the local SQLite database, load 12 mock circulars, extract their MAPs, assign departments, and print mock Slack notifications to the terminal.

```bash
cd backend
python run_demo.py
```

*Note: Depending on your CPU, it may take 30-45 seconds to load the HuggingFace models into memory and process the documents.*

---

### 2. View the Next.js Compliance Console Dashboard
Once the pipeline has completed, you can view the compliance metrics, parsed circulars, and assigned MAPs using the Next.js dashboard portal.

#### Method A: Start Automatically (Recommended)
You can launch both the FastAPI backend and Next.js frontend concurrently using the provided PowerShell script from the project root:
```powershell
.\run_project.ps1
```

#### Method B: Start Manually (Backend and Frontend Separately)
If you prefer starting each service individually, open two terminal windows:

1. **Terminal 1: FastAPI Python Backend Server**
   * Change directory to the python project backend:
     ```bash
     cd backend
     ```
   * Install Python packages:
     ```bash
     pip install -r requirements.txt
     ```
   * Start the ASGI server on port 8000:
     ```bash
     uvicorn main:app --port 8000 --reload
     ```

2. **Terminal 2: Next.js Frontend Client**
   * Change directory to the frontend folder:
     ```bash
     cd frontend
     ```
   * Install Node.js packages:
     ```bash
     npm install
     ```
   * Start the Next.js dev server on port 3000 (forcing webpack to prevent Windows Turbopack crashes):
     ```bash
     npm run dev
     ```

*Once both are running, open your web browser and navigate to **`http://127.0.0.1:3000`**.*

---

## 🧪 Special Features & Testing Workflows

### 1. Manual Deletion of Obligations
*   You can manually delete any compliance obligation directly from the console review card. Clicking **"Delete Compliance Obligation"** deletes the MAP, its assigned tasks, and evidence records, writing a fully-audited log entry.

### 2. Testing the Notifier Re-Escalation Popup Toast
To test the real-time re-escalation alert popup:
1. Select any pending obligation card and click **"Details and Evidence"**.
2. Submit invalid evidence:
   * **Actions Executed**: Type a very short description (less than 20 characters) like `"Done"`.
   * **Document URL**: Leave this field completely **blank**.
3. Click **"Validate Submission"**.
4. The **Validator Agent** will fail the verification due to length constraints and missing files. The status updates to `evidence_incomplete`, and a red **Notifier Agent Alert** toast slides in from the top right corner showing the re-escalation event.

### 3. Dynamic SLA Deadline Indicators
*   Compliance obligation cards and search results display dynamic due badges showing the calculated target date (`⏰ Due Jul 13, 2026`) derived from the circular's creation date plus its allocated SLA limit.

### 4. Local Time Auditing
*   All backend database operations (evidence logging, human review approvals, and deletions) write logs using the local timezone (`datetime.now()`). The **Audit Log Feed** at the bottom of the portal displays logs synchronized with your desktop system's time.
