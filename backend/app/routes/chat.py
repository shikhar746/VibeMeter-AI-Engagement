import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

import app.database as db
from app.limiter import global_key, limiter
from app.data.question_bank import QUESTION_BANK, get_general_opening
from app.agent import chat_engine, ChatState
from app.models.chat import ChatRequest
from app.services.shap_service import get_opening_question
from app.services.chat_service import build_agent_input

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])


@router.post("/start_chat/{employee_id}")
async def start_chat(employee_id: str):
    existing = await db.conversations.find_one({"employee_id": employee_id}, {"_id": 0})
    if existing:
        last_bot = next(
            (m for m in reversed(existing["messages"]) if m.startswith("Bot:")),
            "Bot: Welcome back! How are things going?"
        )
        return {
            "bot_reply": last_bot.removeprefix("Bot: ").strip(),
            "issue": existing["primary_issue"],
            "resumed": True,
        }

    emp_data = await db.employees.find_one({"employee_id": employee_id}, {"_id": 0})
    q_info = get_opening_question(emp_data["top_impact_features"]) if emp_data else get_general_opening()

    all_topics = list(QUESTION_BANK.keys())
    primary_issue = q_info["issue"]
    covered_topics = [primary_issue] if primary_issue in QUESTION_BANK else []
    remaining_topics = [t for t in all_topics if t not in covered_topics]

    await db.conversations.insert_one({
        "employee_id": employee_id,
        "primary_issue": primary_issue,
        "messages": [f"Bot: {q_info['bot_reply']}"],
        "escalate_to_hr": False,
        "vibe_summary": "",
        "is_flagged": emp_data is not None,
        "should_continue": True,
        "mood": "neutral",
        "conversation_status": "active",
        "covered_topics": covered_topics,
        "remaining_topics": remaining_topics,
    })

    return {"bot_reply": q_info["bot_reply"], "issue": q_info["issue"], "resumed": False}


@router.post("/chat")
@limiter.limit("20/minute")
@limiter.limit("200/minute", key_func=global_key)
async def chat_with_bot(request: Request, body: ChatRequest):
    emp_id = body.employee_id
    state = await db.conversations.find_one({"employee_id": emp_id}, {"_id": 0})
    if not state:
        raise HTTPException(status_code=400, detail="Session not initialized. Call /start_chat first.")

    state["messages"].append(f"Employee: {body.message}")

    try:
        agent_input = build_agent_input(state)
        updated_state: ChatState = await run_in_threadpool(chat_engine.invoke, agent_input)
        vibe_summary = updated_state.get("vibe_summary") or state.get("vibe_summary", "")

        await db.conversations.update_one(
            {"employee_id": emp_id},
            {"$set": {
                "messages": updated_state["messages"],
                "escalate_to_hr": updated_state["escalate_to_hr"],
                "vibe_summary": vibe_summary,
                "should_continue": updated_state.get("should_continue", True),
                "mood": updated_state.get("mood", "neutral"),
                "covered_topics": updated_state.get("covered_topics", []),
                "remaining_topics": updated_state.get("remaining_topics", []),
            }}
        )

        last_msg = updated_state["messages"][-1]
        return {
            "bot_reply": last_msg.removeprefix("Bot: ").strip(),
            "escalated": updated_state.get("escalate_to_hr", False),
            "should_continue": updated_state.get("should_continue", True),
            "mood": updated_state.get("mood", "neutral"),
        }

    except Exception:
        # Do not hide outages behind a friendly 200 with escalated=False.
        logger.exception("Chat failed for employee %s", emp_id)
        raise HTTPException(
            status_code=503,
            detail="I'm having a bit of trouble right now. Please try again in a moment.",
        )


@router.post("/end_chat/{employee_id}")
async def end_chat_session(employee_id: str):
    await db.conversations.update_one(
        {"employee_id": employee_id},
        {"$set": {"conversation_status": "closed", "should_continue": False}}
    )
    return {"status": "success", "employee_id": employee_id, "conversation_status": "closed"}
