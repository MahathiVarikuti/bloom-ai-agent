# agent.py - Core conversation agent for Bloom Aesthetics Clinic
#
# Architecture:
#   - Single model call per turn, returning structured JSON
#   - Stage machine: FAQ → QUALIFICATION → (back to FAQ) | ESCALATED at any point
#   - Session state is maintained in memory; saved to disk on exit

import os
import re
import json
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from openai import OpenAI

from config import MODEL, MAX_TOKENS, SOP_PATH, ESCALATION_KEYWORDS


class Stage(Enum):
    FAQ = "faq"
    QUALIFICATION = "qualification"
    ESCALATED = "escalated"


@dataclass
class AgentResponse:
    """What gets returned to the CLI after each turn."""
    message: str
    escalated: bool = False
    escalation_reason: Optional[str] = None
    confidence: str = "high"
    stage: Stage = Stage.FAQ
    sop_gap: Optional[str] = None


@dataclass
class SessionState:
    stage: Stage = Stage.FAQ
    messages: list = field(default_factory=list)
    qualification_data: dict = field(default_factory=dict)
    escalation_log: list = field(default_factory=list)
    sop_gaps: list = field(default_factory=list)
    faq_exchanges: int = 0
    qualification_q_index: int = 0   # which question we're on (0-2)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ---------------------------------------------------------------------------
# Stage-specific instructions injected into the system prompt dynamically.
# Keeping these separate makes it easy to tune each stage independently.
# ---------------------------------------------------------------------------

STAGE_INSTRUCTIONS = {
    Stage.FAQ: """
## CURRENT STAGE: FAQ

Answer the customer's questions using only the SOP data above.
Be friendly and concise — 2 to 3 sentences is usually the right length.

After {faq_threshold} or more exchanges, if it feels natural, you may offer:
"I'd love to help point you in the right direction — would you mind if I asked a couple of quick questions?"
If the customer agrees, include "next_stage": "qualification" in your JSON response.
If they decline, that's completely fine — just continue answering questions.
""",
    Stage.QUALIFICATION: """
## CURRENT STAGE: LEAD QUALIFICATION

You're now gathering information to qualify this lead. Ask exactly ONE question per turn, in this order:

Question 1 (treatment_interest):
  "What treatment are you most interested in — Botox, fillers, or would you prefer to explore during a free consultation?"

Question 2 (prior_experience):
  "Have you had any aesthetic treatments before, or would this be your first time?"

Question 3 (booking_timeframe):
  "Are you looking to book in the next week or two, or is your timeline a bit more flexible?"

Current question index: {q_index} (0 = first question, 1 = second, 2 = third)
So right now, ask question number {q_number}.

Store each answer in "qualification_update" as a key-value pair.
Once you have asked and received an answer to question 3, set "qualification_complete": true.
After qualification is complete, naturally transition: "Great, that's really helpful — is there anything else I can answer for you?"
""",
    Stage.ESCALATED: """
## CURRENT STAGE: ESCALATED

This conversation has been flagged and will be handed off to a human team member.
Let the customer know warmly that someone from the team will be in touch very soon.
Offer to take a note of anything else they'd like to add before the team follows up.
Do not attempt to answer any further questions — leave those for the team.
"""
}


