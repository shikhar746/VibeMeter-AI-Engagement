from langchain_core.messages import SystemMessage, HumanMessage


def get_risk_assessment_messages(conversation: str):
    system_prompt = SystemMessage(content=(
        "You are a Risk Assessment AI. Read the recent conversation and decide whether the "
        "employee shows severe distress, harassment, or workplace toxicity. "
        "Reply with exactly one word: YES or NO."
    ))
    human_prompt = HumanMessage(content=f"Recent conversation:\n{conversation}")
    return [system_prompt, human_prompt]


def get_multi_topic_reply_messages(
    remaining_topics: list,
    covered_topics: list,
    primary_driver: str,
    history: str,
    latest_message: str,
):
    system_prompt = SystemMessage(content=(
        "You are an empathetic HR check-in assistant analyzing an ongoing check-in conversation.\n\n"
        f"Topics still to explore: {remaining_topics}\n"
        f"Topics already covered: {covered_topics}\n"
        f"Primary concern category: {primary_driver}\n\n"
        "Rules:\n"
        "- Do NOT close the conversation if fewer than 2 topics have been covered, even if the employee sounds fine. "
        "A short \"I'm good\" on turn 1 means probe gently, not exit.\n"
        "- Close only if the employee has clearly signaled they're done AND at least 2 topics are covered, OR clear distress requiring escalation.\n"
        "- Ask about one uncovered topic at a time, informed by primary_driver first.\n\n"
        "Respond ONLY in this JSON format, no extra text:\n"
        "{\n"
        '  "bot_reply": "<warm response + at most one follow-up question, empty string if closing>",\n'
        '  "should_continue": true or false,\n'
        '  "topic_covered": "<topic key just addressed, or null>",\n'
        '  "mood": "<one word: positive/neutral/negative/distressed>",\n'
        '  "concern_summary": "<one factual sentence on their main concern right now>"\n'
        "}"
    ))

    human_prompt = HumanMessage(content=(
        f"Conversation so far:\n{history}\n\n"
        f"Employee's latest message:\n{latest_message}"
    ))
    return [system_prompt, human_prompt]
