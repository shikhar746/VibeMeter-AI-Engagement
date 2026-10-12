from fastapi import APIRouter
import app.database as db

router = APIRouter(tags=["Outreach"])


@router.get("/trigger_outreach")
async def trigger_outreach():
    """Returns all employees flagged for outreach (from MongoDB)."""
    cursor = db.employees.find({}, {"_id": 0})
    employees_list = await cursor.to_list(length=None)
    if not employees_list:
        return {"status": "success", "employees_contacted": 0, "data": []}
    return {
        "status": "success",
        "employees_contacted": len(employees_list),
        "data": employees_list,
    }
