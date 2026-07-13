# ResolveDesk AI — Multi-Agent Support Co-Pilot

A production-style, multi-agent AI support co-pilot built with **LangGraph**, **FastAPI**, **React**, **Qdrant**, and **SQLite**. Designed for support managers and agents to query customer data, retrieve company policy documents, and manage subscription operations through a conversational AI interface.

---

## Prerequisites

Before you start, make sure you have the following installed:

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Backend runtime |
| Node.js | 18+ | Frontend React build |
| Git | Any | Cloning the repo |
| Docker *(optional)* | Any | Running Qdrant locally |

---

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/capstone_project.git
cd capstone_project
```

---

## 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Upgrade pip to the latest version
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

---

## 3. Configure Environment Variables

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` and set the following values:

```env
# --- Qdrant Vector Store ---
# Option A: Qdrant Cloud (recommended for sharing)
QDRANT_URL=https://<your-cluster-id>.aws.cloud.qdrant.io
QDRANT_API_KEY=<your-qdrant-cloud-api-key>

# Option B: Local Qdrant via Docker (see Step 4 below)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=   # leave blank for local

# --- LLM (OpenAI-compatible endpoint) ---
OPENAI_API_KEY=<your-openai-or-gemini-api-key>
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-4o-mini

# --- Optional ---
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=   # only needed for LangSmith tracing
```

> **Note:** `SQLITE_DB_PATH` does **not** need to be set. All file paths in the project resolve automatically relative to the project root using `pathlib`. They work on any machine regardless of the directory structure.

---

## 4. Set Up Qdrant (Vector Store)

### Option A: Qdrant Cloud *(recommended)*
1. Sign up at [cloud.qdrant.io](https://cloud.qdrant.io) and create a free cluster.
2. Copy your **Cluster URL** and **API Key** into `.env`.

### Option B: Local Docker
Run a local Qdrant instance with Docker:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

Then set `QDRANT_URL=http://localhost:6333` in `.env` and leave `QDRANT_API_KEY` blank.

---

## 5. Set Up the Database

Generate and seed the SQLite database with sample customer, subscription, and payment data:

```bash
# Create the schema
python database/init_db.py

# Seed with sample data (100 customers)
python database/seed_data_generator.py
```

The database file is automatically created at `database/support.db`.

---

## 6. Generate & Ingest Knowledge Base Documents

Generate the 9 company policy PDF documents and index them into Qdrant:

```bash
# Step 1: Generate the PDFs
python backend/app/knowledge/generate_pdfs.py

# Step 2: Ingest them into Qdrant
python backend/app/knowledge/ingest.py
```

This creates 40 semantic vector chunks in Qdrant under the collection `resolvedesk_docs`.

---

## 7. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

## 8. Run the Application

Use the provided launcher to start both servers simultaneously:

```bash
# Windows
run.bat
```

Or start them manually in two separate terminals:

```bash
# Terminal 1 — Backend API (http://localhost:8000)
python -m uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 — Frontend Dev Server (http://localhost:5173)
cd frontend
npm run dev
```

Open your browser at **http://localhost:5173**.

---

## 9. Run the Automated Evaluation Suite *(optional)*

```bash
python backend/app/evaluation/run_evaluation.py
```

Expected results:
- **Routing Accuracy**: 100% (6/6)
- **Safety Compliance**: 100% (6/6)
- **Content Groundedness**: 100% (6/6)

---

## Project Structure

```
capstone_project/
├── backend/
│   └── app/
│       ├── agents/          # Supervisor, Planner, RAG, SQL agent nodes
│       ├── evaluation/      # Automated test suite & results
│       ├── knowledge/       # PDF generator + Qdrant ingest scripts
│       ├── tools/           # SQL and RAG tool functions
│       └── main.py          # FastAPI app entry point
├── database/
│   ├── schema.sql           # SQLite schema
│   ├── init_db.py           # Creates support.db from schema
│   └── seed_data_generator.py  # Seeds customer/subscription/payment data
├── docs/                    # Phase reports & design documents
├── frontend/                # React + TypeScript UI
├── knowledge/docs/          # Generated PDF knowledge base files
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
└── run.bat                  # One-click launcher (Windows)
```

---

## Architecture Overview

```
User (Browser) → React Frontend (port 5173)
                    ↓ REST API
             FastAPI Backend (port 8000)
                    ↓
            LangGraph Supervisor
           /         |         \
    RAG Agent    SQL Agent   Planner Agent
       ↓              ↓           ↓
  Qdrant Cloud    SQLite DB   RAG + SQL
  (Policy docs) (Customer DB)  combined
                    ↓
             Safety Node
                    ↓
             Final Response
```

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `QDRANT_URL` | ✅ Yes | Qdrant Cloud cluster URL or `http://localhost:6333` |
| `QDRANT_API_KEY` | ⚠️ Cloud only | Qdrant Cloud API key (leave blank for local) |
| `OPENAI_API_KEY` | ✅ Yes | OpenAI or compatible LLM API key |
| `OPENAI_BASE_URL` | ✅ Yes | API base URL (`https://api.openai.com/v1`) |
| `OPENAI_MODEL_NAME` | ✅ Yes | Model name (e.g. `gpt-4o-mini`) |
| `LANGCHAIN_TRACING_V2` | ❌ Optional | Set `true` to enable LangSmith tracing |
| `LANGCHAIN_API_KEY` | ❌ Optional | LangSmith API key |
| `SQLITE_DB_PATH` | ❌ Optional | Override DB path (auto-resolved if not set) |