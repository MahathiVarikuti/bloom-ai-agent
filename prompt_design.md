# Prompt Design — Bloom Aesthetics AI Agent

This document explains the design decisions behind the AI workflow: the system prompt structure, how hallucination is prevented, how escalation is detected, and the tone choices made for an SMB aesthetics context.

---

## System Prompt

The full system prompt (in `agent.py`, `_build_system_prompt()`) looks like this at runtime:

```
You are Aria, a warm and professional customer support assistant for Bloom Aesthetics Clinic.

<sop>
{ ... SOP JSON injected here at runtime ... }
</sop>

<core_rules>
  1. ONLY answer using information present in the <sop> above.
  2. NEVER invent prices, services, availability, or medical advice.
  3. ALWAYS return a single valid JSON object in the defined schema.
</core_rules>

<escalation_rules>
  Set "escalate": true when:
  - Customer is frustrated, upset, or making a complaint
  - Medical question about risks or side effects
  - Pricing negotiation or challenge
  - 2+ consecutive questions not answerable from SOP
  - Customer explicitly asks for a human
</escalation_rules>

<confidence_guide>
  "high"   — Fully covered by SOP
  "medium" — Partially covered
  "low"    — Outside SOP scope
</confidence_guide>

{ Stage-specific instructions injected dynamically }
{ Qualification data already collected (if any) }

<tone>
  Warm, calm, British English. 2–3 sentences. Not pushy.
</tone>
```

---

## Key Design Decisions

### 1. XML Tag Structure

I used XML tags (`<sop>`, `<core_rules>`, `<escalation_rules>`) rather than plain markdown headings because structured XML-delimited sections tend to work more reliably in longer prompts. It creates clear boundaries between the data and the instructions, keeping each section cleanly separated from the others.

It also makes the prompt easier to maintain — you can swap out `<sop>` content without touching the instruction sections.

---

### 2. Stage Instructions Are Injected Dynamically

The system prompt isn't static - the stage-specific instructions (FAQ, Qualification, or Escalated) are injected at the top of each API call based on the current session state.

Why not include all three stages in every prompt?

- When Aria is in FAQ mode, she doesn't need to see qualification question scripts - they add noise and can confuse the model.
- When the prompt says "CURRENT STAGE: QUALIFICATION — ask question number 2", the model has no ambiguity about what to do.
- If qualification behaviour needs tweaking, you change one block, not one section inside a single large prompt.

---

### 3. Structured JSON Output

Every response from Aria is a JSON object, not free text:

```json
{
  "message": "The warm, natural customer-facing reply",
  "escalate": false,
  "escalation_reason": null,
  "confidence": "high",
  "sop_gap": null,
  "qualification_update": {},
  "next_stage": null,
  "qualification_complete": false
}
```

**Why structured output?**

The alternative - parsing free text to detect escalation or extract qualification answers - is fragile. Keywords can be missed, phrasing varies, and you end up writing a bunch of brittle regex. A structured response lets the application layer handle logic cleanly and reliably. The model is good at generating structured data; lean into that.

The `message` field is what the customer sees. The customer only sees this field; the application uses the remaining fields internally.

---

## Hallucination Prevention

This was one of the main design constraints. The SOP is injected in full at the start of every prompt, and the first two core rules are explicit prohibitions:

```
1. ONLY answer using information present in the <sop> above.
2. NEVER invent prices, services, availability, medical advice, staff names, or any other facts.
```

But rules alone aren't enough - I also built structural fallbacks:

**Confidence field**: The model must self-assess at each turn. A "low" confidence rating flags that the answer might be outside SOP scope, even if the model still attempted a response. This is logged as an SOP gap.

**SOP gap logging**: When the model cannot answer from SOP, it's instructed to say so honestly and include the question in `"sop_gap"`. These are stored in the session and surfaced in the summary - useful for improving the SOP over time.

**Escalation as a safety net**: The escalation trigger "you cannot answer 2 or more consecutive questions from the SOP" means that if the model consistently can't help, it hands off rather than improvising. This is the most important hallucination guard - when in doubt, escalate rather than guess.

**Suggested phrasing**: Rather than leaving the model to decide how to handle a gap, I gave it a concrete phrase to use: *"I don't have that detail to hand, but one of our team can help - shall I flag that for you?"* This means the customer experience is consistent, and it doesn't sound like a generic AI deflection.

---

## Confidence-Based Escalation

Escalation is handled in two ways:

