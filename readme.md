# Deloitte VibeMeter

**Proactive employee engagement outreach, powered by SHAP-driven insights and an LLM agent.**

VibeMeter closes the gap between predictive HR analytics and actual human follow-up. Instead of waiting for the next annual survey, it takes employees already flagged as "at risk" by an upstream ML model, figures out *why* (via SHAP feature attributions), and starts a natural, empathetic check-in conversation with them — escalating to HR automatically if things look serious.

---

## How it works

1. **Data hydration** — On startup, the backend reads `engagement_results.csv` and keeps only employees flagged `is_selected = True`.
2. **SHAP parsing** — Each employee's `shap_values` string (e.g. `"Average_Vibe_Score(0.0323), Total_Reward_Points(0.0290), ..."`) is parsed and sorted by absolute impact, so we know the single biggest driver of that employee's risk score.
3. **Question mapping** — The top SHAP feature is mapped to a hand-written, empathetic opening question from `question_bank.py` (e.g. high `Average_Work_Hours` impact → "I noticed you've been putting in quite a few hours lately...").
4. **Conversation** — The employee replies through the chat UI. Each message is routed through a [LangGraph](https://www.langchain.com/langgraph) agent that:
   - Checks the message for signs of severe distress, harassment, or toxicity.
   - If flagged: tells the employee it's escalating to HR.
   - Otherwise: generates a short, empathetic, contextual follow-up question via an LLM.
5. **Reporting** — At any point, HR can pull a summary of every active conversation, with a recommended action per employee, saved to `hr_daily_report.json`.

---

## Tech stack

| Layer | Tech |
|---|---|
| API | FastAPI |
| Agent orchestration | LangGraph + LangChain Core |
| LLM | Llama-3.3-70B-Versatile via Groq |
| Data | Pandas, regex-based SHAP parsing |
| Frontend | React 19 + Vite, plain CSS |
| HTTP client | Axios |

---

## Project structure

```
.
├── main.py                   # FastAPI app, routes, CSV loading, lifecycle
├── agent.py                  # LangGraph state machine (risk check → reply / escalate)
├── question_bank.py          # SHAP feature → opening question mapping
├── engagement_results.csv    # Employee data + SHAP attributions (input)
├── hr_daily_report.json      # Generated report (output, created at runtime)
├── requirements.txt          # Python dependencies
├── .env                      # GROQ_API_KEY (not committed)
└── frontend/
    ├── src/
    │   ├── App.jsx            # Admin panel + chat UI
    │   ├── App.css            # Styling
    │   └── main.jsx
    ├── package.json
    └── vite.config.js
```

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 20.19+ (required by the Vite 8 beta used here)
- A [Groq API key](https://console.groq.com/) (free tier works)

### 1. Backend

```bash
# Clone and enter the project
git clone <repo-url>
cd <repo-name>

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn pandas pydantic langchain-core langgraph langchain-groq python-dotenv

# Configure your Groq API key
echo "GROQ_API_KEY=gsk_your_key_here" > .env

# Run the API
uvicorn main:app --reload --port 8000
```

The server loads `engagement_results.csv` on startup and prints how many employees were flagged for outreach.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

This starts the Vite dev server (default `http://localhost:5173`). The frontend is hardcoded to talk to the backend at `http://127.0.0.1:8000` — update `API_BASE_URL` in `src/App.jsx` if you change the backend port or host.

---

## API reference

### `GET /trigger_outreach`
Returns every employee flagged for outreach, with their top SHAP-ranked features.

```bash
curl http://127.0.0.1:8000/trigger_outreach
```

### `POST /start_chat/{employee_id}`
Initializes a session for an employee and returns their personalized opening question.

```bash
curl -X POST http://127.0.0.1:8000/start_chat/EMP0345
```

### `POST /chat`
Sends an employee's message into the LangGraph agent and gets a reply back.

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"employee_id": "EMP0345", "message": "Honestly things have been pretty stressful lately."}'
```

### `GET /generate_daily_report`
Summarizes all active conversations into an HR action report and writes it to `hr_daily_report.json`.

```bash
curl http://127.0.0.1:8000/generate_daily_report
```

---

## Using the app

1. Run both servers (backend on `:8000`, frontend on `:5173`).
2. Open the frontend in your browser.
3. Click **Trigger Daily Data Load** to simulate the outreach batch job.
4. Enter an employee ID from `engagement_results.csv` (e.g. `EMP0345`) where `is_selected` is `TRUE`, and click **Start Chat**.
5. Chat as that employee. If your message reads as distressed or describes harassment/toxicity, the agent will escalate and flag the conversation to HR.

---

## Known limitations

- **No persistence** — `active_chats` and the loaded CSV data live only in memory. Restarting the backend clears every in-progress conversation.
- **No authentication** — any employee ID can be used to start a session; there's no real login behind it.
- **CORS is wide open** (`allow_origins=["*"]`) — fine for local development, but should be locked down before any real deployment, especially given this handles sensitive wellbeing data.
- **Single-instance only** — in-memory state won't work correctly if you ever run multiple backend instances behind a load balancer.

---

## License

Internal tool — Deloitte People & Purpose.