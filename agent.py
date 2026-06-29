import os
from dotenv import load_dotenv
load_dotenv()
from typing import TypedDict, List

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

# ---------------------------------------------------------------------------
# 1. State Definition
# ---------------------------------------------------------------------------

class ChatState(TypedDict):
    """Represents the state of the interactive HR conversation."""
    employee_id: str
    primary_issue: str
    messages: List[str]
    escalate_to_hr: bool
    vibe_summary: str

# ---------------------------------------------------------------------------
# 2. LLM Initialisation
# ---------------------------------------------------------------------------

def get_llm():
    """Initialises the Groq LLM with safety checks."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")
    
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.4, # Slightly lower temperature for more consistent HR replies
        api_key=api_key,
    )

llm = get_llm()

# ---------------------------------------------------------------------------
# 3. Graph Nodes (Business Logic)
# ---------------------------------------------------------------------------

def analyze_and_check_escalation(state: ChatState) -> ChatState:
    """Analyzes sentiment to determine if HR intervention is required."""
    latest_msg = state["messages"][-1]
    
    system_prompt = SystemMessage(content=(
        "You are a Risk Assessment AI. Analyze the employee feedback for severe "
        "distress, harassment, or workplace toxicity. Reply ONLY with 'YES' or 'NO'."
    ))
    human_prompt = HumanMessage(content=f"Feedback: {latest_msg}")

    response = llm.invoke([system_prompt, human_prompt])
    is_critical = "YES" in response.content.strip().upper()

    # Create a clean state update
    return {**state, "escalate_to_hr": state["escalate_to_hr"] or is_critical}


def generate_bot_reply(state: ChatState) -> ChatState:
    """Generates an empathetic response tailored to the identified issue."""
    issue = state["primary_issue"]
    history = "\n".join(state["messages"])

    system_prompt = SystemMessage(content=(
        "You are an empathetic Deloitte HR Assistant. Provide a short, supportive "
        "reply and ask exactly one follow-up question. Do not use prefixes."
    ))
    human_prompt = HumanMessage(content=(
        f"Context: The issue is {issue}.\n"
        f"Conversation History:\n{history}"
    ))

    response = llm.invoke([system_prompt, human_prompt])
    bot_msg = f"Bot: {response.content.strip()}"
    
    return {**state, "messages": state["messages"] + [bot_msg]}


def trigger_escalation(state: ChatState) -> ChatState:
    """Informs the employee that their concern is being escalated to HR."""
    escalation_text = (
        "Bot: I hear you, and I want to make sure you get the right support. "
        "I'm going to confidentially flag this to our HR team so someone "
        "can reach out to you directly."
    )
    
    return {
        **state, 
        "messages": state["messages"] + [escalation_text],
        "escalate_to_hr": True
    }

# ---------------------------------------------------------------------------
# 4. Routing Logic
# ---------------------------------------------------------------------------

def route_conversation(state: ChatState) -> str:
    """Conditional routing based on the escalation flag."""
    return "escalate" if state.get("escalate_to_hr") else "reply"

# ---------------------------------------------------------------------------
# 5. Graph Compilation
# ---------------------------------------------------------------------------

def build_agent():
    """Constructs the LangGraph workflow."""
    builder = StateGraph(ChatState)

    builder.add_node("analyze", analyze_and_check_escalation)
    builder.add_node("generate_reply", generate_bot_reply)
    builder.add_node("escalate", trigger_escalation)

    builder.set_entry_point("analyze")

    builder.add_conditional_edges(
        "analyze",
        route_conversation,
        {
            "escalate": "escalate",
            "reply": "generate_reply",
        },
    )

    builder.add_edge("generate_reply", END)
    builder.add_edge("escalate", END)

    return builder.compile()

chat_engine = build_agent()