### Hard triggers (rule-based, in the prompt)
These are conditions where the model should always escalate, regardless of confidence:
- Complaint or expressed frustration
- Medical question (safety, risks, side effects, allergies)
- Pricing negotiation
- Explicit request for a human

These are listed explicitly in `<escalation_rules>`. The model is told to set `"escalate": true` in its JSON output.

### Soft trigger (confidence-based)
The "2+ consecutive unanswered questions" rule acts as the confidence-based escalation. I deliberately didn't use a numeric threshold on the `confidence` field itself (e.g. "escalate if confidence < 0.4") because:

1. The model's self-assessed confidence isn't calibrated - it can be overconfident
2. A consecutive-questions rule is more robust and easier to audit
3. It mirrors how a human agent would work: one thing I can't answer is fine; two in a row means I need backup

The escalation state is captured in `session.escalation_log` with a timestamp, reason, and the trigger message - so there's always a clear audit trail.

---

## Tone and Persona

The persona is **Aria** - a warm, calm, knowledgeable clinic assistant. The name matters: it gives the AI a consistent identity and makes the conversation feel less like talking to a chatbot.

The tone choices were driven by the context:

- **Aesthetics clinic customers can be nervous.** They might be asking about a treatment for the first time, unsure if it's right for them, or anxious about cost. The tone needs to feel reassuring without being patronising.
- **British English.** The clinic is UK-based (prices in GBP). Using British spellings ("enquiry", "colour", "organise") and conventions feels natural and congruent.
- **Concise.** SMB customers don't want walls of text. 2–3 sentences is usually right. The model tends to over-explain when not constrained - the tone instruction explicitly limits this.
- **Not salesy.** Aesthetics is a high-trust category. An agent that pushes too hard would feel off. The instruction "avoid being pushy or salesy" is there because the default model behaviour can lean that way when describing services.

The `"message"` field - the only thing the customer sees - is always natural language. The structured JSON is purely internal. This means the customer experience feels like talking to a person, while the application layer gets clean, reliable data.

---

## Stage Transition Logic

```
[FAQ] ──────────────────────────────────────────► [ESCALATED]
  │  (after 2+ exchanges, Aria offers)              ▲  ▲  ▲
  │                                                 │  │  │
  ▼                                                 │  │  │
[QUALIFICATION] ──────────────────────────────────►┘  │  │
  │  (all 3 questions answered)                        │  │
  │                                                    │  │
  └─► [back to FAQ, with qualification context] ───────┘  │
                                                           │
      (any stage can trigger escalation) ─────────────────┘
```

- Stage is injected fresh into the system prompt on every call - the model always knows where it is
- Transitions are driven by fields in the JSON response (`next_stage`, `qualification_complete`, `escalate`)
- Qualification answers accumulate in `session.qualification_data` and are re-injected into subsequent prompts so Aria doesn't ask the same thing twice

---

## Session Summary

The summary is generated by a **separate prompt call** - not the same prompt used for conversation. This was a deliberate choice.

The conversation prompt is optimised for real-time, empathetic, turn-by-turn responses. The summary prompt has a completely different job: synthesise, extract, and structure. Conflating the two would make both worse.

The summary prompt gets the full conversation history (formatted as readable Customer/Aria lines), plus all the metadata collected during the session (qualification data, escalation log, SOP gaps). It returns a structured JSON object with:

- **Customer intent** - what they were trying to achieve
- **Key details** - services enquired, booking intent, experience level
- **Qualification summary** - the three answers collected
- **SOP gaps** - questions that couldn't be answered, for SOP improvement
- **Escalation details** - if and why the conversation was escalated
- **Recommended next action** - a specific step for the human team

The recommended next action is intentionally concrete ("Book a follow-up call" rather than "Follow up"). The goal is for the team to be able to act on the summary without having to read the full transcript.

---

## Known Limitations and Trade-offs

- **JSON parsing** relies on the model following instructions. If the model produces malformed JSON (rare with modern chat models but still possible), the app falls back gracefully but loses structured metadata for that turn.
- **No memory across sessions** - each conversation starts fresh. A production version would retrieve customer history from a CRM.
- **Qualification questions are fixed** - the three questions were chosen for general qualification, but a real deployment might want to adapt them based on the channel or the customer's opening message.
- **Confidence is self-assessed** - the model doesn't have a calibrated confidence score. The `confidence` field is a useful signal, not a precise measurement.
