import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Header

import app.database as db
from app.config import HR_PASSWORD
from app.models.hr import HrLoginRequest
from app.services.hr_service import verify_hr_token

router = APIRouter(tags=["HR"])


@router.post("/auth/hr/login")
async def hr_login(request: HrLoginRequest):
    """
    Validates the HR password against the HR_PASSWORD environment variable.
    """
    hr_password = os.getenv("HR_PASSWORD", HR_PASSWORD)
    if not hr_password:
        raise HTTPException(status_code=500, detail="HR_PASSWORD not configured on server.")
    if request.password != hr_password:
        raise HTTPException(status_code=401, detail="Incorrect password.")

    return {"status": "success", "role": "hr", "token": request.password}


@router.get("/dashboard/employees")
async def dashboard_employees(x_hr_token: Optional[str] = Header(default=None)):
    """
    Returns aggregated employee + conversation data for the HR dashboard table.
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

    rows.sort(key=lambda r: (not r["escalated"], -r["message_count"]))

    return {"employees": rows, "total": len(rows)}
