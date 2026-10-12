import json
from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

import app.database as db
from app.agent.llm import llm

router = APIRouter(tags=["Reports"])


@router.get("/generate_daily_report")
async def generate_daily_report():
    """
    Aggregates all conversations into an HR report and saves to hr_daily_report.json.
    """
    cursor = db.conversations.find({}, {"_id": 0})
    all_convos = await cursor.to_list(length=None)

    if not all_convos:
        return {"report": [], "status": "no_data"}

    report_data = []
    for state in all_convos:
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

    def _write_report():
        with open("hr_daily_report.json", "w") as f:
            json.dump(report_data, f, indent=4)

    await run_in_threadpool(_write_report)

    return {"status": "success", "report": report_data}
