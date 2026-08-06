# ⚡ VibeMeter

> **AI-Powered Employee Engagement & Risk Mitigation System**  
> Converts SHAP-based attrition risk signals into proactive, empathetic outreach conversations with real-time HR escalation.

---

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# Activate venv: source .venv/bin/activate (Linux/Mac) or .venv\Scripts\activate (Windows)
pip install -r requirements.txt
cp .env.example .env   # Set GROQ_API_KEY, MONGODB_URI, HR_PASSWORD
uvicorn main:app --reload --port 8000
```
*Look for `✅ SUCCESS: Connected to MongoDB` in your terminal.*

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Open [http://localhost:5173](http://localhost:5173) in your browser.*

---

## 🛠️ Architecture & Tech Stack

```
[ SHAP Data CSV ] ➔ ( Startup Seeding ) ➔ [ MongoDB ]
                                             │
[ React 19 Frontend ] ── POST /chat ──► [ FastAPI Async Engine ]
                                             │
                                   [ LangGraph 3-Node Agent ]
                                             │
                        ┌────────────────────┴────────────────────┐
                        ▼                                         ▼
            [ Empathetic Dialogue ]                    [ HR Escalation Flag ]
```

| Layer | Stack | Purpose |
|---|---|---|
| **Backend** | FastAPI + Uvicorn | High-performance asynchronous API service |
| **AI Agent** | LangGraph + Llama 3.3 (Groq) | Intelligent conversation routing & risk evaluation |
| **Database** | MongoDB (Motor Driver) | Async persistence for chats & employee profiles |
| **Frontend** | React 19 + Vite + Axios | Real-time chat interface & HR management dashboard |

---

## ✨ Key Features

- 🎯 **SHAP Personalisation:** Automatically crafts opening questions tailored to top attrition drivers (Work-Life, Growth, Management, Recognition).
- 🛡️ **Autonomous HR Escalation:** Continuous toxicity & distress detection flags high-risk conversations instantly.
- 📊 **Live HR Dashboard:** Secure, token-gated portal giving HR teams real-time visibility into employee sentiment and priority alerts.
- 💾 **Session Resilience:** Persistent chat history allows employees to resume check-ins anytime seamlessly.
- 🔄 **Idempotent Data Seeding:** Ingests SHAP CSV records without duplication on server startup.

---

## 📡 API Overview

- `POST /start_chat/{employee_id}` — Initialise/resume check-in session.
- `POST /chat` — Send message and receive AI agent response.
- `POST /auth/hr/login` — HR portal authentication.
- `GET /dashboard/employees` — Fetch prioritized employee risk list (Requires `X-HR-Token`).
- `GET /generate_daily_report` — Export structured JSON report for HR analytics.

---

## ⚙️ Environment Configuration

Create `backend/.env` with the following keys:

| Key | Description | Default |
|---|---|---|
| `GROQ_API_KEY` | Groq API Key for LLM Inference | *(Required)* |
| `MONGODB_URI` | MongoDB Connection String | `mongodb://localhost:27017` |
| `HR_PASSWORD` | Password for HR Dashboard | *(Required)* |
| `ENGAGEMENT_CSV_PATH` | Path to SHAP engagement data | `data/engagement_results.csv` |

---

## 📂 Project Structure

```
.
├── backend/          # FastAPI server, LangGraph agent, DB models
│   ├── data/         # Raw CSV input files
│   ├── main.py       # API entry point & lifespan triggers
│   ├── agent.py      # LangGraph risk routing logic
│   └── database.py   # Motor MongoDB async client
└── frontend/         # React SPA, UI components, dashboard modal
```