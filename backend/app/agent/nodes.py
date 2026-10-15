import json
import logging
import re
from app.agent.llm import get_llm
from app.agent.prompts import get_risk_assessment_messages, get_multi_topic_reply_messages
from app.models.chat import ChatState
from app.data.question_bank import QUESTION_BANK

logger = logging.getLogger(__name__)


def analyze_and_check_escalation(state: ChatState) -> ChatState:
    if state.get("escalate_to_hr"):                       # sticky
        return state
    window = "\n".join(state.get("messages", [])[-6:])    # last few turns, not just one message
    try:
        answer = get_llm().invoke(get_risk_assessment_messages(window)).content.strip().upper()
        is_critical = answer.startswith("YES")            # not `"YES" in answer`
        summary = None
    except Exception:
        logger.exception("Risk check failed, failing safe")
        is_critical = True                                # a human looks, instead of nobody
        summary = "Automated risk check unavailable. Manual review needed."
    out = {**state, "escalate_to_hr": is_critical}
    if summary:
        out["vibe_summary"] = summary
    return out


def generate_bot_reply(state: ChatState) -> ChatState:
    primary_driver = state.get("primary_issue", "general workplace experience")
    messages = state.get("messages", [])
    history = "\n".join(messages[:-1]) if len(messages) > 1 else "(Conversation starting)"
    latest_message = messages[-1] if messages else ""

    all_known = list(QUESTION_BANK.keys())
    covered = list(state.get("covered_topics", []))
    if primary_driver in all_known and primary_driver not in covered:
        covered.append(primary_driver)

    remaining = state.get("remaining_topics", [t for t in all_known if t not in covered])
    prompt_msgs = get_multi_topic_reply_messages(remaining, covered, primary_driver, history, latest_message)

    try:
        raw_text = get_llm().invoke(prompt_msgs).content.strip()
        cleaned_json = re.sub(r"```(?:json)?", "", raw_text).strip() if "```" in raw_text else raw_text
        data = json.loads(cleaned_json)

        bot_reply = data.get("bot_reply", "").strip()
        should_continue = bool(data.get("should_continue", True))
        topic_covered = data.get("topic_covered")
        mood = str(data.get("mood", "neutral")).strip().lower()
        concern_summary = str(data.get("concern_summary", "")).strip()

        if topic_covered and topic_covered in remaining:
            covered.append(topic_covered)
            remaining = [t for t in remaining if t != topic_covered]

        if len(covered) < 2 and not should_continue:
            should_continue = True
            if not bot_reply:
                bot_reply = "I'm glad to hear that! How have things been going with your team and overall workload recently?"

        fallback_msg = "Thank you for taking the time to share your feedback with us. Have a wonderful day!" if not should_continue else "Thank you for sharing. Could you tell me a bit more about your current workload or team setup?"
        bot_msg = f"Bot: {bot_reply or fallback_msg}"

    except Exception as err:
        logger.warning("Structured JSON parsing failed in agent, falling back: %s", err)
        bot_msg = "Bot: Thank you for sharing. How else can we support you in your role?"
        should_continue, mood = True, "neutral"
        concern_summary = state.get("vibe_summary", "Employee provided feedback regarding workplace experience.")

    return {
        **state,
        "messages": state["messages"] + [bot_msg],
        "vibe_summary": concern_summary or state.get("vibe_summary", ""),
        "should_continue": should_continue,
        "mood": mood,
        "covered_topics": covered,
        "remaining_topics": remaining,
    }


def trigger_escalation(state: ChatState) -> ChatState:
    escalation_text = (
        "Bot: I hear you, and I want to make sure you get the right support. "
        "I'm going to confidentially flag this to our HR team so someone "
        "can reach out to you directly."
    )
    return {
        **state,
        "messages": state["messages"] + [escalation_text],
        "escalate_to_hr": True,
        "should_continue": False,
        "mood": "distressed",
        "vibe_summary": state.get("vibe_summary") or "High risk concern escalated to HR.",
    }


def route_conversation(state: ChatState) -> str:
    return "escalate" if state.get("escalate_to_hr") else "reply"
