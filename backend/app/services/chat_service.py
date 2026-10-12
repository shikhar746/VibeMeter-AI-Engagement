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
        "should_continue": state.get("should_continue", True),
        "mood": state.get("mood", "neutral"),
        "covered_topics": state.get("covered_topics", []),
        "remaining_topics": state.get("remaining_topics", []),
    }
