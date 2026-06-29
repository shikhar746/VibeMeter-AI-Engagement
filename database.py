# question_bank.py

QUESTION_BANK = {
    # Category 1: Work-Life Balance
    "Average_Work_Hours": {
        "primary": "I noticed you've been putting in quite a few hours lately. How are you holding up, and are you finding enough time to disconnect and recharge?",
        "follow_up": "Is there anything specific on your plate right now that's demanding so much of your time? Maybe we can look into balancing the load."
    },
    "Days_since_last_leave": {
        "primary": "It looks like it's been a while since you took some time off to unwind. Have you been able to take any breaks recently?",
        "follow_up": "Taking time for yourself is important. Is there a project keeping you from taking a few days off, or just haven't gotten around to it?"
    },

    # Category 2: Recognition & Rewards
    "Total_Reward_Points": {
        "primary": "We really value your contributions here. I wanted to check in—do you feel like your hard work and achievements are being recognized by the team?",
        "follow_up": "What kind of recognition means the most to you? (e.g., public shoutouts, project opportunities, or platform rewards?)"
    },
    "Days_since_last_reward": {
        "primary": "I want to make sure your efforts aren't going unnoticed. Do you feel you've had recent wins that haven't been fully celebrated?",
        "follow_up": "Could you share one recent accomplishment you're particularly proud of?"
    },

    # Category 3: Career Growth
    "Latest_Promotion_Consideration": {
        "primary": "I'd love to hear about your career goals. Do you feel like you have a clear path for growth and development in your current role?",
        "follow_up": "Are there any specific skills or new responsibilities you've been hoping to take on recently?"
    },

    # Category 4: Team Culture & Environment
    "Average_Team_Messages_Sent": {
        "primary": "Working collaboratively is a big part of our culture. How are things going with your team lately? Do you feel connected with everyone?",
        "follow_up": "Sometimes remote or hybrid setups can make communication tricky. Is there anything that would help you collaborate more easily with your peers?"
    },

    # Category 5: Management & Performance
    "Average_Manager_Feedback_Score": {
        "primary": "Feedback is crucial for us to support you. How would you describe the guidance and feedback you're currently receiving from your manager?",
        "follow_up": "Do you feel you have enough 1-on-1 time to discuss your progress and any roadblocks you're facing?"
    },

    # Generic fallback based on Vibemeter
    "Average_Vibe_Score": {
        "primary": "I've noticed your recent vibe check-ins haven't been the highest. I just wanted to reach out and see how you're truly doing. What's been on your mind lately?",
        "follow_up": "Is there anything specific at work causing you frustration, or just a general feeling of being overwhelmed?"
    }
}


# Rotating general questions for employees not in the flagged CSV.
# The bot picks one based on a simple hash of the employee ID so the
# same person always gets the same opener (consistent, not random).
GENERAL_QUESTIONS = [
    "Hey! Just dropping in for a quick check-in. How has work been feeling for you lately — any highlights or low points from the past few weeks?",
    "Hi there! I wanted to take a moment to see how you're doing. Is there anything on your mind about work, your team, or your day-to-day that you'd like to talk through?",
    "Hello! I'm here for a confidential chat whenever you need it. To start — how would you describe your overall energy and motivation at work right now?",
    "Hi! Quick check-in from the People team. On a scale of 'cruising along' to 'could really use some support' — where are you landing these days?",
    "Hey, glad you're here. Sometimes it helps just to talk. What's one thing about your current role that's going well, and one thing that's been a bit of a challenge?",
]


def get_general_opening(employee_id: str) -> dict:
    """
    Returns a consistent general opening question for employees not in the
    flagged dataset, chosen deterministically from GENERAL_QUESTIONS.
    """
    index = hash(employee_id) % len(GENERAL_QUESTIONS)
    return {
        "issue": "general_checkin",
        "bot_reply": GENERAL_QUESTIONS[index],
    }