# RegWatch: Autonomous Regulatory Compliance Pipeline

**RegWatch** is an intelligent, multi-agent AI pipeline designed to automate the regulatory compliance process for financial institutions. It handles the continuous flow of circulars issued by RBI, SEBI, and MCA, from regulation identification all the way to task assignment—ensuring no critical compliance deadline is missed.

---

## 🏆 Offline constraints & Architecture

In strict adherence to the project guidelines, **this entire solution operates 100% offline.** 
No external LLM APIs (like OpenAI or Anthropic) are invoked, and the solution requires zero internet connectivity once the dependencies are installed.

To achieve state-of-the-art AI routing and deduplication offline, the system relies on local **Vector Embeddings** and **Semantic Search**:
1. **Watcher Agent**: Scans local directories for incoming circular PDFs and offline JSON data, extracting raw text robustly.
2. **MAP Extractor Agent**: Uses a robust offline Rule-Based NLP engine to extract Mandatory Action Points (MAPs) (e.g., sentences with "shall", "must", "mandated") without requiring 16GB+ of RAM for a local generative LLM. *(Note: Code for a local Ollama LLM extraction is provided in `map_extractor.py` and can be enabled if desired).*
3. **Dedup Agent**: Uses local `sentence-transformers` embeddings (via HuggingFace) and Cosine Similarity to semantically detect duplicated circulars, even if they are worded differently.
4. **Router Agent**: Utilizes **RAG** (Retrieval-Augmented Generation) powered by local embeddings and ChromaDB to semantically route the extracted MAPs to the correct internal department based on the company's knowledge base.
5. **Notifier Agent**: Dispatches simulated Email/Slack alerts directly to department queues.

## 🚀 How to Run the Demo

### 1. Execute the Pipeline
To demonstrate the pipeline functioning from start to finish, run the automated demo script. This will reset the local SQLite database, load 12 mock circulars, extract their MAPs, assign departments, and print mock Slack notifications to the terminal.

```bash
python run_demo.py
```

*Note: Depending on your CPU, it may take 30-45 seconds to load the HuggingFace models into memory and process the documents.*

### 2. View the Next.js Compliance Console Dashboard
Once the pipeline has completed, you can view the compliance metrics, parsed circulars, and assigned MAPs using the Next.js dashboard portal.

#### Method A: Start Automatically (Recommended)
You can launch both the FastAPI backend and Next.js frontend concurrently using the provided PowerShell script from the project root:
```powershell
.\RegWatch_SurakshaCanara\run_project.ps1
```

#### Method B: Start Manually (Backend and Frontend Separately)
If you prefer starting each service individually, open two terminal windows:

1. **Terminal 1: FastAPI Python Backend Server**
   * Change directory to the python project root:
     ```bash
     cd C:\Users\mhask\Desktop\canara\RegWatch_SurakshaCanara
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
     cd C:\Users\mhask\Desktop\canara\RegWatch_SurakshaCanara\frontend
     ```
   * Install Node.js packages:
     ```bash
     npm install
     ```
   * Start the Next.js dev server on port 3000:
     ```bash
     npm run dev
     ```

*Once both are running, open your web browser and navigate to **`http://localhost:3000`**.*
