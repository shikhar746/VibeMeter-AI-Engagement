from typing import List
from pydantic import BaseModel
from typing_extensions import TypedDict


class ChatRequest(BaseModel):
    employee_id: str
    message: str


class ChatState(TypedDict):
    """Represents the state of an interactive HR conversation."""

    employee_id: str
    primary_issue: str
    messages: List[str]
    escalate_to_hr: bool
    vibe_summary: str
    should_continue: bool
    mood: str
    covered_topics: List[str]
    remaining_topics: List[str]
