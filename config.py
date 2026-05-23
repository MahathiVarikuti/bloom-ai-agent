# config.py - Central configuration for the Bloom AI Agent

MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 1024
SOP_PATH = "sop.json"

# How many FAQ exchanges before Aria proactively offers qualification
FAQ_EXCHANGES_BEFORE_QUALIFY = 2

# Qualification questions asked in order, one at a time
QUALIFICATION_QUESTIONS = [
    "treatment_interest",
    "prior_experience",
    "booking_timeframe"
]

# Deterministic escalation keywords — checked BEFORE the model call.
# If any of these appear in the customer's message, we escalate immediately
# without waiting for the AI to decide. Fast, reliable, no false negatives.
ESCALATION_KEYWORDS = [
    "complaint",
    "complain",
    "angry",
    "furious",
    "disgusted",
    "refund",
    "manager",
    "supervisor",
    "hurt",
    "pain",
    "allergic",
    "reaction",
    "sue",
    "lawyer",
    "unacceptable",
]

COLORS = {
    "reset":    "\033[0m",
    "bold":     "\033[1m",
    "dim":      "\033[2m",
    "cyan":     "\033[96m",
    "green":    "\033[92m",
    "yellow":   "\033[93m",
    "red":      "\033[91m",
    "magenta":  "\033[95m",
    "white":    "\033[97m",
}
