# Bloom Aesthetics — AI Customer Support Agent

A Python-based AI workflow built for the Closira internship assignment. It handles inbound customer conversations for a fictional aesthetics clinic end-to-end: answering FAQs from an SOP, qualifying leads, detecting when to escalate, and producing a structured session summary.

---

## Demo

```
  ╔══════════════════════════════════════════╗
  ║         Bloom Aesthetics Clinic          ║
  ║         AI Support Agent — Aria          ║
  ╚══════════════════════════════════════════╝

Aria: Hi there! Welcome to Bloom Aesthetics Clinic — I'm Aria. How can I help you today?

You: What are your Botox prices?

Aria: Our Botox treatments start from £200, and the final price depends on the number
      of areas you'd like treated. Consultations are completely free if you'd like to
      discuss options before committing to anything.

You: quit

════════════════════════════════════════════════════
             SESSION SUMMARY
════════════════════════════════════════════════════
Customer Intent
  Customer enquired about Botox pricing and treatment options.
...
```

---

## What It Does
The workflow is designed to simulate a lightweight SMB customer support assistant while keeping responses grounded and safe.
The workflow has four distinct stages:

| Stage | Description |
|---|---|
| **FAQ Answering** | Answers inbound questions strictly from the SOP. Never invents information. |
| **Lead Qualification** | Asks 3 structured questions (treatment interest, experience, timeframe) one at a time. |
| **Escalation Detection** | Automatically detects complaints, medical questions, pricing negotiation, frustration, and out-of-scope questions. Flags and logs the reason. |
| **Session Summary** | At end of session, produces a structured JSON summary: intent, qualification data, SOP gaps, recommended next action. |

---

## Project Structure

```
bloom-ai-agent/
├── main.py               # CLI entry point and conversation loop
├── agent.py              # Core agent: all 4 stages, state machine, session management
├── config.py             # Model, constants, and CLI colour config
├── sop.json              # SOP data for Bloom Aesthetics Clinic
├── requirements.txt
├── .env.example
├── prompt_design.md      # Full system prompt + design decisions
├── README.md
├── test_transcripts/
│   ├── 01_in_sop_question.md
│   ├── 02_out_of_scope.md
│   ├── 03_escalation_trigger.md
│   ├── 04_lead_qualification.md
│   └── 05_conversation_summary.md
└── logs/                 # Auto-created — session JSON files saved here
```

---

## Setup

**Requirements:** Python 3.9+, an Anthropic API key

```bash
# 1. Clone the repo
git clone https://github.com/your-username/bloom-ai-agent
cd bloom-ai-agent

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API key
cp .env.example .env
# Open .env and replace 'your_api_key_here' with your actual key

# 5. Run
python main.py
```

---

## Usage

Type naturally to chat with Aria. A few things to know:

- **`quit` / `bye` / `exit`** — ends the session and generates the summary
- **`summary`** — same as above
- **Ctrl+C** — graceful exit

The agent starts in **FAQ mode** and transitions to **qualification** naturally after a couple of exchanges (if the customer is willing). Escalation can happen at any point and is surfaced in the terminal with a red `🚨` indicator.

After every session, a full JSON log is saved to `logs/session_YYYYMMDD_HHMMSS.json`.

---

## Architecture

```
  User input
      │
      ▼
  ┌─────────────────────────┐
  │  Keyword Safety Check   │  ← deterministic, runs before any API call
  │  (complaint, refund...) │    catches obvious triggers instantly
  └────────────┬────────────┘
               │ no keyword hit
               ▼
  ┌─────────────────────────┐
  │    Claude API Call      │  ← structured JSON response
  │  (stage-aware prompt)   │    with error handling fallback
  └────────────┬────────────┘
               │
       ┌───────┴────────┐
       │  Parse + Route │
       └───────┬────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
  FAQ     Qualification  Escalated
  Stage      Stage        Stage
    │          │             │
    └──────────┴─────────────┘
                   │
                   ▼
           Session Summary
           (separate prompt)
                   │
                   ▼
           logs/session_*.json
```


**Key design choices:**

- **Structured JSON output from Claude** — every response is a JSON object. The `message` field is what the customer sees; the rest (escalate, confidence, sop_gap, etc.) drives application logic. This keeps the workflow predictable and easier to validate.
- **Dynamic system prompt** — stage-specific instructions are injected fresh at every turn, so the model always knows exactly what it should be doing.
- **Separate summariser prompt** — the conversation prompt and summary prompt are intentionally different. They have different jobs, and blending them would make both worse.
- **Escalation as a safety net** — when the model can't answer two consecutive questions, it escalates rather than guessing. This is the most important hallucination guard.

---

## SOP Data

The SOP (`sop.json`) covers:

- **Business:** Bloom Aesthetics Clinic
- **Hours:** Mon–Sat, 9am–7pm (closed Sunday)
- **Services:** Botox (from £200), Dermal Fillers (from £250), Consultation (free)
- **Booking:** Via WhatsApp or website. 24hr cancellation policy.
- **Escalation triggers:** complaint, medical question, pricing negotiation, 2+ unanswered questions, explicit human request

You can extend the SOP by editing `sop.json` — no code changes needed.

---

## Test Transcripts

Six sample conversations in `test_transcripts/`, one per expected behaviour:

1. `01_in_sop_question.md` — Botox price enquiry, answered from SOP
2. `02_out_of_scope.md` — Question not in SOP, escalation after 2 gaps
3. `03_escalation_trigger.md` — Complaint and pricing negotiation scenarios
4. `04_lead_qualification.md` — Full 3-question qualification flow
5. `05_conversation_summary.md` — End-of-session summary with all fields
6. `06_realistic_messy_conversation.md` — Informal input, mid-chat medical keyword, keyword escalation

---

## Trade-offs and Known Limitations

**No orchestration framework.** This implementation intentionally avoids heavier tools like LangChain to keep the workflow transparent and easy to reason about. For a focused SMB support use case with four well-defined stages, a clean state machine is simpler and more debuggable than an abstraction layer on top of it.

**Confidence is self-assessed.** The `confidence` field in the JSON response is the model's own self-assessment — not a calibrated probability. It's a useful signal, but shouldn't be treated as a precise measurement.

**JSON parsing has a fallback.** If Claude produces malformed JSON (rare, but it can happen), the app strips markdown fences and tries to extract a JSON object. If all else fails, it returns a safe default response rather than crashing. The structured data for that turn is lost, but the conversation continues.

**Stage transitions are model-driven.** The qualification stage depends on the model returning `"next_stage": "qualification"` when it offers and the customer accepts. In rare cases the model might not include this field even when appropriate — the stage would remain FAQ. A more robust production system would use a separate classifier for stage routing.

**No memory across sessions.** Each conversation starts from scratch. A real deployment would pull customer history from a CRM before starting the prompt.

**CLI only.** No frontend or webhook integration — this is a prototype demonstrating the AI logic layer. It could be wrapped in a WhatsApp or web handler without changing the core agent code.

---

## Future Improvements

- **WhatsApp / webhook integration** — the agent logic is already channel-agnostic; it just needs an inbound handler (Twilio or Meta's Cloud API) plugged in front of `agent.chat()`
- **CRM integration** — pass customer history into the session context at startup so Aria knows if someone has visited before
- **Multi-language support** — the SOP and tone instructions could be translated per-session based on the customer's detected language

---

## Changing the Model

The model is set in `config.py`:

```python
MODEL = "claude-3-5-sonnet-20241022"
```

Swap this for any model in the Anthropic API. `claude-3-haiku-20240307` is faster and cheaper if you're running many tests.
