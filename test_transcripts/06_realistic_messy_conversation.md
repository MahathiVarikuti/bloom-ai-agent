# Test Transcript 06 - Realistic Conversation (Messy Input)

**Scenario:** Customer types informally, jumps between topics, raises a medical concern mid-conversation, and eventually books. This is closer to how real customers actually behave - not a clean Q&A.

---

**Aria:** Hi there! Welcome to Bloom Aesthetics Clinic - I'm Aria. How can I help you today?

**Customer:** hi yea i was looking at ur website and thinking abt botox maybe?? not sure tbh

**Aria:** Hey! No pressure at all - it's completely normal to be weighing it up. We offer Botox starting from £200, and the price depends on how many areas you'd want treated. If you're still figuring out whether it's the right thing for you, a free consultation is a great first step - you'd get to chat it through with a practitioner before committing to anything.

**Customer:** ok cool, how long does it last tho

**Aria:** That's a really common question, but honestly that detail isn't something I have in the information I've got here. It's a great one to ask during a consultation though - the practitioner can give you a proper answer based on the specific treatment. Would you like help booking one?

*(Internal: `confidence: "low"`, `sop_gap: "Customer asked about Botox longevity - not in SOP"`)*

**Customer:** yeah makes sense. also i had a reaction to something similar last year, is that gonna be a problem?

*(Internal: keyword check - "reaction" matches ESCALATION_KEYWORDS → immediate escalation, no API call needed)*

**🚨 ESCALATION TRIGGERED**
Reason: Keyword trigger: 'reaction'
Detected by: keyword_check

**Aria:** I'm really sorry to hear that - I want to make sure you get the right support straight away. I'm flagging this for one of our team now and someone will be in touch with you very shortly.

*(Internal: stage → ESCALATED, logged with `detected_by: "keyword_check"` for audit)*

---

**What this transcript demonstrates:**

1. **Informal input handled naturally** - typos, trailing "??" and hedging ("maybe", "not sure tbh") don't break the system
2. **Honest SOP gap** — "how long does it last" isn't in the SOP; Aria says so rather than guessing
3. **Keyword escalation fires fast** - "reaction" triggers the deterministic check *before* any API call, so there's no delay and no risk of the model misjudging a potential medical concern
4. **Escalation message stays warm** - not robotic, not alarming, just reassuring and clear
5. **Audit trail is clean** - the escalation log records `detected_by: "keyword_check"` so the team knows it was a hard trigger, not a model judgement call

---

**Expected behaviour: ✅ PASS**
- Casual / informal input handled without issue
- SOP gap correctly identified and logged
- Medical keyword triggers immediate escalation (pre-model, zero latency)
- Stage correctly set to ESCALATED
- Customer experience remains reassuring throughout
