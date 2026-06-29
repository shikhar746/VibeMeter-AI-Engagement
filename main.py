import os
import re
import json
import pandas as pd

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional

from question_bank import QUESTION_BANK, get_general_opening
from agent import chat_engine, ChatState, llm
import database as db

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
    return {"issue": primary_issue, "bot_reply": question_data["primary"]}


def build_agent_input(state: dict) -> dict:
    """
    Extracts only the keys that ChatState expects so extra DB fields
    (like 'is_flagged', '_id') don't cause TypedDict/LangGraph errors.
    """
    return {
        "employee_id": state["employee_id"],
        "primary_issue": state["primary_issue"],
        "messages": state["messages"],
        "escalate_to_hr": state.get("escalate_to_hr", False),
        "vibe_summary": state.get("vibe_summary", ""),
    }


# ---------------------------------------------------------------------------
# Lifecycle: Resource Management
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect DB and seed employees. Shutdown: close DB."""

    # 1. Connect to MongoDB
    await db.connect_db()

    # 2. Seed employees from CSV (idempotent — upserts, never duplicates)
    csv_path = "engagement_results.csv"
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            selected = df[df["is_selected"] == True]
            count = 0
            for row in selected.to_dict("records"):
                await db.employees.update_one(
                    {"employee_id": str(row["employee_id"])},
                    {"$set": {
                        "employee_id": str(row["employee_id"]),
                        "top_impact_features": parse_shap_string(row["shap_values"]),
                    }},
                    upsert=True,
                )
                count += 1
            print(f"✅ Seeded {count} flagged employees into MongoDB.")
        except Exception as e:
            print(f"🔴 CSV seed error: {e}")
    else:
        print(f"⚠️  {csv_path} not found — skipping seed.")

    yield  # App is live

    # Shutdown
    await db.close_db()


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

# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    employee_id: str
    message: str


class HrLoginRequest(BaseModel):
    password: str


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def verify_hr_token(token: Optional[str]) -> None:
    """
    Raises 403 if the token doesn't match HR_PASSWORD env var.
    Call this at the top of any HR-only endpoint.
    """
    hr_password = os.getenv("HR_PASSWORD")
    if not hr_password:
        raise HTTPException(status_code=500, detail="HR_PASSWORD not configured on server.")
    if token != hr_password:
        raise HTTPException(status_code=403, detail="Forbidden — invalid HR token.")


# ---------------------------------------------------------------------------
# Routes: Employee Outreach
# ---------------------------------------------------------------------------

@app.get("/trigger_outreach")
async def trigger_outreach():
    """Returns all employees flagged for outreach (from MongoDB)."""
    cursor = db.employees.find({}, {"_id": 0})
    employees_list = await cursor.to_list(length=None)
    if not employees_list:
        raise HTTPException(status_code=500, detail="No engagement data in database.")
    return {
        "status": "success",
        "employees_contacted": len(employees_list),
        "data": employees_list,
    }


# ---------------------------------------------------------------------------
# Routes: Chat
# ---------------------------------------------------------------------------

@app.post("/start_chat/{employee_id}")
async def start_chat(employee_id: str):
    """
    Initializes or resumes a chat session for any employee.

    - Flagged employee (in employees collection) → SHAP-driven personalised opener.
    - Unknown employee (not in collection)       → warm general wellbeing check-in.
      We never block an employee from talking.
    """
    # Always check for an existing conversation first (resume regardless of flag status)
    existing = await db.conversations.find_one({"employee_id": employee_id}, {"_id": 0})
    if existing:
        last_bot = next(
            (m for m in reversed(existing["messages"]) if m.startswith("Bot:")),
            "Bot: Welcome back! How are things going?"
        )
        bot_reply = last_bot.removeprefix("Bot: ").strip()
        return {
            "bot_reply": bot_reply,
            "issue": existing["primary_issue"],
            "resumed": True,
        }

    # New conversation — check if they are a flagged employee
    emp_data = await db.employees.find_one({"employee_id": employee_id}, {"_id": 0})

    if emp_data:
        q_info = get_opening_question(emp_data["top_impact_features"])
    else:
        q_info = get_general_opening(employee_id)

    new_conversation = {
        "employee_id": employee_id,
        "primary_issue": q_info["issue"],
        "messages": [f"Bot: {q_info['bot_reply']}"],
        "escalate_to_hr": False,
        "vibe_summary": "",
        "is_flagged": emp_data is not None,
    }
    await db.conversations.insert_one(new_conversation)

    return {
        "bot_reply": q_info["bot_reply"],
        "issue": q_info["issue"],
        "resumed": False,
    }


@app.post("/chat")
async def chat_with_bot(request: ChatRequest):
    """
    Processes an employee message through the LangGraph agent and
    persists the updated conversation + vibe summary to MongoDB.
    """
    emp_id = request.employee_id

    # Load state from DB (exclude _id so it doesn't bleed into the agent)
    state = await db.conversations.find_one({"employee_id": emp_id}, {"_id": 0})
    if not state:
        raise HTTPException(
            status_code=400,
            detail="Session not initialized. Call /start_chat first."
        )

    # Append the employee's new message
    state["messages"].append(f"Employee: {request.message}")

    try:
        # Build a clean input dict containing only ChatState keys
        agent_input = build_agent_input(state)
        updated_state: ChatState = await run_in_threadpool(chat_engine.invoke, agent_input)

        # Generate / refresh a one-sentence vibe summary for the HR dashboard
        history = "\n".join(updated_state["messages"])
        summary_prompt = (
            "In one concise sentence, summarise this employee's main concern and current mood "
            "based on the conversation so far. Be factual and specific, not vague.\n\n"
            f"Conversation:\n{history}"
        )
        try:
            summary_res = await run_in_threadpool(llm.invoke, summary_prompt)
            vibe_summary = summary_res.content.strip()
        except Exception as summary_err:
            print(f"⚠️  Vibe summary generation failed: {summary_err}")
            vibe_summary = state.get("vibe_summary", "")   # keep previous on failure

        # Persist full updated conversation back to MongoDB
        await db.conversations.update_one(
            {"employee_id": emp_id},
            {"$set": {
                "messages": updated_state["messages"],
                "escalate_to_hr": updated_state["escalate_to_hr"],
                "vibe_summary": vibe_summary,
            }}
        )

        # Return the last bot message to the frontend
        last_msg = updated_state["messages"][-1]
        clean_reply = last_msg.removeprefix("Bot: ").strip()

        return {
            "bot_reply": clean_reply,
            "escalated": updated_state.get("escalate_to_hr", False),
        }

    except Exception as exc:
        print(f"🔴 AI Error for {emp_id}: {exc}")
        return {
            "bot_reply": "I'm having a bit of trouble right now. Please try again in a moment.",
            "escalated": False,
        }


# ---------------------------------------------------------------------------
# Routes: Daily Report (admin)
# ---------------------------------------------------------------------------

@app.get("/generate_daily_report")
async def generate_daily_report():
    """
    Aggregates all conversations into an HR report and saves to hr_daily_report.json.
    Uses the vibe_summary already stored in MongoDB where available to save LLM calls.
    """
    cursor = db.conversations.find({}, {"_id": 0})
    all_convos = await cursor.to_list(length=None)

    if not all_convos:
        return {"report": [], "status": "no_data"}

    report_data = []
    for state in all_convos:
        # Re-generate a deeper summary only if the conversation has meaningful content
        history = "\n".join(state["messages"])
        if len(state["messages"]) > 1:
            summary_prompt = (
                "Summarise the core concern and current emotional state of this employee "
                "based on the conversation below. Keep it to two sentences maximum.\n\n"
                f"Conversation:\n{history}"
            )
            try:
                summary_res = await run_in_threadpool(llm.invoke, summary_prompt)
                insight = summary_res.content.strip()
            except Exception:
                insight = state.get("vibe_summary") or "Summary unavailable."
        else:
            insight = state.get("vibe_summary") or "No messages exchanged yet."

        report_data.append({
            "employee_id": state["employee_id"],
            "primary_issue": state["primary_issue"],
            "vibe_summary": insight,
            "escalated": state.get("escalate_to_hr", False),
            "action_item": (
                "🚨 HR Intervention Required"
                if state.get("escalate_to_hr")
                else "Continue Monitoring"
            ),
        })

    with open("hr_daily_report.json", "w") as f:
        json.dump(report_data, f, indent=4)

    return {"status": "success", "report": report_data}


# ---------------------------------------------------------------------------
# Routes: HR Auth
# ---------------------------------------------------------------------------

@app.post("/auth/hr/login")
async def hr_login(request: HrLoginRequest):
    """
    Validates the HR password against the HR_PASSWORD environment variable.
    Returns the password as a bearer token — the frontend stores it and sends
    it as the X-HR-Token header on subsequent protected requests.

    Never hardcode credentials — set HR_PASSWORD in your .env file.
    """
    hr_password = os.getenv("HR_PASSWORD")
    if not hr_password:
        raise HTTPException(status_code=500, detail="HR_PASSWORD not configured on server.")
    if request.password != hr_password:
        raise HTTPException(status_code=401, detail="Incorrect password.")

    # We use the password itself as the token (simple, stateless).
    # For production, replace this with a signed JWT.
    return {"status": "success", "role": "hr", "token": request.password}


# ---------------------------------------------------------------------------
# Routes: HR Dashboard  (protected)
# ---------------------------------------------------------------------------

@app.get("/dashboard/employees")
async def dashboard_employees(x_hr_token: Optional[str] = Header(default=None)):
    """
    Returns aggregated employee + conversation data for the HR dashboard table.
    Requires the X-HR-Token header set to HR_PASSWORD.

    Columns: employee_id, primary_issue, escalated, vibe_summary, message_count.
    """
    verify_hr_token(x_hr_token)

    cursor = db.conversations.find({}, {"_id": 0})
    convos = await cursor.to_list(length=None)

    rows = []
    for c in convos:
        rows.append({
            "employee_id": c["employee_id"],
            "primary_issue": c.get("primary_issue", "—"),
            "escalated": c.get("escalate_to_hr", False),
            "vibe_summary": c.get("vibe_summary") or "Conversation in progress…",
            "message_count": len(c.get("messages", [])),
        })

    # Sort: escalated employees first, then by message count descending
    rows.sort(key=lambda r: (not r["escalated"], -r["message_count"]))

    return {"employees": rows, "total": len(rows)}