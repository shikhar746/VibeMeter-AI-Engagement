from langgraph.graph import END, StateGraph
from app.models.chat import ChatState
from app.agent.nodes import (
    analyze_and_check_escalation,
    generate_bot_reply,
    trigger_escalation,
    route_conversation,
)


def build_agent() -> StateGraph:
    """Construct and compile the LangGraph workflow."""
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