class BloomAgent:
    """
    Aria - the AI support agent for Bloom Aesthetics Clinic.

    Handles inbound customer enquiries across four stages:
    1. FAQ answering (SOP-grounded only)
    2. Lead qualification (3 structured questions)
    3. Escalation detection (automatic, rule-based)
    4. Session summarisation (separate summariser prompt)
    """

    def __init__(self, sop_path: str = SOP_PATH):
        self.client = OpenAI(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        self.sop = self._load_sop(sop_path)
        self.session = SessionState()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_sop(self, path: str) -> dict:
        with open(path, "r") as f:
            return json.load(f)

    def _build_system_prompt(self) -> str:
        sop_str = json.dumps(self.sop, indent=2)

        # Fill in dynamic values in stage instructions
        stage = self.session.stage
        q_index = self.session.qualification_q_index
        instructions = STAGE_INSTRUCTIONS[stage].format(
            faq_threshold=2,
            q_index=q_index,
            q_number=q_index + 1
        )

        # Inject any qualification data already collected so Aria remembers it
        qual_context = ""
        if self.session.qualification_data:
            qual_context = f"""
<qualification_already_collected>
{json.dumps(self.session.qualification_data, indent=2)}
</qualification_already_collected>
"""

        return f"""You are Aria, a warm and professional customer support assistant for Bloom Aesthetics Clinic.

<sop>
{sop_str}
</sop>

<core_rules>
These rules are non-negotiable:

1. ONLY answer using information present in the <sop> above.
   If something is not in the SOP, say so honestly - never guess or make things up.
   A good phrase: "I don't have that detail to hand, but one of our team can help - shall I flag that for you?"

2. NEVER invent prices, services, availability, medical advice, staff names, or any other facts.

3. ALWAYS return ONLY a single raw valid JSON object in this exact format.
Do not include explanations.
Do not include markdown.
Do not wrap the JSON in code fences.

{{
  "message": "Your warm, conversational response to the customer",
  "escalate": false,
  "escalation_reason": null,
  "confidence": "high",
  "sop_gap": null,
  "qualification_update": {{}},
  "next_stage": null,
  "qualification_complete": false
}}
</core_rules>

<escalation_rules>
Set "escalate": true (and give an "escalation_reason") when ANY of these occur:
- Customer is frustrated, upset, angry, or making a complaint
- Customer asks a medical question: risks, side effects, contraindications, allergies, health conditions
- Customer wants to negotiate, challenge, or dispute a price
- You cannot answer 2 or more consecutive questions from the SOP
- Customer explicitly asks to speak to a human, a real person, or someone from the team

When escalating, your message should still be warm and reassuring - not robotic.
</escalation_rules>

<confidence_guide>
"high"   - Answer is fully and clearly covered by the SOP
"medium" - Partially covered; some details are missing from the SOP
"low"    - Mostly or entirely outside the SOP scope
</confidence_guide>

{instructions}
{qual_context}

<tone>
Warm, calm, and genuinely helpful - not scripted. Customers at an aesthetics clinic may feel nervous or uncertain; your job is to make them feel at ease and informed.
Keep replies concise (2-3 sentences is usually right). Use British English spellings (e.g. "enquiry", "colour", "organise").
Avoid being pushy, salesy, or over-formal. If you're unsure about something, always offer a human rather than guessing.
</tone>"""

    def _parse_response(self, raw: str) -> dict:
        """
        Parse the model's JSON response robustly.
        Strips markdown fences and falls back gracefully if parsing fails.
        """
        clean = raw.strip()
        # Remove markdown code fences if present
        if "```" in clean:
            clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.MULTILINE)
            clean = re.sub(r"\s*```$", "", clean, flags=re.MULTILINE)
            clean = clean.strip()

        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            # Try to extract a JSON object from anywhere in the response
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass

            # Last resort: return a safe fallback so the app doesn't crash
            return {
                "message": "I'm so sorry, something went a bit wrong on my end. Could you repeat that?",
                "escalate": False,
                "escalation_reason": None,
                "confidence": "low",
                "sop_gap": "Response parsing failed - raw output was not valid JSON",
                "qualification_update": {},
                "next_stage": None,
                "qualification_complete": False
            }

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def chat(self, user_input: str) -> AgentResponse:
        """
        Process a single user message and return a structured response.
        This is the main entry point called by the CLI on every turn.
        """
        self.session.messages.append({
            "role": "user",
            "content": user_input
        })

        # --- Deterministic keyword check (runs BEFORE the model) ---
        # This catches obvious escalation triggers instantly, with zero latency
        # and no chance of the model missing them. The model is a second layer
        # on top of this, not the only line of defence.
        keyword_hit = next(
            (kw for kw in ESCALATION_KEYWORDS if kw in user_input.lower()), None
        )
        if keyword_hit and self.session.stage != Stage.ESCALATED:
            reason = f"Keyword trigger: '{keyword_hit}'"
            self.session.stage = Stage.ESCALATED
            self.session.escalation_log.append({
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "trigger_message": user_input,
                "detected_by": "keyword_check"
            })
            self.session.messages.append({
                "role": "assistant",
                "content": json.dumps({"message": "escalated_by_keyword"})
            })
            return AgentResponse(
                message=(
                    "I'm really sorry to hear that - I want to make sure you get the "
                    "right support straight away. I'm flagging this for one of our team "
                    "now and someone will be in touch with you very shortly."
                ),
                escalated=True,
                escalation_reason=reason,
                confidence="high",
                stage=Stage.ESCALATED
            )

        # --- Call the model ---
        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": self._build_system_prompt()
                    },
                    *self.session.messages
                ],
                max_tokens=MAX_TOKENS
            )
            raw_text = response.choices[0].message.content or ""
        except Exception as e:
            # If the API call fails for any reason, fail safely.
            # Better to hand off to a human than to leave the customer hanging.
            reason = f"API error: {type(e).__name__}"
            self.session.stage = Stage.ESCALATED
            self.session.escalation_log.append({
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "trigger_message": user_input,
                "detected_by": "error_handler"
            })
            return AgentResponse(
                message=(
                    "I'm sorry, I've run into a temporary issue on my end. "
                    "I'm passing you over to one of our team who can help you right away."
                ),
                escalated=True,
                escalation_reason=reason,
                confidence="low",
                stage=Stage.ESCALATED
            )

        parsed = self._parse_response(raw_text)

        # Store the raw response in history so the model sees prior context
        self.session.messages.append({
            "role": "assistant",
            "content": raw_text
        })

        # --- Stage transitions ---

        # FAQ → Qualification (when Aria offers and customer accepts)
        if parsed.get("next_stage") == "qualification" and self.session.stage == Stage.FAQ:
            self.session.stage = Stage.QUALIFICATION

        # Qualification complete → back to FAQ (with collected context retained)
        if parsed.get("qualification_complete") and self.session.stage == Stage.QUALIFICATION:
            self.session.stage = Stage.FAQ
            self.session.qualification_q_index = 3  # mark as done

        # Advance the qualification question index when a question was just asked
        if self.session.stage == Stage.QUALIFICATION and parsed.get("qualification_update"):
            self.session.qualification_q_index = min(
                self.session.qualification_q_index + 1, 3
            )

        # --- Escalation handling ---
        if parsed.get("escalate"):
            self.session.stage = Stage.ESCALATED
            self.session.escalation_log.append({
                "timestamp": datetime.now().isoformat(),
                "reason": parsed.get("escalation_reason", "unspecified"),
                "trigger_message": user_input
            })

        # --- Data collection ---
        if parsed.get("qualification_update"):
            self.session.qualification_data.update(parsed["qualification_update"])

        if parsed.get("sop_gap"):
            self.session.sop_gaps.append({
                "question": user_input,
                "gap": parsed["sop_gap"]
            })

        if self.session.stage == Stage.FAQ:
            self.session.faq_exchanges += 1

        return AgentResponse(
            message=parsed.get("message", "I'm sorry, could you say that again?"),
            escalated=parsed.get("escalate", False),
            escalation_reason=parsed.get("escalation_reason"),
            confidence=parsed.get("confidence", "high"),
            stage=self.session.stage,
            sop_gap=parsed.get("sop_gap")
        )

    def generate_summary(self) -> dict:
        """
        Produce a structured end-of-session summary using a dedicated summariser prompt.
        Intentionally separate from the main chat prompt - different job, different instructions.
        """
        history_text = self._format_history_for_summary()

        summary_prompt = f"""You are a clinical assistant summarising a customer support conversation for the Bloom Aesthetics Clinic team.

<conversation>
{history_text}
</conversation>

<session_metadata>
Total exchanges: {len(self.session.messages) // 2}
Final stage reached: {self.session.stage.value}
Qualification data collected: {json.dumps(self.session.qualification_data, indent=2)}
Escalation events: {json.dumps(self.session.escalation_log, indent=2)}
SOP gaps flagged: {json.dumps(self.session.sop_gaps, indent=2)}
Session started: {self.session.started_at}
</session_metadata>

Produce a clean, structured summary for the team to review. Return ONLY valid JSON in this format:

{{
  "customer_intent": "One clear sentence summarising what the customer was trying to achieve",
  "key_details": {{
    "services_enquired_about": [],
    "booking_intent": "high / medium / low / none",
    "treatment_experience": "first-time / experienced / unknown"
  }},
  "qualification_summary": {{
    "treatment_interest": "...",
    "prior_experience": "...",
    "booking_timeframe": "..."
  }},
  "sop_gaps_identified": [],
  "escalation": {{
    "was_escalated": false,
    "reason": null,
    "trigger_message": null
  }},
  "recommended_next_action": "A specific, actionable step for the Bloom team to take"
}}"""

        response = self.client.chat.completions.create(
            model=MODEL,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": summary_prompt
                }
            ],
            max_tokens=MAX_TOKENS
        )

        return self._parse_response(
            response.choices[0].message.content or ""
        )

    def save_session(self, filepath: str):
        """Write the full session log to a JSON file for audit and review."""
        data = {
            "started_at": self.session.started_at,
            "ended_at": datetime.now().isoformat(),
            "final_stage": self.session.stage.value,
            "total_exchanges": len(self.session.messages) // 2,
            "qualification_data": self.session.qualification_data,
            "escalation_log": self.session.escalation_log,
            "sop_gaps": self.session.sop_gaps,
            "message_count": len(self.session.messages)
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def _format_history_for_summary(self) -> str:
        """Convert message history to readable text for the summariser."""
        lines = []
        for msg in self.session.messages:
            role_label = "Customer" if msg["role"] == "user" else "Aria"
            content = msg["content"]
            # Try to extract the "message" field from Aria's JSON responses
            if msg["role"] == "assistant":
                try:
                    parsed = json.loads(content)
                    content = parsed.get("message", content)
                except (json.JSONDecodeError, TypeError):
                    pass
            lines.append(f"{role_label}: {content}")
        return "\n".join(lines)
