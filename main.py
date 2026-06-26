import os
import re
import json
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from contextlib import asynccontextmanager
from pydantic import BaseModel

from question_bank import QUESTION_BANK
from agent import chat_engine, ChatState, llm

# ---------------------------------------------------------------------------
# In-memory Persistent Stores
# ---------------------------------------------------------------------------
cached_engagement_data: list = []
active_chats: dict = {}

# ---------------------------------------------------------------------------
# Business Logic Helpers
# ---------------------------------------------------------------------------

def parse_shap_string(shap_string: str) -> dict:
    """Parses SHAP strings like 'feature(0.8)'. Handles scientific notation."""
    if pd.isna(shap_string):
        return {}

    pattern = r"([a-zA-Z0-9_\s]+)\(([-0-9.eE+]+)\)"
    matches = re.findall(pattern, shap_string)
    parsed = {feat.strip(): float(val) for feat, val in matches}
    
    # Sort by absolute impact descending
    return dict(sorted(parsed.items(), key=lambda x: abs(x[1]), reverse=True))


def get_opening_question(top_impact_features: dict) -> dict:
    """Maps the top SHAP feature to a personalized opening question."""
    if not top_impact_features:
        return {
            "issue": "general",
            "bot_reply": "Hi there! Just checking in to see how your week is going?",
        }

    primary_issue = list(top_impact_features.keys())[0]
    question_data = QUESTION_BANK.get(
        primary_issue,
        {"primary": "Hi there! I wanted to do a quick check-in. How have things been at work?"}
    )

    return {
        "issue": primary_issue,
        "bot_reply": question_data["primary"],
    }


# ---------------------------------------------------------------------------
# Lifecycle: Resource Management
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup CSV loading and shutdown cleanup."""
    global cached_engagement_data
    csv_path = "engagement_results.csv"

    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            # Only load employees flagged for outreach
            selected = df[df["is_selected"] == True]

            cached_engagement_data = [
                {
                    "employee_id": str(row["employee_id"]),
                    "top_impact_features": parse_shap_string(row["shap_values"]),
                }
                for row in selected.to_dict("records")
            ]
            print(f"✅ Startup: Loaded {len(cached_engagement_data)} flagged employees.")
        except Exception as e:
            print(f"🔴 Startup Error: {e}")
    else:
        print(f"⚠️ Warning: {csv_path} not found.")

    yield  # Server is serving requests

    cached_engagement_data.clear()
    active_chats.clear()


# ---------------------------------------------------------------------------
# API Setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Deloitte VibeMeter API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    employee_id: str
    message: str


# ---------------------------------------------------------------------------
# Routes: Core Functionality
# ---------------------------------------------------------------------------

@app.get("/trigger_outreach")
def trigger_outreach():
    """Identifies and returns the list of disengaged employees."""
    if not cached_engagement_data:
        raise HTTPException(status_code=500, detail="No engagement data loaded.")
    
    return {
        "status": "success",
        "employees_contacted": len(cached_engagement_data),
        "data": cached_engagement_data
    }


@app.post("/start_chat/{employee_id}")
def start_chat(employee_id: str):
    """Initializes a stateful session with a personalized opening message."""
    emp_data = next((e for e in cached_engagement_data if e["employee_id"] == employee_id), None)
    
    if not emp_data:
        raise HTTPException(status_code=404, detail="Employee not found or not flagged.")

    q_info = get_opening_question(emp_data["top_impact_features"])

    # Initializing LangGraph state as a plain dict
    active_chats[employee_id] = {
        "employee_id": employee_id,
        "primary_issue": q_info["issue"],
        "messages": [f"Bot: {q_info['bot_reply']}"],
        "escalate_to_hr": False,
        "vibe_summary": "",
    }

    return {
        "bot_reply": q_info["bot_reply"],
        "issue": q_info["issue"],
    }


@app.post("/chat")
async def chat_with_bot(request: ChatRequest):
    """Processes user messages through the Agentic AI pipeline."""
    emp_id = request.employee_id

    if emp_id not in active_chats:
        raise HTTPException(status_code=400, detail="Session not initialized.")

    state = active_chats[emp_id]
    state["messages"].append(f"Employee: {request.message}")

    try:
        # Using threadpool for non-blocking LLM execution
        updated_state: ChatState = await run_in_threadpool(chat_engine.invoke, state)
        active_chats[emp_id] = updated_state
        
        last_msg = updated_state["messages"][-1]
        clean_reply = last_msg.removeprefix("Bot: ").strip()

        return {
            "bot_reply": clean_reply,
            "escalated": updated_state.get("escalate_to_hr", False),
        }
    except Exception as exc:
        print(f"🔴 AI Error for {emp_id}: {exc}")
        return {"bot_reply": "I'm having a bit of trouble. Please try again later.", "escalated": False}


@app.get("/generate_daily_report")
async def generate_daily_report():
    """Aggregates active chats into an HR insight report and saves to disk."""
    if not active_chats:
        return {"report": [], "status": "no_data"}
    
    report_data = []
    for emp_id, state in active_chats.items():
        history = "\n".join(state["messages"])
        summary_prompt = f"Summarize the core reason for this employee's vibe and their current mood: {history}"
        
        try:
            summary_res = await run_in_threadpool(llm.invoke, summary_prompt)
            insight = summary_res.content.strip()
        except:
            insight = "Summary unavailable due to LLM error."
        
        report_data.append({
            "employee_id": emp_id,
            "primary_issue": state["primary_issue"],
            "vibe_summary": insight,
            "escalated": state["escalate_to_hr"],
            "action_item": "HR Intervention Required" if state["escalate_to_hr"] else "Continue Monitoring"
        })

    # Save a physical copy for HR audit
    with open("hr_daily_report.json", "w") as f:
        json.dump(report_data, f, indent=4)
        
    return {"status": "success", "report": report_data}