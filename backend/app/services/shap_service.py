import re
import pandas as pd
from app.data.question_bank import QUESTION_BANK


def parse_shap_string(shap_string: str) -> dict:
    """Parses SHAP strings like 'feature(0.8)'. Handles scientific notation."""
    if pd.isna(shap_string):
        return {}
    pattern = r"([a-zA-Z0-9_\s]+)\(([-0-9.eE+]+)\)"
    matches = re.findall(pattern, shap_string)
    parsed = {feat.strip(): float(val) for feat, val in matches}
    return dict(sorted(parsed.items(), key=lambda x: abs(x[1]), reverse=True))


def get_opening_question(top_impact_features: dict) -> dict:
    """Maps the top SHAP feature to a personalized opening question."""
    if not top_impact_features:
        return {
            "issue": "general",
            "bot_reply": "Hi there! Just checking in to see how your week is going?",
        }
    primary_issue = list(top_impact_features.keys())[0]
    question_data = QUESTION_BANK.get(
        primary_issue,
        {"primary": "Hi there! I wanted to do a quick check-in. How have things been at work?"}
    )
    return {"issue": primary_issue, "bot_reply": question_data["primary"]}
